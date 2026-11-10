# 0004. Order training data by a per-record hash

- **Status:** Accepted
- **Date:** 2026-11-10

## Context

Replay resumes training from the nearest checkpoint before the first batch a deletion changes.
With ordinary per-epoch random shuffling, removing or adding a single record changes the whole
permutation, so the first changed batch is near step 0 and replay degenerates to a full retrain.
Records admitted by a flip were never in any batch, so "the first batch they touch" is undefined
unless an ordering rule says where they would have been.

## Decision

Within epoch `e`, the selected records are sorted by `h(seed, e, record_id)`, where `h` is a
fixed cryptographic hash (for example BLAKE2b) truncated to an integer. Batches are consecutive
chunks of `B` records in that order; the rule for a final partial batch is fixed in milestone 1
and applied identically everywhere.

- Removing a record leaves the relative order of all other records unchanged.
- An admitted record has a well-defined position.
- The first changed batch in epoch `e` is the batch containing the earliest changed position.
- Any other randomness during training (dropout, augmentation) is seeded per step from
  `(seed, global_step)`, so replay does not depend on how far a random stream had advanced.

The full-retrain reference path uses the same ordering rule, so comparing replay with a full
retrain is a like-for-like comparison.

## Consequences

- Replay can start at the checkpoint at or before the first changed batch.
- Every batch after the first change shifts by one or more records, so everything after the
  first change is retrained.
- **Savings ceiling:** with `E` epochs over the same data, every record appears in epoch 1, so
  the first change is always in epoch 1 and replay redoes at least the last `E − 1` epochs. ADR
  0006 addresses this.

## Alternatives considered

- **Random shuffling with a stored permutation.** Removing a record from a stored permutation
  keeps others in order, but admitted records still have no position, and the permutation must
  be stored per epoch.
- **Fixed sort by record ID.** Deterministic but identical every epoch, which can hurt training.
