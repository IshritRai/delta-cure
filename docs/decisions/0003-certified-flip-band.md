# 0003. Re-score only records inside a certified flip band

- **Status:** Accepted
- **Date:** 2026-11-10

## Context

The scope says only records "within a margin band" near the filter's boundary are re-scored. A
fixed-width band is not sound: retraining the filter changes its weights, which shifts every
record's score, and a record far from the boundary can still flip if the weights move enough.
Tests on sample data can fail to find a missed flip without proving none exist.

Also, for a linear filter on precomputed features, scoring every record is a single
matrix-vector product, which is cheap compared with retraining the filter or replaying training.
The value of the band is therefore mainly a **correctness guarantee**, and a saving only when
scoring is expensive.

## Decision

The filter is a linear model with score `s(x) = w·x + b` and a **fixed** decision threshold `τ`:
a record is kept when `s(x) ≥ τ`.

After the filter is retrained without the deleted record(s) (case C, ADR 0002), the new weights
`w'` and bias `b'` are known exactly. With `Δw = w' − w` and `Δb = b' − b`, each record's score
changes by `Δw·x + Δb`, and by the Cauchy-Schwarz inequality

    |s'(x) − s(x)| ≤ ‖Δw‖₂ · ‖x‖₂ + |Δb|

So a record **cannot** change side of the threshold when

    |s(x) − τ| > ‖Δw‖₂ · ‖x‖₂ + |Δb| + ε

where `ε` is a small slack for floating-point error. Every record that fails this test is in the
**certified band** and is re-scored exactly with `w'`, `b'`. Flips are the band records whose
keep/drop decision changed: the **dropped** set (kept → dropped) and the **admitted** set
(dropped → kept).

To store what this needs, the filter step saves, per record, its score `s(x)` and its feature
norm `‖x‖₂`.

Constraints this places on milestone 1:

1. **Features must not depend on the training data.** If a feature transform (for example a
   vocabulary, IDF weights or a scaler) is fitted on data that includes a deleted record, every
   record's features change and the bound no longer holds. Use a data-independent transform
   (for example feature hashing) or one fitted on a fixed reference set that is never subject
   to deletion.
2. **The threshold is an absolute score, not a quantile.** "Keep the top k %" moves the threshold
   whenever any score moves, which needs a different bound. Quantile selection is out of scope
   unless a later ADR adds it.

## Consequences

- "No missed flips" holds by construction, not only by test. Milestone 3 still tests it against
  full re-scoring, including adversarial deletions chosen to move the weights as much as possible.
- The README describes the contribution as an exact, certified flip computation, not as a large
  compute saving on the filter step.
- The band's size (how many records needed re-scoring) is reported per deletion as a measured
  result.

## Alternatives considered

- **Fixed margin band.** Simple, but can miss flips, which fails the scope's first success check.
- **Influence-function estimate of `Δw` before retraining.** Avoids the retrain but is an
  approximation for finite steps; the exact retrain is cheap for a linear model on a labelled
  slice, so the estimate buys little.
- **Re-score everything.** Also exact and cheap here. Kept as the reference implementation that
  milestone 3 tests against.
