# Architecture Decision Records

Significant design decisions, one per file. Process: [0001](0001-record-architecture-decisions.md).
New records start from [`template.md`](template.md).

| # | Decision | Status |
| --- | --- | --- |
| [0001](0001-record-architecture-decisions.md) | Record architecture decisions | Accepted |
| [0002](0002-two-deletion-cases.md) | Handle pool-only and labelled-slice deletions separately | Accepted |
| [0003](0003-certified-flip-band.md) | Re-score only records inside a certified flip band | Accepted |
| [0004](0004-deterministic-record-ordering.md) | Order training data by a per-record hash | Accepted |
| [0005](0005-checkpoint-contents-and-determinism.md) | Make checkpoints complete and replay bit-exact on CPU | Accepted |
| [0006](0006-training-schedule-for-replay-savings.md) | Choose a training schedule that lets replay save work | Proposed |
| [0007](0007-erasure-of-derived-artifacts.md) | Purge derived artifacts as part of every deletion | Proposed |
| [0008](0008-batched-deletions.md) | Process deletions in batches | Accepted |
