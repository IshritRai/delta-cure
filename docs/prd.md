# Product Requirements Document: Curator-Aware Unlearning (delta-cure)

| Field | Value |
| --- | --- |
| Owner | Ishrit Rai |
| Status | Draft for review |
| Version | 0.1 |
| Last updated | 2026-11-10 |
| Related | [Scope](scope.md) · [Design](design.md) · [Decisions](decisions/README.md) |

## 1. Summary

delta-cure is a deletion service for ML training pipelines that use a learned data filter. When
a record must be erased, the service removes it from every part of the pipeline it touched:
the stored data, the filter that decided which records to train on, the set of records the
filter selected, and the trained model. The output must match what a full re-filter and retrain
would have produced, at lower cost, with no stored copy of the record or of anything trained on
it left behind.

## 2. Background and problem

Training pipelines increasingly curate data with a **learned filter**: a quality classifier,
trained on a small labelled slice, that scores a larger pool and keeps the records above a
threshold. Erasure requests (for example under data-protection laws that give people a right to
have their data deleted) require that a person's records stop influencing the model.

Existing exact-unlearning approaches remove the record from the model's training set and
retrain or replay from a checkpoint. They treat the selected training set as fixed. But when the
deleted record was in the filter's labelled slice, it also shaped the filter. Removing it can
flip other records' keep/drop decisions: some kept records should now be dropped and some
dropped records should now be admitted. A pipeline that ignores these flips ends up with a
model that does not match a genuine retrain on the post-deletion data. The closest prior work
handles curation with a fixed filter only (see [Sources in the scope](scope.md#sources)).

Retraining everything from scratch after each deletion is correct but expensive.

## 3. Goals and non-goals

### Goals

| ID | Goal |
| --- | --- |
| G1 | **Exactness.** After each deletion, the selected set equals a fresh curation, and the model matches a full re-filter and retrain. |
| G2 | **Lower cost.** Each deletion costs less wall-clock and compute time than a full re-filter and retrain, as measured. |
| G3 | **Complete erasure.** No stored artifact contains a deleted record or a model trained on it. |
| G4 | **Auditability.** For any record, an operator can see where it was used and, once deleted, when and by which job. |
| G5 | **Reproducibility.** A fresh clone runs the end-to-end demo with one command, and every reported number can be regenerated. |

### Non-goals

- Approximate unlearning (for example gradient-ascent or influence-based weight edits without a
  correctness guarantee).
- Models other than the small text classifier used in the demo; filters other than linear
  models; quantile-based ("top k %") selection ([ADR 0003](decisions/0003-certified-flip-band.md)).
- Distributed or multi-GPU training.
- Certifying legal compliance. The service provides technical erasure; whether that satisfies a
  given law is outside this project.
- A user interface beyond the HTTP API.

## 4. Users and personas

| Persona | Needs |
| --- | --- |
| **ML platform engineer** (primary) | Runs training pipelines; must honour deletion requests without rerunning everything; needs a service to call and clear job status. |
| **Privacy or compliance officer** | Needs evidence that a deletion is complete: what was removed, when, and that nothing trained on the record remains. |
| **ML researcher** | Wants to compare unlearning methods; needs reproducible benchmarks and exact reference results. |

## 5. Use cases

| ID | As a… | I want to… | So that… |
| --- | --- | --- | --- |
| UC1 | platform engineer | submit a record ID for deletion and get a job ID | I can track an erasure request |
| UC2 | platform engineer | check a job's status | I know when the erasure is complete or if it failed |
| UC3 | compliance officer | look up a record's lineage, or its tombstone after deletion | I can show where it was used and when it was removed |
| UC4 | platform engineer | submit many deletions at once | they are handled in one pass instead of one retrain each |
| UC5 | researcher | run the benchmark suite from a fresh clone | I can reproduce the reported results |
| UC6 | researcher | compare the service against naive drop-only deletion and full retrain | I can see the size of the error the service avoids |

## 6. Functional requirements

Priority uses MoSCoW: **M**ust, **S**hould, **C**ould. Each requirement lists the milestone that
delivers it.

### 6.1 Training pipeline

| ID | Requirement | Priority | Milestone |
| --- | --- | --- | --- |
| FR1 | Every record has a stable ID that never changes across dataset versions. | M | 1 |
| FR2 | The filter is a logistic regression on data-independent features with a fixed score threshold, trained on a labelled slice. | M | 1 |
| FR3 | The filter step stores, per pool record, its score and feature norm, plus the weights and bias of each filter version. | M | 1 |
| FR4 | Training orders records within each epoch by a per-record hash and seeds other randomness per step ([ADR 0004](decisions/0004-deterministic-record-ordering.md)). | M | 1 |
| FR5 | Checkpoints every N steps store model, optimizer and scheduler state, step, epoch, seed, and data and filter versions ([ADR 0005](decisions/0005-checkpoint-contents-and-determinism.md)). | M | 1 |
| FR6 | A batch log records the record IDs, seed and step of every training batch. | M | 1 |
| FR7 | One command trains the pipeline end to end, with runs tracked in MLflow. | M | 1 |

### 6.2 Reference paths

| ID | Requirement | Priority | Milestone |
| --- | --- | --- | --- |
| FR8 | A naive deletion path removes only the record and replays, without touching the filter. | M | 2 |
| FR9 | A full reference path re-filters and retrains from scratch on post-deletion data, using the same ordering and schedule. | M | 2 |

### 6.3 Deletion engine

| ID | Requirement | Priority | Milestone |
| --- | --- | --- | --- |
| FR10 | Each deleted record is classified as pool-only (selected or not) or labelled-slice, and only labelled-slice deletions trigger a filter retrain ([ADR 0002](decisions/0002-two-deletion-cases.md)). | M | 3 |
| FR11 | After a filter retrain, only records inside the certified band are re-scored, and the dropped and admitted sets are computed ([ADR 0003](decisions/0003-certified-flip-band.md)). | M | 3 |
| FR12 | Training replays from the latest checkpoint at or before the first batch changed by any deleted, dropped or admitted record. | M | 4 |
| FR13 | After each deletion, the record's content, superseded checkpoints, superseded filter versions and tracking artifacts containing it are purged, and a tombstone is written ([ADR 0007](decisions/0007-erasure-of-derived-artifacts.md)). | M | 5 |

### 6.4 Service API

| ID | Requirement | Priority | Milestone |
| --- | --- | --- | --- |
| FR14 | `POST /delete/{record_id}` queues a deletion and returns a job ID. A repeated request for the same pending record returns the existing job. | M | 5 |
| FR15 | `POST /delete/{record_id}` for an unknown or already-deleted record returns a clear error or the tombstone, not a new job. | M | 5 |
| FR16 | `GET /status/{job_id}` reports queued, running, succeeded or failed, with the step reached and a failure reason. | M | 5 |
| FR17 | `GET /lineage/{record_id}` returns the record's filter, selected-set and checkpoint links, or its tombstone. | M | 5 |
| FR18 | Pending deletions are processed together as a batch with one filter retrain and one replay ([ADR 0008](decisions/0008-batched-deletions.md)). | M | 5 |
| FR19 | Each completed job records its measured cost (wall-clock time, compute time, band size, flips, replay start step). | S | 5 |

### 6.5 Benchmarking and packaging

| ID | Requirement | Priority | Milestone |
| --- | --- | --- | --- |
| FR20 | A benchmark runs random and adversarial deletion sequences, single and batched, and reports results per deletion case. | M | 6 |
| FR21 | `docker compose up` starts the demo from a fresh clone. | M | 6 |
| FR22 | The README reports only results produced by the benchmark in this repository, with the command, seed and commit used. | M | 6 |
| FR23 | A command-line interface wraps the API for scripted deletions. | C | 6 |

## 7. Non-functional requirements

| ID | Category | Requirement |
| --- | --- | --- |
| NFR1 | Correctness | The flip set equals full re-filtering for every deletion; this holds by construction and is also tested. |
| NFR2 | Correctness | On small CPU runs, replay produces parameters bit-identical to a full retrain. |
| NFR3 | Correctness | On larger runs, the accuracy gap to a full retrain is within seed-to-seed variation. |
| NFR4 | Performance | Per-deletion cost is lower than a full retrain and is reported per deletion. No target is set in advance; the baseline comes from milestone 2 measurements. |
| NFR5 | Privacy | After a job succeeds, no store holds the record's content or an artifact trained on it. Logs never contain record content. |
| NFR6 | Reliability | A job interrupted mid-way can be retried without corrupting checkpoints or the lineage store; the previous valid state stays usable until the new one is complete. |
| NFR7 | Reproducibility | All randomness is seeded; dependencies are pinned; one command reproduces each reported number. |
| NFR8 | Security | No secrets or absolute paths in code; configuration comes from files or environment variables. The API is not exposed beyond localhost without an authentication layer (see open question Q3). |
| NFR9 | Observability | Each job emits structured logs per step and records metrics in MLflow. |
| NFR10 | Maintainability | Type hints and docstrings on all public functions; lint, type checks and tests pass in CI on every pull request. |

## 8. Success metrics

From the [scope's success checks](scope.md#success-checks). All values come from measured runs;
none are targets set in advance.

| Metric | Measured as | Pass |
| --- | --- | --- |
| Missed flips | Flip set vs full re-filter, every deletion | Zero |
| Training-set match | Curated set after deletion vs fresh curation | Identical |
| Replay exactness | Replay vs full retrain, small CPU runs | Bit-identical |
| Model match | Accuracy gap vs full retrain, across seeds | Within seed-to-seed variation |
| Cost per deletion | Wall-clock and compute time vs full retrain | Lower |
| Naive gap | Error of drop-only deletion vs full retrain | Measurably worse than the service |
| Erasure completeness | Search of all stores after deletion | Nothing found |
| Reproducibility | Fresh clone runs the demo with one command | Works |

## 9. Assumptions and constraints

- The filter is linear with a fixed threshold, and its features do not depend on the training
  data (ADR 0003).
- Training is small enough to run deterministically on CPU for exactness tests.
- A single worker processes deletions; there is one training run per deployment.
- Python 3.11; dependencies pinned in `pyproject.toml`.

## 10. Dependencies

scikit-learn, PyTorch, MLflow, Hugging Face `datasets`, SQLite, FastAPI, Docker Compose, and a
public text dataset to be chosen in milestone 1. DVC is under review (ADR 0007).

## 11. Risks and mitigations

| Risk | Impact | Mitigation |
| --- | --- | --- |
| Replay saves little under multi-epoch training, because every record appears in epoch 1 | "Cost saved" check fails or passes trivially | Decide the training schedule before building (ADR 0006); report the ceiling alongside measurements |
| Flips are rare on realistic data | Naive gap is small and the contribution looks marginal | Report it as a finding; adversarial sequences target labelled-slice records with high influence |
| Nondeterminism in training | Replay and retrain differ for reasons unrelated to correctness | CPU deterministic mode and exact comparison in tests (ADR 0005) |
| Stored artifacts retain deleted data | Erasure is incomplete | Purge step and erasure-completeness check (ADR 0007) |
| Feature transforms fitted on the data | Certified band is no longer sound | Data-independent features (ADR 0003) |
| Checkpoint storage grows with full state | Disk usage limits checkpoint frequency | Measure and report; tune N |

## 12. Release plan

| Milestone | Deliverable |
| --- | --- |
| 1. Baseline pipeline | One command trains end to end |
| 2. Reference path | Naive and full paths run; their gap is measured |
| 3. Flip engine | Tests show no missed flips, including adversarial deletions |
| 4. Replay engine | Bit-identical to full retrain on small CPU runs |
| 5. Service | Deletion works through the API, including batching and purge |
| 6. Benchmark and polish | Public repo with measured results and one-command demo |

Each milestone has one GitHub issue, one branch and one pull request.

## 13. Open questions

| ID | Question | To decide by |
| --- | --- | --- |
| Q1 | Standard epochs or staged training? (ADR 0006) | Milestone 1 plan |
| Q2 | Keep DVC for the initial import, or drop it? (ADR 0007) | Milestone 1 plan |
| Q3 | What authentication should the API have outside the local demo? | Milestone 5 plan |
| Q4 | Can a record ID itself be personal data, and if so, how are tombstones keyed? | Milestone 5 plan |
| Q5 | Which dataset, labelled slice and model size make flips measurable while keeping exactness tests fast? | Milestone 1 plan |
| Q6 | What batching policy (immediate, delayed, size limit) should the service use? | Milestone 5 plan |

## 14. Glossary

| Term | Meaning |
| --- | --- |
| Learned filter | Classifier that scores candidate records and keeps those above a threshold |
| Labelled slice | The labelled records used to train the filter |
| Pool | Candidate records the filter scores |
| Selected set | Pool records the filter keeps; the model's training data |
| Flip | A record whose keep/drop decision changes after the filter is retrained |
| Dropped / admitted | Flips from kept to dropped / from dropped to kept |
| Certified band | Records whose decision could change given the measured weight change; all others provably cannot |
| Replay | Resuming training from a checkpoint with updated data instead of retraining from scratch |
| Tombstone | Record of a deletion (ID, time, job) holding no record content |

## 15. Document history

| Version | Date | Change |
| --- | --- | --- |
| 0.1 | 2026-11-10 | First draft from the scope and ADRs 0001–0008 |
