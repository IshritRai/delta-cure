# 0006. Choose a training schedule that lets replay save work

- **Status:** Proposed (to be decided in milestone 1 planning)
- **Date:** 2026-11-10

## Context

Under ADR 0004, every record appears in epoch 1 of standard multi-epoch training, so the first
batch changed by any deletion is in epoch 1. With `E` epochs, replay redoes at least `E − 1`
epochs plus part of epoch 1. The scope's "cost saved" check could pass only marginally, or fail,
for reasons that have nothing to do with the flip engine.

## Options

**A. Standard multi-epoch training; accept the ceiling.** Simplest and closest to common
practice. Report the ceiling honestly alongside the measured savings.

**B. Staged (sliced) training, as in SISA.** Partition records into `S` slices by hash. Stage `k`
trains on slices `1..k` for a fixed number of steps, with a checkpoint at each stage boundary. A
record in slice `k` is first used in stage `k`, so replay restarts at stage `k`. The full-retrain
reference uses the same schedule. This changes training dynamics, so model quality versus
option A must be measured.

**C. Single pass over the data.** The first change is spread evenly through training, but one
epoch may be too little training for a useful model.

## Recommendation

Option B for the service, with option A also run in milestone 2 as a baseline so the effect of
the schedule on both quality and replay cost is measured rather than assumed.

## Decision

Pending. To be settled in the milestone 1 plan and this ADR updated to Accepted.

## Consequences

Whichever option is chosen fixes the checkpoint layout, the batch log format and the replay
start-point rule for all later milestones.
