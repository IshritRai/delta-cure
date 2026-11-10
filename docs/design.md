# Design

Organized from [`scope.md`](scope.md), [`architecture.png`](architecture.png) and the
[architecture decision records](decisions/README.md). Product requirements are in
[`prd.md`](prd.md). Where a question is still open, this document says so and links the ADR that
will settle it.

## Goal

When a record is erased, update every part of the pipeline that record touched, including the
learned filter's picks, so the result matches a from-scratch re-filter + retrain at lower cost,
and leave no stored copy of the record or of anything trained on it.

## Data flow

### Training path (builds the model)

1. **Raw records** with stable IDs. Each dataset version is a manifest of record IDs over a
   content store that supports physical deletion ([ADR 0007](decisions/0007-erasure-of-derived-artifacts.md)).
2. **Learned filter**: scikit-learn logistic regression trained on a **labelled slice**.
   - Features are data-independent (for example feature hashing), so deleting a record never
     changes another record's features ([ADR 0003](decisions/0003-certified-flip-band.md)).
   - A record is kept when its score `s(x) = w·x + b` is at least a fixed threshold `τ`.
   - For every pool record, the filter step stores the score `s(x)` and the feature norm `‖x‖₂`.
3. **Selected set**: the pool records the filter keeps.
4. **Training**: small PyTorch text classifier, tracked in MLflow.
   - Within each epoch, records are ordered by `h(seed, epoch, record_id)` and cut into batches
     of fixed size ([ADR 0004](decisions/0004-deterministic-record-ordering.md)).
   - Other randomness is seeded per step from `(seed, global_step)`.
   - Checkpoints every N steps hold model, optimizer and scheduler state, step, epoch, seed, and
     data and filter versions ([ADR 0005](decisions/0005-checkpoint-contents-and-determinism.md)).
   - A per-batch log records the record IDs, seed and step of every batch.
   - The training schedule (standard epochs vs staged slices) is open:
     [ADR 0006](decisions/0006-training-schedule-for-replay-savings.md).
5. **Model**: final checkpoint.

### Deletion path (runs on every erase request)

Requests are queued and processed in batches; each step below runs once per batch
([ADR 0008](decisions/0008-batched-deletions.md)).

| Step | Action | Updates on training path |
| --- | --- | --- |
| 1. Delete request | `POST /delete/{record_id}` enqueues the request and returns a job ID | — |
| 2. Classify | Look up each record: pool only (selected or not) or labelled slice ([ADR 0002](decisions/0002-two-deletion-cases.md)) | — |
| 3. Retrain filter | Only if the batch contains labelled-slice records: refit without them | Refits the learned filter |
| 4. Find flips | Re-score only records inside the certified band; compute dropped and admitted sets | Patches the selected set |
| 5. Replay training | Resume from the latest checkpoint at or before the first changed batch, using the batch log | Resumes the training run |
| 6. Purge | Delete the records' content, superseded checkpoints and filter versions, and tracking artifacts containing them; write tombstones | Removes stale state |
| 7. Verify | On small runs, compare with a full re-filter + retrain | — |

Step 4 is the new contribution.

### Certified flip band (step 4)

After the retrain, with `Δw = w' − w` and `Δb = b' − b`, every record's score moves by at most
`‖Δw‖₂ · ‖x‖₂ + |Δb|`. A record is re-scored exactly only if

    |s(x) − τ| ≤ ‖Δw‖₂ · ‖x‖₂ + |Δb| + ε

where `ε` is a small floating-point slack. All other records provably keep their decision. Flips
are band records whose decision changed: **dropped** (kept → dropped) and **admitted**
(dropped → kept).

### Replay start point (step 5)

With hash ordering, removing a record keeps everyone else's relative order, and an admitted
record has a defined slot. The first changed batch is the one containing the earliest changed
position across all deleted, dropped and admitted records. Replay starts from the latest
checkpoint at or before it. Under standard multi-epoch training this is always in epoch 1,
which caps the savings; ADR 0006 weighs staged training as the fix.

## Stored state

Recorded during training, read during deletion.

| Store | Technology | Contents | Read by |
| --- | --- | --- | --- |
| Lineage store | SQLite | Record → filter → selected set → checkpoint links; labelled-slice, pool and selected membership; which checkpoint first used each record; deletion tombstones | Steps 2, 4, 5, 6 |
| Filter state | Stored by the filter step | Weights and bias per filter version; each record's score and feature norm | Steps 3, 4 |
| Checkpoints + batch log | PyTorch checkpoints, per-batch log | Full training state every N steps; record IDs, seed and step per batch | Step 5 |
| Dataset versions | Hugging Face `datasets`; DVC under review | Record content store plus a manifest of record IDs per version | Steps 1, 6 |

Table schemas are defined in the milestone that introduces each store and recorded as ADRs.

## API

| Endpoint | Purpose |
| --- | --- |
| `POST /delete/{record_id}` | Submit a deletion; returns a job ID |
| `GET /status/{job_id}` | Status of the batch the job belongs to |
| `GET /lineage/{record_id}` | Lineage for a record, or its tombstone if deleted |

The batching policy and response formats are defined in milestone 5.

## Verification

Compares the service's output with a full re-filter + retrain on small runs (pytest, GitHub
Actions). Exactness tests run on CPU with deterministic algorithms and compare parameters for
exact equality. The success checks are listed in [`scope.md`](scope.md#success-checks).

All numbers come from measured runs; none are targets set in advance.
