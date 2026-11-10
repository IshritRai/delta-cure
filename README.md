# Curator-Aware Unlearning (delta-cure)

[![CI](https://github.com/IshritRai/delta-cure/actions/workflows/ci.yml/badge.svg)](https://github.com/IshritRai/delta-cure/actions/workflows/ci.yml)

A deletion service for ML training pipelines. Many pipelines use a **learned filter** (a quality
classifier) to decide which records reach the model. When a record is deleted, today's tools
remove it from the model's training set and stop there. But if the record was in the filter's
labelled training slice, it also trained the filter. Without it, the filter's keep/drop decisions can flip: some kept records should now
drop, and some rejected records should now get in. This service finds those flips and updates
the model to match a from-scratch retrain, at lower cost, without retraining from scratch.

## Architecture

![System architecture: training path, deletion path and stored state](docs/architecture.png)

Each deletion step updates the training step above it. The highlighted step is the new part:
only records near the filter's boundary are re-scored, and "near" is a certified band computed
from how far the filter's weights moved, so no flip can be missed. Training data is ordered by a
per-record hash so a deletion changes as few batches as possible, and a lineage store records
which checkpoint first used each record, so replay starts as late as possible. Every deletion
ends by purging superseded checkpoints and other derived artifacts.

## Documentation

| Document | Contents |
| --- | --- |
| [`docs/prd.md`](docs/prd.md) | Product requirements: users, requirements, success metrics, risks |
| [`docs/scope.md`](docs/scope.md) | Engineering scope, milestones and success checks |
| [`docs/design.md`](docs/design.md) | Data flow, stored state and deletion steps |
| [`docs/decisions/`](docs/decisions/README.md) | Architecture decision records |

## Components and stack

| Layer | Scope | Tools |
| --- | --- | --- |
| Data versioning | Raw records with stable IDs; a dataset version per deletion as a manifest of record IDs, with physical deletion of erased records | Hugging Face `datasets`; DVC under review |
| Learned filter | Quality classifier trained on a labelled slice; data-independent features; fixed score threshold; stores each record's score and feature norm | scikit-learn `LogisticRegression` |
| Training | Small text classifier; hash-based record order; checkpoints every N steps with optimizer and scheduler state; per-batch log of record IDs, seed and step | PyTorch, MLflow |
| Lineage store | Record → filter → selected set → checkpoint links; labelled-slice membership; deletion tombstones | SQLite |
| Deletion engine | Classify the deletion, retrain filter, re-score the certified band, compute flips, replay from nearest checkpoint, purge superseded artifacts | Python package |
| API | `POST /delete/{record_id}`, `GET /status/{job_id}`, `GET /lineage/{record_id}`; batched deletion jobs | FastAPI |
| Verification | Compares output with a full re-filter + retrain on small runs | pytest, GitHub Actions |
| Packaging | One-command demo and README with measured results | Docker Compose |

## Milestones

- [ ] **1. Baseline pipeline** — dataset with stable IDs, filter with data-independent features, training loop with hash-based ordering, complete checkpoints and batch log, MLflow tracking. One command trains end to end.
- [ ] **2. Reference path** — naive deletion (drop the record only) and full re-filter + retrain; their gap is measured.
- [ ] **3. Flip engine** — retrain filter, re-score records within the certified band, compute dropped and admitted sets; tests show no missed flips against full re-filtering, including adversarial deletions.
- [ ] **4. Replay engine** — resume from the earliest checkpoint whose batches change, using the batch log; bit-identical to a full retrain on small CPU runs.
- [ ] **5. Service** — FastAPI endpoints, lineage store, batched deletion jobs, job status, artifact purge; deletion works through the API.
- [ ] **6. Benchmark and polish** — random and adversarial deletion sequences, single and batched, per deletion case; cost comparison, Docker Compose, README with results.

## Setup

Requires Python 3.11.

```bash
git clone https://github.com/IshritRai/delta-cure.git
cd delta-cure
python3.11 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
pre-commit install
```

## Run

The pipeline, deletion engine and API are not implemented yet; run commands will be added as
each milestone lands. To run the checks:

```bash
ruff check . && ruff format --check .
mypy
pytest
```

## Results

Results: to be added from our own runs.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md).

## License

[MIT](LICENSE)
