# 0008. Process deletions in batches

- **Status:** Accepted
- **Date:** 2026-11-10

## Context

Deletion requests arrive one at a time through `POST /delete/{record_id}`, but each job may
retrain the filter and replay training. Running one replay per request repeats work that a
single replay could cover, and concurrent jobs would conflict over the same checkpoints.

## Decision

- Requests are queued. A single worker takes all pending requests as one **batch**.
- For a batch, the filter is retrained once without all labelled-slice deletions in it, flips
  are computed once against that retrain, and training replays once from the earliest point any
  record in the batch touches.
- Requests arriving while a batch runs go into the next batch.
- Each request gets its own job ID; `GET /status/{job_id}` reports the status of the batch it
  belongs to.
- The guarantee after each batch is that the result equals a full re-filter and retrain without
  every record deleted so far.

The policy for when to start a batch (immediately, after a delay, or at a size limit) is decided
in milestone 5.

## Consequences

- Only one worker writes checkpoints, so there are no concurrent-write conflicts.
- Latency for an individual request depends on the batch it lands in; the PRD treats this as a
  measured property, not a target.
- Milestone 6 benchmarks both single deletions and batches.

## Alternatives considered

- **One job per request.** Simpler status model, but repeats replay work and needs locking.
