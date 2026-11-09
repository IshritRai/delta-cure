# Curator-Aware Unlearning — Engineering Scope

A deletion service for ML training pipelines. When someone asks for their data to be erased, it updates every part of the pipeline that data touched, including a learned filter's picks, without retraining from scratch.

## Problem

Many pipelines use a **learned filter** (a quality classifier) to decide which records reach the model. When a record is deleted, today's tools remove it from the model's training set and stop there.

But that record also trained the filter. Without it, the filter's keep/drop decisions can flip: some kept records should now drop, and some rejected records should now get in. This service finds those flips and updates the model to match a from-scratch retrain, at lower cost.

## Architecture

![System architecture: training path, deletion path and stored state](architecture.png)

Each deletion step updates the training step above it. The highlighted step is the new part: only records near the filter's boundary are re-scored. A lineage store records which checkpoint first used each record, so replay starts as late as possible.

## Components and stack

Every layer uses standard, widely used tools, so the novel part (flip handling) stands out.

| Layer | Scope | Tools |
| --- | --- | --- |
| Data versioning | Raw records with stable IDs; versioned snapshots per deletion | DVC, Hugging Face `datasets` |
| Learned filter | Quality classifier trained on a labelled slice; stores each record's margin | scikit-learn `LogisticRegression` |
| Training | Small text classifier; checkpoints every N steps; per-batch log of record IDs, seed and step | PyTorch, MLflow |
| Lineage store | Record → filter → selected set → checkpoint links | SQLite |
| Deletion engine | Retrain filter, re-score near-boundary records, compute flips, replay from nearest checkpoint | Python package |
| API | `POST /delete/{record_id}`, `GET /status/{job_id}`, `GET /lineage/{record_id}` | FastAPI |
| Verification | Compares output with a full re-filter + retrain on small runs | pytest, GitHub Actions |
| Packaging | One-command demo and README with measured results | Docker Compose |

## Milestones

Each milestone ends with something runnable.

1. **Baseline pipeline.** Dataset with stable IDs, filter, training loop with checkpoints and batch log, MLflow tracking. Deliverable: one command trains end to end.
2. **Reference path.** Naive deletion (drop the record only) and full re-filter + retrain. Deliverable: both paths run and their gap is measured.
3. **Flip engine.** Retrain filter, re-score records within a margin band, compute dropped and admitted sets. Deliverable: tests show no missed flips against full re-filtering.
4. **Replay engine.** Resume from the earliest checkpoint touched by any flipped or deleted record, using the batch log. Deliverable: result matches full retrain on small runs.
5. **Service.** FastAPI endpoints, lineage store, job status. Deliverable: deletion works through the API.
6. **Benchmark and polish.** Random and adversarial deletion sequences, cost comparison, Docker Compose, README with results. Deliverable: public repo.

## Success checks

The project succeeds when deletions through the service match a full retrain at lower cost. All numbers come from measured runs; none are targets set in advance.

| Check | How it's measured | Pass | Fail |
| --- | --- | --- | --- |
| No missed flips | Flip set vs full re-filter, every deletion | Identical sets | Any mismatch |
| Same training set | Curated set after deletion vs fresh curation | Identical | Any mismatch |
| Model match | Accuracy gap vs full retrain, across seeds | Within seed-to-seed variation | Outside it |
| Cost saved | Wall-clock and GPU time vs full retrain | Lower, reported per deletion | Equal or higher |
| Naive gap shown | Error of drop-only deletion vs full retrain | Measurably worse than this service | No difference |
| Reproducible | Fresh clone runs demo with one command | Works | Fails |

## Sources

- [Exact Unlearning After Data Curation (Oct 2026)](https://arxiv.org/abs/2610.33426): closest prior work; fixed filter only
- [Schelter, unlearning via incremental view maintenance (2021)](https://ssc.io/pdf/ivm-unlearning.pdf): deterministic pipelines only
- [Unlearning at Scale](https://arxiv.org/html/2508.12220v1): per-batch logging and checkpoint replay for one model
- [SISA, Machine Unlearning (IEEE S&P 2021)](https://arxiv.org/pdf/1912.03817): checkpoint-based exact unlearning
- [Do unlearning algorithms learn the right features? (Nov 2026)](https://arxiv.org/abs/2611.06681): small deletions can change what retraining learns
