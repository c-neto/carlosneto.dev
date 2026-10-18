---
tags: opensearch, logs, ism, observability
date: "2026-10-17"
category: Log Analytics
---

*__Blog Post Publish Date:__ 2026/10/17*

---

# OpenSearch Index Rollover Explained: Numbers, Dates, Aliases, and ISM

If you have ever stared at a cluster full of indexes named `logs-000001`, `logs-000002`, or `logs-2026.02.14` and wondered who creates these, why the weird suffixes, and how ISM fits in, this post is for you. This blog post untangles the four concepts that get knotted together here. It explains what an alias, a rollover, an index suffix, and an ISM policy each do, and how they work together.

I think this is one of the most confusing parts of OpenSearch, and the reason is that these four ideas are almost always introduced at once, as if they were one thing. They are not. Let's take them one at a time.

## The Problem They All Solve

You are shipping logs (or metrics, or any time-based data) into OpenSearch, forever. If you put everything into a single index called `logs`, two bad things happen:

1. That index grows without bound. Shards get huge, queries slow down, and you can never cleanly delete old data without expensive deletes.
2. You cannot apply a retention policy like "keep 30 days, then drop". Deleting old documents one by one is slow and wasteful.

The clean solution is to keep writing to a fresh index periodically and delete whole old indexes when they age out. Dropping an entire index is instant and cheap. But that creates a new question: how does your application know which index to write to today? That is where aliases and rollover come in.

## Concept 1: The Alias, Your Stable Write Address

An alias is a stable name that points to one or more real indexes. Think of it as a mailbox label that you can move between physical boxes.

Your application never writes to `logs-000001` directly. It writes to the alias `logs`. One index behind that alias is marked as the write index (`is_write_index: true`), and that is where new documents actually land.

```json
PUT /logs-000001
{
  "aliases": {
    "logs": {
      "is_write_index": true
    }
  }
}
```

Now your app writes to `logs`, and OpenSearch routes those writes to `logs-000001`. When you later want writes to go somewhere new, you just move which index the alias writes to, and your application does not change a thing. That "moving" is what rollover does.

## Concept 2: Rollover, the Act of Starting a Fresh Index

Rollover is the operation that creates a new index and moves the write alias to it. That is the whole idea. Before rollover, writes go to `logs-000001`. After rollover, writes go to `logs-000002`, and `logs-000001` becomes a read-only historical index that the alias still reads from but no longer writes to.

You trigger it against the alias:

```json
POST /logs/_rollover
```

The response tells you exactly what happened:

```json
{
  "acknowledged": true,
  "shards_acknowledged": true,
  "old_index": "logs-000001",
  "new_index": "logs-000002",
  "rolled_over": true,
  "conditions": {}
}
```

### Rollover with conditions

Usually you do not want to roll over blindly. You want it to happen only when the current index gets "big enough" or "old enough". You pass conditions, and the rollover only fires if at least one is met:

```json
POST /logs/_rollover
{
  "conditions": {
    "max_age": "7d",
    "max_size": "50gb",
    "max_docs": 10000000
  }
}
```

This means: roll over if the current write index is 7 days old OR has reached 50 GB OR holds 10 million documents, whichever comes first. If none are met, the response says `"rolled_over": false` and nothing changes.

This is why rollover exists. It lets you keep index shards in a healthy size and age range automatically, instead of guessing up front how big an index will get.

## Concept 3: The Suffix, How New Index Names Are Generated

When rollover creates a new index, it has to name it. There are two styles of suffix, and this is the part that confuses everyone.

### Style A: Numeric suffix (`-000001`, `-000002`, ...)

If your starting index ends in a zero-padded number, rollover simply increments it:

```
logs-000001  →  logs-000002  →  logs-000003  ...
```

You get this by naming your first index with the `-000001` suffix:

```json
PUT /logs-000001
{
  "aliases": { "logs": { "is_write_index": true } }
}
```

That is it. The number has no meaning other than "order of creation". It does not tell you when the index was created, it is just a counter. This is the most common and simplest style.

### Style B: Date-math suffix (`-2026.02.14`, ...)

Sometimes you want the index name to contain the date so it is human-readable at a glance. OpenSearch supports date math in index names: you wrap the name in `<...>` and embed a date expression like `{now/d}` (meaning "now, rounded down to the day").

The catch: the `<`, `>`, `{`, `}`, and `/` characters must be URL-encoded when you send the request. So this logical name:

```
<logs-{now/d}-000001>
```

is sent as:

```json
PUT %3Clogs-%7Bnow%2Fd%7D-000001%3E
{
  "aliases": { "logs": { "is_write_index": true } }
}
```

That creates an index named something like `logs-2026.02.14-000001`. Notice it still has the numeric `-000001` on the end. The date tells you when, and the number still increments on each rollover so names never collide if you roll over twice in one day.

Quick reference for the date-math time units:

| Unit | Meaning |
| --- | --- |
| `y` | Years |
| `M` | Months |
| `w` | Weeks |
| `d` | Days |
| `h` / `H` | Hours |
| `m` | Minutes |
| `s` | Seconds |

And `/` rounds down: `{now/d}` is the start of today, `{now/M}` is the start of this month.

### Which should you use?

- __Numeric__: simplest. Use it when you rely on rollover conditions (size/age/docs) to control rotation and you do not care about reading the date from the name. This is the default choice for most log setups.
- __Date math__: use it when people (or external tools) benefit from seeing the date directly in the index name, for example daily indexes like `logs-2026.02.14`.

Either way, the alias is still how you read and write. The suffix is just how the physical indexes are named.

## Concept 4: ISM, the Robot That Does This for You

So far every rollover has been a manual `POST /logs/_rollover`. Nobody wants to run that by hand every few hours. Index State Management (ISM) is the built-in automation that does it for you, and also handles the aging and deletion afterward.

An ISM policy is a small state machine. For our use case it says, in effect: keep rolling over on these conditions, then after N days, delete.

```json
PUT _plugins/_ism/policies/rollover-50gb-7d-delete-30d
{
  "policy": {
    "description": "Roll over at 50gb or 7d, delete after 30d",
    "default_state": "rollover",
    "states": [
      {
        "name": "rollover",
        "actions": [
          {
            "rollover": {
              "min_size": "50gb",
              "min_index_age": "7d"
            }
          }
        ],
        "transitions": [
          { "state_name": "delete", "conditions": { "min_index_age": "30d" } }
        ]
      },
      {
        "name": "delete",
        "actions": [ { "delete": {} } ]
      }
    ],
    "ism_template": {
      "index_patterns": ["logs-*"],
      "priority": 100
    }
  }
}
```

Two things to notice:

- The `rollover` action here uses `min_size` / `min_index_age` (the ISM spelling), which do the same job as the `max_size` / `max_age` conditions you would pass to a manual rollover. When you list several inside one `rollover` object, they are combined with OR, so any one triggers it.
- The `ism_template` block auto-attaches this policy to any index matching `logs-*`, so you set it up once and every future rollover index inherits it.

ISM runs a background job (every 5 minutes by default) that checks each managed index, performs the current state's actions, and advances it when transition conditions are met. That is how `logs-000001` quietly becomes read-only, then gets deleted 30 days later, with nobody touching anything.

### Telling ISM about rollover: the alias link

For ISM's `rollover` action to know which alias to flip, the index template must declare the rollover alias:

```json
PUT _template/logs
{
  "order": 80,
  "index_patterns": ["logs-*"],
  "settings": {
    "index.number_of_shards": "1",
    "index.number_of_replicas": "1",
    "index.refresh_interval": "10s",
    "plugins.index_state_management.rollover_alias": "logs"
  }
}
```

That `plugins.index_state_management.rollover_alias: "logs"` line is the glue. It tells ISM: when you roll over an index born from this template, the write alias to move is `logs`.

## Putting It All Together

Here is the full picture, start to finish:

1. Template: you define `logs-*` settings and set `rollover_alias: logs`.
2. First index and alias: you create `logs-000001` with `is_write_index: true` on the `logs` alias.
3. App writes to the alias: documents land in `logs-000001`.
4. ISM watches: when `logs-000001` hits 50 GB or 7 days, ISM runs `rollover`, which creates `logs-000002` and moves the write alias to it.
5. Repeat forever: `logs-000003`, `logs-000004`, each born automatically.
6. ISM ages them out: 30 days after creation, ISM deletes each old index.

Your application only ever knows about one name: `logs`. Everything else is machinery.

## The Most Common Points of Confusion, Cleared Up

- Does the `-000001` number mean anything? No. With numeric suffixes it is just a creation counter. Use date-math suffixes if you want the date encoded in the name.
- Is rollover the same as ISM? No. Rollover is a single action (make a new index, move the alias). ISM is the automation that calls rollover (and delete, and tier migrations) on a schedule.
- Do I write to `logs-000002` or `logs`? Always the alias, `logs`. Never a physical index name directly.
- Why did my rollover not happen? The conditions were not met. Check the response for `"rolled_over": false`, or for managed indexes use `GET _plugins/_ism/explain/<index>?show_policy=true`.
- Numeric vs date suffix, which matters for retention? Neither directly. Retention is driven by ISM conditions (index age), not by what the name says.

## Conclusion (Author Opinion)

Once I started teaching this as four cooperating pieces instead of one confusing blob, people stopped being afraid of it. That is really the whole trick. The alias is the address, rollover is the act of moving it, the suffix is just a name, and ISM is the robot running the schedule. None of them are complicated on their own.

My advice: start with numeric suffixes and a simple ISM policy, wire the `rollover_alias` once, and only reach for date math when a human or a tool actually benefits from reading the date in the name. Get those basics solid and time-based indexing in OpenSearch stops being mysterious and becomes something you can reason about and tune with confidence.

## References

- <https://opensearch.org/docs/latest/im-plugin/ism/index/>
- <https://opensearch.org/docs/latest/im-plugin/index-rollover/>
- <https://opensearch.org/docs/latest/field-types/supported-field-types/date/>
