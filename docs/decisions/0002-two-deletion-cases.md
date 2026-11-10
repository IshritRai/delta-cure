# 0002. Handle pool-only and labelled-slice deletions separately

- **Status:** Accepted
- **Date:** 2026-11-10

## Context

The learned filter is trained on a **labelled slice** and then scores the **pool** of candidate
records. The scope's problem statement says a deleted record "also trained the filter", but that
is only true when the record is in the labelled slice. A record that was only scored did not
influence the filter's weights, so deleting it cannot flip any other record's keep/drop decision.

## Decision

The deletion engine classifies every deleted record before doing any work:

| Case | Record was in | Filter | Flips | Training |
| --- | --- | --- | --- | --- |
| A. Pool only, not selected | Pool | Unchanged | None | Unchanged (never reached the model) |
| B. Pool only, selected | Pool and selected set | Unchanged | None | Replay without the record |
| C. Labelled slice | Labelled slice (and possibly the pool) | Retrained without it | Computed (ADR 0003) | Replay without the record and with flips applied |

All cases also remove the record from storage and purge derived artifacts (ADR 0007).

The lineage store records, per record, whether it is in the labelled slice, the pool, and the
selected set, so classification is a lookup.

## Consequences

- Cases A and B skip the filter retrain and flip computation entirely.
- Benchmarks (milestone 6) report results per case, so the cost of case C is not averaged away by
  the cheaper cases.
- Adversarial deletion sequences target case C, since that is the only case where the naive
  "drop the record only" approach can be wrong.

## Alternatives considered

- **Always retrain the filter.** Correct but wasteful for cases A and B, and it would hide the
  real cost of case C in averages.
