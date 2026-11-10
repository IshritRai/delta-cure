# 0007. Purge derived artifacts as part of every deletion

- **Status:** Proposed (storage approach to be decided in milestone 1 planning)
- **Date:** 2026-11-10

## Context

The purpose of the service is erasure, but several parts of the planned stack keep copies of a
deleted record or of models trained on it:

- **Dataset snapshots.** The scope plans a versioned snapshot per deletion using DVC. Earlier
  snapshots still contain the record, in DVC's cache and referenced from git history.
- **Checkpoints** at or after the record's first use were trained on it.
- **Filter versions** trained on a deleted labelled-slice record.
- **MLflow artifacts** may contain copies of data or models.

If these remain, the deletion is not complete.

## Decision

1. A deletion job is complete only after a **purge step** removes the record's content from
   storage and deletes every artifact trained on it: superseded checkpoints, superseded filter
   versions, and any experiment-tracking artifacts that contain the record or such models.
   Checkpoints from before the record's first use are kept; they carry no influence from it.
2. Dataset versions are represented as **manifests of record IDs** over a content store that
   supports physical deletion, rather than as full copies per deletion.
3. Whether DVC is kept (for example only to version the initial raw import) or dropped is decided
   in milestone 1 planning.
4. Deleted records leave a **tombstone** (record ID, deletion time, job ID) in the lineage store
   so status and audit queries still work. Tombstones hold no record content. Whether record IDs
   themselves can be personal data is listed as an open question in the PRD.

## Consequences

- An "erasure complete" check is added to the success checks: after a deletion, no stored
  artifact contains the record or a model trained on it.
- Purging old checkpoints means a later deletion can never replay from before an earlier
  deletion's first-use point using superseded state; replay always starts from current, valid
  checkpoints.

## Alternatives considered

- **DVC snapshot per deletion (scope as written).** Gives easy versioning but keeps deleted data
  in cache and history unless purged with history rewriting, which defeats the point.
