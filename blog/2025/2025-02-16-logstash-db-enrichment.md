---
tags: logstash, logs
date: "2025-02-16"
category: Observability
author: Carlos Neto
title: "Logstash DB Enrichment: Tips and Traps"
description: "Hidden behaviors of Logstash jdbc_streaming enrichment with PostgreSQL: pipelines that won't start without the database, table locks and slow queries that freeze ingestion, and the JDBC timeouts that prevent them."
myst:
  html_meta:
    description: "Hidden behaviors of Logstash jdbc_streaming enrichment with PostgreSQL: pipelines that won't start without the database, table locks and slow queries that freeze ingestion, and the JDBC timeouts that prevent them."
og:title: "Logstash DB Enrichment: Tips and Traps"
og:description: "Hidden behaviors of Logstash jdbc_streaming enrichment with PostgreSQL: pipelines that won't start without the database, table locks and slow queries that freeze ingestion, and the JDBC timeouts that prevent them."
---

*__Blog Post Publish Date:__ 2025/02/16*

---

# Logstash DB Enrichment: Tips and Traps

This blog post covers the lessons from enriching logs in Logstash with data from a PostgreSQL database. It explains hidden behaviors of the `jdbc_streaming` filter that can stop log ingestion, and the JDBC connection string parameters that prevent them. These problems are hard to reproduce and not clearly documented, so I hope these tips save you hours of troubleshooting and forum searching.

The examples assume [Logstash OSS 8.17.2](https://www.elastic.co/guide/en/logstash/current/logstash-8-17-2.html) running in Kubernetes with a PostgreSQL database, but the same considerations apply to a single instance or another relational database. I also built a Docker Compose lab where you can try every tip in this post: <i class="fab fa-github fa-fade"></i> [github.com/c-neto/my-devops-labs/logstash/db-enrichment](https://github.com/c-neto/my-devops-labs/tree/main/logstash/db-enrichment)

Special thanks to PostgreSQL specialist [Lucio Chiessi](https://www.linkedin.com/in/lucio-chiessi) for helping me explore the JDBC connection string options that are useful for Logstash.

## Use Prepared Statements

The first tip is to enable [`use_prepared_statements`](https://www.elastic.co/guide/en/logstash/8.17/plugins-filters-jdbc_streaming.html#plugins-filters-jdbc_streaming-use_prepared_statements) in the [`jdbc_streaming`](https://www.elastic.co/guide/en/logstash/8.17/plugins-filters-jdbc_streaming.html) filter.

A **prepared statement** is a SQL query that PostgreSQL parses and plans once, then runs many times with different parameters. It's faster, because the plan is not rebuilt on every call, and safer, because parameters are bound instead of concatenated, which prevents SQL injection. An enrichment query is a perfect fit: its structure never changes, only the parameter does, and it runs for every log. For example:

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

## When the Database Is Down, Your Pipeline Won't Start

When a pipeline uses `jdbc_streaming`, Logstash checks the database connection __before the pipeline starts__ receiving logs. If the database is down, the pipeline is not registered and receives nothing. The check happens at startup, not when a log reaches the filter. So even if none of your logs match the `if` condition that leads to the enrichment, the whole pipeline stays down.

There is a detail that makes this confusing. If the database is up when the pipeline starts and the connection breaks later, the pipeline keeps running and only the enrichment fails. When the connection comes back, enrichment works again.

The consequence is that enrichment creates a hard dependency between every new Logstash instance and the database. If the database is down, new Logstash pods can't start their pipelines, so scaling doesn't help, and a simple restart blocks ingestion.

I didn't find any parameter in the Logstash documentation to change this. One workaround is to split the logs into two pipelines: one for logs that always need enrichment and one for logs that never do, so a database outage only affects the first. That can duplicate code, so my suggestion is to generate the pipeline from a template, with a fallback version that leaves out the `jdbc_streaming` block. On Kubernetes, I template the pipeline with [Helm](https://helm.sh/) (see [Helm Charts: Development Practices](/blog/2025/2025-02-25-helm-best-practices.md)). Outside Kubernetes, [Jinja](https://jinja.palletsprojects.com/en/stable/) works well. [Logstash Modular Pipelines](/blog/2023/2023-11-02-logstash-modular-pipelines.md) shows another way to compose pipelines without repeating inputs and outputs.

## Table Lock = Frozen Log Ingestion

This is the worst one: logs stop flowing and nothing explicitly tells you why.

If a log reaches `jdbc_streaming` while the queried table is locked, the query waits, and the whole pipeline stops behind it, including logs that don't use the enrichment. At the default log level, Logstash doesn't log anything that points to the lock.

The `jdbc_streaming` documentation has no parameter for this, so I looked at the [PostgreSQL JDBC driver](https://jdbc.postgresql.org/documentation/use/) instead. That explained the behavior: by default, a query waiting for a locked table waits forever.

The fix is to add [`options=-c lock_timeout=1000`](https://www.postgresql.org/docs/current/runtime-config-client.html) to the JDBC connection string. **`lock_timeout`** is the maximum time, in milliseconds, that a statement waits to acquire a lock. With `1000`, if the lock isn't acquired within 1 second, the query fails, Logstash logs an explicit lock timeout error, the log continues through the pipeline without the enrichment, and the next logs keep flowing.

To reproduce it, lock the table in PostgreSQL:

```sql
LOCK TABLE table_used_by_logstash IN ACCESS EXCLUSIVE MODE;
```

After that, I reviewed every JDBC connection parameter that defaults to infinite and could cause a similar freeze. The next sections cover them.

## Slow Query = Slow Log Ingestion

The query execution timeout also defaults to infinite in PostgreSQL. If the database is overloaded or throttled and an enrichment query takes a long time, every log in the pipeline queues behind it, just like with a lock.

Set [`options=-c statement_timeout=5000`](https://www.postgresql.org/docs/current/runtime-config-client.html) in the JDBC connection string. **`statement_timeout`** is the maximum time, in milliseconds, that a query can run before PostgreSQL cancels it. With `5000`, queries longer than 5 seconds are aborted, the error appears in the Logstash logs, enrichment is skipped and the failure tag is added to the event, and the pipeline keeps working.

To simulate a slow query, add [`pg_sleep`](https://pgpedia.info/p/pg_sleep.html) to the statement. In this example, `pg_sleep(10)::text` makes every query take 10 seconds:

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

## Set Login and Socket Timeouts

For the same reason, set two more [connection parameters](https://jdbc.postgresql.org/documentation/use/#connection-parameters):

- `loginTimeout=10`: the maximum time, in seconds, to wait for a connection to be established. After that, the driver throws an error.
- `socketTimeout=10`: the maximum time, in seconds, to wait for data from the database on a socket read. After that, the connection is closed.

## Identify Logstash Connections in the Database

Enrichment queries can put real load on the database, so the database team needs to see which connections come from Logstash. Set [`ApplicationName=logstash`](https://jdbc.postgresql.org/documentation/use/#connection-parameters) in the connection string, and every Logstash connection shows up under that name. For example, this query lists them:

```sql
SELECT pid, application_name, usename, datname, client_addr, state
FROM pg_stat_activity
WHERE application_name = 'logstash';
```

Putting all the parameters from this post together, a connection string looks like this (spaces inside `options` are URL-encoded as `%20`):

```text
jdbc:postgresql://postgres:5432/db?ApplicationName=logstash&loginTimeout=10&socketTimeout=10&options=-c%20lock_timeout=1000%20-c%20statement_timeout=5000
```

## Sequel Options Are Not Database Connection Parameters

Don't mix up [`sequel_opts`](https://github.com/jeremyevans/sequel/blob/master/doc/opening_databases.rdoc#label-postgres) and the [JDBC connection string](https://jdbc.postgresql.org/documentation/use/). They play different roles. Logstash talks to the database through **JDBC**, but it manages the connections with the **Sequel** library in JRuby, which `sequel_opts` configures. The JDBC connection string defines how the database behaves for the session. Sequel defines how Logstash manages its pool of connections.

For example, [`sequel_opts::pool_timeout`](https://github.com/jeremyevans/sequel/blob/master/doc/opening_databases.rdoc#label-postgres) is how long Logstash waits for a free connection in its pool. It has nothing to do with how long a query may run, which is a database setting defined in [`jdbc_connection_string`](https://www.elastic.co/guide/en/logstash/8.17/plugins-filters-jdbc_streaming.html#plugins-filters-jdbc_streaming-jdbc_connection_string):

```lua
jdbc_streaming {
  sequel_opts => {
    max_connections => 4
    pool_timeout => 5
  }
  jdbc_connection_string => "jdbc:postgresql://postgres:5432/db?options=-c%20statement_timeout=1000%20"
}
```

## Test Before You Trust the Defaults

When I started with Logstash, I assumed its behavior was simple and that the defaults were safe. They aren't always. Logstash has many details that can slow down log ingestion or stop it completely.

As requirements grow, so do the surprises. Don't take anything for granted, and test it. I highly recommend a Docker Compose lab to try features in different situations before production. It makes the setup more reliable, helps you plan workarounds, and avoids nasty surprises, especially late on a Friday night.

Don't forget to check out the lab: <i class="fab fa-github fa-fade"></i> [github.com/c-neto/my-devops-labs/logstash/db-enrichment](https://github.com/c-neto/my-devops-labs/tree/main/logstash/db-enrichment)

## Key Takeaways

- Enable `use_prepared_statements` in `jdbc_streaming`: enrichment queries have a fixed structure and run for every log.
- A pipeline with `jdbc_streaming` doesn't start if the database is down at startup, even for logs that never reach the enrichment. Keep a fallback pipeline without it.
- PostgreSQL waits forever for a locked table by default. Set `lock_timeout` so a lock can't freeze ingestion.
- Query execution has no timeout by default either. Set `statement_timeout` so a slow database can't queue every log.
- Set `loginTimeout` and `socketTimeout`, and `ApplicationName=logstash` so the database team can identify Logstash connections.
- `sequel_opts` controls Logstash's connection pool. The JDBC connection string controls the database session. They are not interchangeable.

## References

- [jdbc_streaming filter plugin (Logstash)](https://www.elastic.co/guide/en/logstash/current/plugins-filters-jdbc_streaming.html)
- [Client connection defaults: lock_timeout and statement_timeout (PostgreSQL)](https://www.postgresql.org/docs/current/runtime-config-client.html)
- [Connection parameters (PostgreSQL JDBC driver)](https://jdbc.postgresql.org/documentation/use/)
- [Opening databases: PostgreSQL options (Sequel)](https://github.com/jeremyevans/sequel/blob/master/doc/opening_databases.rdoc#label-postgres)
- [Docker Compose lab for this post (GitHub)](https://github.com/c-neto/my-devops-labs/tree/main/logstash/db-enrichment)

*I'm Carlos Neto, and I've been running OpenSearch on EKS for over five years. More about me on [my home page](/index.md). If you have questions or a different approach, contact me on [LinkedIn](https://www.linkedin.com/in/c-neto/).*

---

```{raw} html
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@graph": [
    {
      "@type": "BlogPosting",
      "headline": "Logstash DB Enrichment: Tips and Traps",
      "description": "Hidden behaviors of Logstash jdbc_streaming enrichment with PostgreSQL: pipelines that won't start without the database, table locks and slow queries that freeze ingestion, and the JDBC timeouts that prevent them.",
      "datePublished": "2025-02-16",
      "inLanguage": "en",
      "url": "https://carlosneto.dev/blog/2025/2025-02-16-logstash-db-enrichment/",
      "mainEntityOfPage": "https://carlosneto.dev/blog/2025/2025-02-16-logstash-db-enrichment/",
      "keywords": ["Logstash", "jdbc_streaming", "PostgreSQL", "JDBC", "log enrichment"],
      "author": {"@id": "https://carlosneto.dev/#person"}
    },
    {
      "@type": "Person",
      "@id": "https://carlosneto.dev/#person",
      "name": "Carlos Neto",
      "url": "https://carlosneto.dev/",
      "sameAs": ["https://www.linkedin.com/in/c-neto/", "https://github.com/c-neto"]
    },
    {
      "@type": "BreadcrumbList",
      "itemListElement": [
        {"@type": "ListItem", "position": 1, "name": "Home", "item": "https://carlosneto.dev/"},
        {"@type": "ListItem", "position": 2, "name": "Blog", "item": "https://carlosneto.dev/blog/"},
        {"@type": "ListItem", "position": 3, "name": "Logstash DB Enrichment: Tips and Traps"}
      ]
    }
  ]
}
</script>
```
