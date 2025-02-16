---
tags: logstash
date: "2025-02-16"
category: Log Analytics
---

*__Blog Post Publish Date:__ 2025/02/16*

---

# Logstash DB Enrichment - Tips and Traps!

In this blog post, I share my experiences with Logstash log enrichment using a database. I'll cover some hidden behaviors and the importance of configuring the JDBC connection string parameters to avoid mysterious problems that are hard to replicate and not clearly documented.

These tips come from real-world scenarios and aren't always obvious in the official documentation. I hope they help you save hours of troubleshooting and searching through forums.

The examples assume you're running Logstash OSS 8.17 in a Kubernetes cluster with a PostgreSQL database. However, the key considerations apply even if you're using a single instance or a different relational database.

I've also created a docker-compose lab for you to explore and test all the tips discussed in this blog post: <i class="fab fa-github fa-fade"></i> [github.com/c-neto/my-devops-labs/logstash/db-enrichment](https://github.com/c-neto/my-devops-labs/tree/main/logstash/db-enrichment)

I reserve special thanks to PostgreSQL Database Specialist [Lucio Chiessi](https://www.linkedin.com/in/lucio-chiessi) for helping me explore the JDBC connection string options that can be beneficial for Logstash.

## Use Prepared Statements

The first tip is to use the `use_prepared_statements` option in the `jdbc_streaming` filter plugin. A Prepared Statement in PostgreSQL is a pre-compiled SQL query that improves performance and security by allowing repeated execution with different parameters while preventing SQL injection. When a query is prepared, PostgreSQL analyzes and optimizes the execution plan once. In subsequent calls, only the parameters are replaced, avoiding recompilation and improving efficiency.

Normally, the query in the log ingestion pipeline has a defined structure, changing only the parameters, and it is frequently executed. It is an ideal use case for log enrichment.

Example of `use_prepared_statements`:

```lua
jdbc_streaming {
  jdbc_driver_library => "/usr/share/logstash/postgresql.jar"
  jdbc_driver_class => "org.postgresql.Driver"
  jdbc_connection_string => "${DB_JDBC_CONNECTION_STRING}"
  jdbc_user => "${DB_USER}"
  jdbc_password => "${DB_PASSWORD}"
  use_prepared_statements => true
  prepared_statement_name => "logstash_enrich_query"
  prepared_statement_bind_values => [
    "[document][user_id]"
  ]
  statement => "
  SELECT
    user_name,
    user_email,
    user_group
  FROM table_users
  WHERE id = ?
  "
  target => "sql"
}
```

## When the Database is Out, Your Pipeline Won't Start!

When you configure a Logstash pipeline that uses log enrichment by `jdbc_streaming`, Logstash verifies the connection with the database __before starting__ to receive the logs. If the database is out, the pipeline will not be registered, and log ingestion will be removed. Pay attention, Logstash verifies the database connection before starting to receive logs, not when receiving logs that will use the `jdbc_streaming`. In other words, if your database is out, the log ingestion pipeline that has `jdbc_streaming` will not start, even if all logs don't satisfy `if` conditions to be enriched.

However, there is one detail that causes confusion in the behavior mentioned above: If the database is running when the Logstash pipeline starts, and the database connection is broken, the pipeline will continue working with log enrichment errors only. When the database connection is live again, the enrichment will be re-established and work.

It is important to understand because when you configure a database log enrichment, indirectly, you are configuring a hard dependency between Logstash new instances and database health.

It is a problem because if the database is out, it invalidates scaling the Logstash pods, and if Logstash restarts, the log ingestion will be blocked because of the hard dependency on the database.

Ok, but... How to fix this behavior? I didn't find any parameter in the Logstash documentation to prevent this behavior... In this case, you can organize distinct pipelines in a way that one pipeline is only for logs that will always be enriched, and another pipeline for logs that will not be enriched. This approach can avoid stopping log ingestion of logs that don't need to be enriched when the database is out. But, this approach can increase the duplicate code. Thus, my suggestion is to use templates of your log pipeline to have a fallback pipeline without log enrichment to avoid rendering the `jdbc_streaming` statements. If you are working in Kubernetes, I suggest templating the pipeline using [Helm](https://helm.sh/); if not, you can use another template engine like [Jinja](https://jinja.palletsprojects.com/en/stable/).

## Lock Table == Lock Log Ingestion

This is the worst problem that can occur: when issues arise, and service logs are frozen without an explicit indication of the root cause.

When a log is performing the `jdbc_streaming` filter plugin, and at that moment, the table defined in the query is locked, all logs will be stopped, even logs that will not perform `jdbc_streaming`. The worst thing is that Logstash service logs don't generate logs to explicitly indicate this behavior (_at least in the default log level_).

I explored the documentation of the [jdbc_streaming](https://www.elastic.co/guide/en/logstash/current/plugins-filters-jdbc_streaming.html) to check parameters that can help avoid this behavior, and I didn't find any. At this moment, I realized that I needed to explore the PostgreSQL JDBC connection string. I explored <https://jdbc.postgresql.org/> and found important things that explain the behavior. By default, if a query execution is on a table that is locked, the timeout for query execution is infinite!

To solve this problem, it is necessary to explicitly set the parameter `options=-c lock_timeout=1000` in the JDBC connection string to set the maximum time in milliseconds to wait for a lock on a table. If the lock cannot be acquired within 1 second, an error is thrown in Logstash service explicitly indicating that the log was not enriched due to lock timeout, and the log pipeline will continue, and the log will proceed to the next statement.

To simulate this case, you can execute the following command in PostgreSQL:

```sql
LOCK TABLE table_used_by_logstash IN ACCESS EXCLUSIVE MODE;
```

At this moment, I paid attention to reviewing all JDBC connection parameters with infinite values by default that could cause problems like the one mentioned, and I will present them in the following topics in this blog post.

## Slow Query == Slow Log Ingestion

Another JDBC connection parameter that defaults to infinite is the query execution timeout. If the database is overloaded and facing throttling, your log ingestion will be affected. If an enrichment query execution takes a long time, all logs in this pipeline will be queued, similar to the behavior explained in the previous topic. The default connection parameter in PostgreSQL for query execution timeout is infinite, thus, database overload will impact log ingestion.

To solve this case, you can explicitly set the JDBC connection parameter `options=-c statement_timeout=5000` to set the maximum time in milliseconds that a query can run before being terminated. In this case, queries running longer than 5 seconds will be aborted, and it will be explicitly logged in Logstash service logs, the pipeline will continue working, and log enrichment will be skipped, adding the tag.

To simulate a slow query, you can add the function [pg_sleep](https://pgpedia.info/p/pg_sleep.html). In the example below, `pg_sleep(10)::text` is introduced to artificially simulate a slow query:

```lua
jdbc_streaming {
  jdbc_driver_library => "/usr/share/logstash/postgresql.jar"
  jdbc_driver_class => "org.postgresql.Driver"
  jdbc_connection_string => "${DB_JDBC_CONNECTION_STRING}"
  jdbc_user => "${DB_USER}"
  jdbc_password => "${DB_PASSWORD}"
  use_prepared_statements => true
  prepared_statement_name => "logstash_enrich_query"
  prepared_statement_bind_values => ["[document][user_id]"]
  statement => "
    SELECT
      pg_sleep(10)::text,    
      user_name,
      user_email,
      user_group
    FROM table_users
    WHERE id = ?
  "
  target => "sql"
}
```

## Define Timeouts for Database Login and Socket

In the same context as the previously presented timeout parameters, it is important to define `loginTimeout=10` to specify the maximum time in seconds to wait for a connection to be established. If the connection cannot be established within this time, an error is thrown, and `socketTimeout=10` to set the maximum time in seconds for reading data from the database. If the database does not respond within this time, the connection is closed.

## Ensure DB Connection Identification

The Logstash enrichment queries can be offensive to the database. In this case, it is necessary to tag the connections to make it easier to identify in the aspect of database administration. To define the connection identification, use the JDBC Connection String parameter `ApplicationName=logstash` to set the application name to `logstash` for easier identification in PostgreSQL logs.

Thus, you can identify the connection from Logstash by the following PostgreSQL query:

```sql
SELECT pid, application_name, usename, datname, client_addr, state
FROM pg_stat_activity
WHERE application_name = 'logstash';
```

## Sequel Opts != Database Connection Parameters

Don't be confused, the [jdbc_streaming::sequel_opts](https://github.com/jeremyevans/sequel/blob/master/doc/opening_databases.rdoc#label-postgres) parameters and [JDBC Connection String](https://jdbc.postgresql.org/documentation/use/) performing distinct roles. Logstash connects to databases using **JDBC**, but it internally manages the connection through the **Sequel** library in JRuby, allowing for additional configuration via [sequel_opts](https://github.com/jeremyevans/sequel/blob/master/doc/opening_databases.rdoc#label-postgres). Thus, the JDBC connection string defines behavior with the database, and Sequel defines connection characteristics to manage this connection.

The example below is ideal to explain it. The `sequel_opts::pool_timeout` defines a timeout for Logstash to wait for an available pool connection to use, which is not related to the timeout of query execution, which is the parameter related to the database, defined in the `jdbc_connection_string`.

```lua
jdbc_streaming {
  sequel_opts => {
    max_connections => 4
    pool_timeout => 5
  }
  jdbc_connection_string => "jdbc:postgresql://postgres:5432/db?options=-c%20statement_timeout=1000%20"
}
```

## Conclusion

When working with Logstash, I initially assumed that its behaviors were straightforward and default. However, Logstash has many nuances that can impact log ingestion and even halt it.

As requirements grow, so do the challenges. Nothing should be taken for granted, and everything needs to be validated. I highly recommend setting up a docker-compose lab to test features in various contexts. This ensures reliability, helps plan workarounds, and prevents unexpected issues, especially late on a Friday night.

Don't forget to check out the docker-compose lab: <i class="fab fa-github fa-fade"></i> [github.com/c-neto/my-devops-labs/logstash/db-enrichment](https://github.com/c-neto/my-devops-labs/tree/main/logstash/db-enrichment)

## References

- <https://jdbc.postgresql.org/documentation/use/>
- <https://www.postgresql.org/docs/current/runtime-config-client.html>
- <https://www.elastic.co/guide/en/logstash/current/plugins-filters-jdbc_streaming.html>
- <https://github.com/c-neto/my-devops-labs/tree/main/logstash/db-enrichment>
- <https://github.com/jeremyevans/sequel/blob/master/doc/opening_databases.rdoc#label-postgres>
