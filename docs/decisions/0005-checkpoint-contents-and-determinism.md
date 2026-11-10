# 0005. Make checkpoints complete and replay bit-exact on CPU

- **Status:** Accepted
- **Date:** 2026-11-10

## Context

Replay must produce the same model as a full retrain on the post-deletion data. If a checkpoint
is missing state, or training is nondeterministic, replay and retrain will differ for reasons
unrelated to correctness, and the "model match" check cannot distinguish bugs from noise.

## Decision

Each checkpoint stores, at minimum:

- model parameters and buffers,
- optimizer state and learning-rate scheduler state,
- global step and epoch,
- the ordering seed (ADR 0004),
- the data version and filter version it was trained against.

Checkpoints are written every `N` steps (and at stage boundaries if ADR 0006 adopts staged
training).

For exactness tests:

- Training runs on CPU with PyTorch's deterministic-algorithms mode enabled and single-process
  data loading.
- Replay and full retrain are compared parameter by parameter for **exact equality**, not within
  a tolerance.

For larger runs (GPU, multiple seeds), the scope's "within seed-to-seed variation" check
applies instead.

## Consequences

- Any difference in a small CPU run is a bug, which makes milestone 4 testable.
- Checkpoints are larger than weights-only checkpoints. The storage cost is measured and
  reported.
- The exact PyTorch APIs used for determinism are confirmed against the installed version in
  milestone 1.

## Alternatives considered

- **Tolerance-based comparison only.** Easier to pass but cannot tell a small replay bug from
  floating-point noise.
