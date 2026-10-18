---
tags: opensearch, aws, ism, cost
date: "2026-10-17"
category: Log Analytics
---

*__Blog Post Publish Date:__ 2026/10/17*

---

# How I Cut $8,000 to $10,000 a Month Off an OpenSearch Cluster by Rethinking Storage

This is not a best-practices guide. It is a field report of how I restructured a production OpenSearch cluster to cut storage cost dramatically, somewhere between $8,000 and $10,000 a month, by understanding where the money was going, accepting some calculated risks, and weighing them against the benefits. Your numbers and risk tolerance will differ. The point is the reasoning, not the recipe.

## Step Zero: Find Where the Money Actually Goes

Before touching anything, I broke down the cluster cost line by line. The result was unambiguous: the single largest cost of the cluster was EBS. Not compute, not data transfer. The network-attached block storage holding all the indexed data, replicated, sitting on disks provisioned for the full retention window.

That reframed the whole problem. This was not "make the cluster faster" or "add nodes". It was "stop paying premium block-storage prices for data that does not need premium block storage". Everything that follows is a consequence of that one observation.

The key insight: not all data has the same value or the same access pattern. Data from the last few hours is queried constantly and needs to be fast. Data from four months ago is touched rarely, if ever. Paying the same per-GB storage price for both is the waste.

## The Shape of the Solution: Three Tiers by Age

I split the data's life into stages and matched each stage to the cheapest storage that still met its real access needs.

### Tier 1, hot: instance storage, no EBS

For recent data, I built hot nodes on EC2 instance types with locally-attached NVMe instance storage and no EBS at all. Local NVMe is far faster than network-attached EBS, there is no network hop between the node and its disk, which is exactly what you want for heavy indexing and near-real-time search on fresh data.

The trade-offs of instance storage are real:

- __Capacity is much smaller__ than what you can attach via EBS. That is fine. The hot tier only needs to hold a few days of data.
- __It is ephemeral.__ If the instance dies or rotates, its local disk is wiped. To make that survivable, the hot tier runs with shard replicas (one, sometimes two), so a lost node never means lost data. On the hot tier I pay for replication, and in exchange I get both high IO performance and fault tolerance.

So: hot data is fastest storage plus full replica-based redundancy. Expensive per GB, but small, so the total is contained.

### Tier 2, warm: max EBS, no replicas (the real trick)

After 3 days, indexes move to a warm tier. These warm nodes are built completely differently: high memory, and the maximum EBS a node can attach, 16 TB. This is where the bulk of the data lives for the long haul, so capacity-per-node matters more than raw IO.

Here is the move that saved the most money. The index template provisions data with one replica (up to two when warranted) while it is hot, so nothing is lost if a hot node dies. But the moment an index transitions to the warm tier, I disable replicas entirely and lean on the durability guarantee that EBS already provides.

The reasoning:

- EBS is network-attached and durable on its own. If a warm node dies or gets rotated, the data is still sitting safely on its EBS volume. A new node is born, re-attaches the volume, and carries on, no data lost.
- Because EBS already guarantees persistence, a second copy in the cluster is redundant for durability. Keeping replicas on the warm tier would mean paying for two full copies of months of data on the most expensive storage line in the bill.

Dropping warm-tier replicas cut the EBS disk consumption of that data by at least half. That single decision, trusting EBS durability instead of in-cluster replication for long-lived, rarely-written data, was the bulk of the savings.

This is a deliberate trade, not a free lunch. Without replicas, a warm index is briefly unavailable for query during the window when a node is being replaced and the volume re-attaches. For data that is months old and queried occasionally, that short unavailability was an easy price to pay. On a hot index taking live writes, it would not have been.

### Tier 3, cold / searchable: snapshot to S3, restore on demand

After 6 months, the data moves off the cluster's disks entirely. The index is snapshotted to S3 and then removed from the warm nodes. S3 is dramatically cheaper per GB than EBS, and this data is now archival, needed only for occasional audits.

Data in S3 is not immediately indexed or queryable. When someone actually needs it, I restore it on demand using searchable snapshots. To serve those restores I spin up a dedicated searchable node, again with no EBS, only fast local NVMe instance storage. In practice that NVMe acts as a cache in front of the snapshot: the authoritative copy of the data lives in the S3 bucket, and the searchable node just holds enough locally to serve queries quickly.

Because the real data is safe in S3, these searchable indexes are restored with no replicas. If the searchable node dies, nothing is lost. The data is intact in the bucket, and you simply restore again.

> <i class="fa-solid fa-circle-info"></i> **A practical tip that pays off here:**
>
> Make your rollover index suffix a date (for example `logs-2026.02.14-000001`). When you are hunting through months of snapshots in S3 for an audit, the date in the index name instantly tells you the approximate time range the index covers. No guessing, no opening each one to check timestamps.

## Why 3 Days and 6 Months?

Those two numbers, 3 days hot and 6 months before archival, are not universal constants. They are what made sense for this organization's access patterns: live dashboards and alerting worked almost entirely against the last couple of days, warm data covered the typical investigation window, and anything older was purely audit material.

Your thresholds will be different. A security team might keep data hot for a week. A team with strict compliance retention might keep warm data for a year. The specific numbers matter far less than the discipline of defining them. What matters is drawing the lines clearly:

- __What is hot__: recently written, queried constantly, needs speed and redundancy.
- __What is warm__: aging, read occasionally, needs capacity and durability but not peak IO.
- __What is cold / searchable__: archival, touched rarely, needs the cheapest durable storage you can restore from.

Once those categories are explicit, the storage decisions follow naturally.

## The ISM Policy That Automates It

All of this runs automatically through an Index State Management policy. Below is a generalized, anonymized version of the policy that drives the lifecycle: rollover, snapshot, warm migration, replica removal, and deletion. The notification blocks and internal identifiers have been stripped out to keep it generic.

```json
PUT _plugins/_ism/policies/rollover-50gb-30d-snapshot-warm-3d-delete-180d
{
  "policy": {
    "description": "Roll over at 50GB primary shard or 30d. Set read-only, snapshot to S3 at 03:00, move to warm after 3d, disable replicas on warm, delete at 180d.",
    "ism_template": [
      {
        "index_patterns": ["logs-app*"],
        "priority": 80
      }
    ],
    "default_state": "wait-first-write",
    "states": [
      {
        "name": "wait-first-write",
        "actions": [],
        "transitions": [
          { "state_name": "rollover", "conditions": { "min_doc_count": "1" } },
          { "state_name": "rollover", "conditions": { "min_index_age": "30d" } }
        ]
      },
      {
        "name": "rollover",
        "actions": [
          {
            "rollover": {
              "min_primary_shard_size": "50gb",
              "min_index_age": "30d"
            }
          }
        ],
        "transitions": [
          { "state_name": "read-only" }
        ]
      },
      {
        "name": "read-only",
        "actions": [
          { "read_only": {} }
        ],
        "transitions": [
          {
            "state_name": "snapshot",
            "conditions": {
              "cron": {
                "cron": { "expression": "* 3 * * *", "timezone": "UTC" }
              }
            }
          }
        ]
      },
      {
        "name": "snapshot",
        "actions": [
          {
            "snapshot": {
              "repository": "my-s3-repository",
              "snapshot": "{{ctx.index}}"
            }
          }
        ],
        "transitions": [
          { "state_name": "warm", "conditions": { "min_index_age": "3d" } }
        ]
      },
      {
        "name": "warm",
        "actions": [
          {
            "allocation": {
              "require": { "temp": "warm" },
              "include": {},
              "exclude": {},
              "wait_for": false
            }
          }
        ],
        "transitions": [
          { "state_name": "disable-replicas" }
        ]
      },
      {
        "name": "disable-replicas",
        "actions": [
          {
            "replica_count": { "number_of_replicas": 0 }
          }
        ],
        "transitions": [
          { "state_name": "delete", "conditions": { "min_index_age": "180d" } }
        ]
      },
      {
        "name": "delete",
        "actions": [
          { "delete": {} }
        ],
        "transitions": []
      }
    ]
  }
}
```

The lifecycle reads top to bottom as the story of a single index:

1. __wait-first-write__: do not act on an empty index. Wait for the first document (or 30 days as a safety net) before rolling.
2. __rollover__: start a fresh write index once the current one hits 50 GB per primary shard or 30 days old.
3. __read-only__: freeze the rolled-over index. Nothing more will be written to it.
4. __snapshot__: at 03:00, snapshot it to the S3 repository. The archival copy now exists before anything risky happens to in-cluster redundancy.
5. __warm__: 3 days in, relocate the index to the warm (high-memory, big-EBS) nodes.
6. __disable-replicas__: drop to zero replicas, trusting EBS durability for this aging data. This is the money-saving step.
7. __delete__: at 180 days, remove it from the cluster. The S3 snapshot remains for on-demand searchable restore.

Note the ordering: the snapshot happens before replicas are disabled. By the time I am relying on a single EBS-backed copy in the warm tier, there is already an independent copy in S3. The risk of zero replicas is bounded by that archival safety net.

## What I Ended Up With

After the restructure, the cluster was no longer one undifferentiated pool of expensive EBS. It was three purpose-built layers:

| Tier | Storage | Redundancy | Durability from | Serves |
| --- | --- | --- | --- | --- |
| Hot | Local NVMe (no EBS) | Replicas (1-2) | In-cluster replication | High-IO indexing + live search on recent data |
| Warm | Max EBS (16 TB), high memory | No replicas | EBS volume persistence | Long-term indexed data, occasional reads |
| Cold / Searchable | S3 + NVMe cache node (no EBS) | No replicas | S3 object durability | On-demand audit restores via searchable snapshots |

- __Hot__ gave me high-IO performance for recent data with full fault tolerance via replicas.
- __Warm__ gave me long-term indexed data with persistence guaranteed by EBS, no replica tax.
- __Cold / searchable__ gave me even-longer-term data restored on demand from S3 for the occasional audit, with no standing disk cost at all.

Each tier pays only for what its data actually needs. The bill dropped $8,000 to $10,000 a month, and nothing that mattered got slower, because the only data I slowed down (or made restore-on-demand) was data nobody was querying in real time anyway.

## Conclusion (Author Opinion)

This was not clever OpenSearch trivia. It was: measure where the cost is, understand the access pattern of your data, and stop paying premium-storage prices for data that does not need it. The savings came from being willing to drop redundancy where a cheaper durability guarantee already existed (EBS, then S3), and from understanding exactly what risk that introduced and when it was acceptable.

Again, this is a report, not a prescription. I accepted reduced-redundancy windows and on-demand-only access for old data because, for this workload, the cost of those trade-offs was near zero and the savings were large. Every case is unique. Before you copy any of it, make sure that same math holds for yours.

## References

- <https://opensearch.org/docs/latest/im-plugin/ism/index/>
- <https://aws.amazon.com/ebs/pricing/>
- <https://opensearch.org/docs/latest/tuning-your-cluster/availability-and-recovery/snapshots/searchable_snapshot/>
