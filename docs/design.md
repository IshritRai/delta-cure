# Design

Organized from [`scope.md`](scope.md) and [`architecture.png`](architecture.png). This document
adds no claims beyond the scope; where the scope is silent, the section says so.

## Goal

When a record is erased, update every part of the pipeline that record touched, including the
learned filter's picks, so the result matches a from-scratch re-filter + retrain at lower cost.

## Data flow

### Training path (builds the model)

1. **Raw records** — stable IDs, versioned with DVC.
2. **Learned filter** — scikit-learn quality classifier trained on a labelled slice; stores each
   record's margin.
3. **Selected set** — the records the filter keeps.
4. **Training** — small text classifier (PyTorch, tracked in MLflow); checkpoints every N steps;
   per-batch log of record IDs, seed and step.
5. **Model** — final checkpoint.

### Deletion path (runs on every erase request)

| Step | Action | Updates on training path |
| --- | --- | --- |
| 1. Delete request | `POST /delete/{record_id}` | — |
| 2. Retrain filter | Refit the filter without the record | Refits the learned filter |
| 3. Find flips | Re-score near-boundary records only; compute dropped and admitted sets | Patches the selected set |
| 4. Replay training | Resume from the nearest checkpoint using the batch log | Resumes the training run |
| 5. Verify | Compare against a full re-filter + retrain | — |

Step 3 is the new contribution. Step 4 resumes from the earliest checkpoint touched by any
flipped or deleted record.

## Stored state

Recorded during training, read during deletion.

| Store | Technology | Contents | Read by |
| --- | --- | --- | --- |
| Lineage store | SQLite | Record → filter → selected set → checkpoint links; which checkpoint first used each record | Step 3 (find flips) |
| Checkpoints + batch log | PyTorch checkpoints, per-batch log | Checkpoint every N steps; record IDs, seed and step per batch | Step 4 (replay training) |
| Filter margins | Stored by the learned filter | Each record's margin | Step 3 (near-boundary re-scoring) |
| Dataset snapshots | DVC, Hugging Face `datasets` | Versioned snapshot per deletion | Data versioning |

Table schemas are not specified in the scope; they will be defined in the milestone that
introduces each store and recorded in [`decisions/`](decisions/).

## API

| Endpoint | Purpose |
| --- | --- |
| `POST /delete/{record_id}` | Submit a deletion |
| `GET /status/{job_id}` | Job status |
| `GET /lineage/{record_id}` | Lineage for a record |

## Verification

Compares the service's output with a full re-filter + retrain on small runs (pytest, GitHub
Actions). Success checks, from the scope:

| Check | How it's measured | Pass | Fail |
| --- | --- | --- | --- |
| No missed flips | Flip set vs full re-filter, every deletion | Identical sets | Any mismatch |
| Same training set | Curated set after deletion vs fresh curation | Identical | Any mismatch |
| Model match | Accuracy gap vs full retrain, across seeds | Within seed-to-seed variation | Outside it |
| Cost saved | Wall-clock and GPU time vs full retrain | Lower, reported per deletion | Equal or higher |
| Naive gap shown | Error of drop-only deletion vs full retrain | Measurably worse than this service | No difference |
| Reproducible | Fresh clone runs demo with one command | Works | Fails |

All numbers come from measured runs; none are targets set in advance.
