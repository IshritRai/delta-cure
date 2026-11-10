# 0001. Record architecture decisions

- **Status:** Accepted
- **Date:** 2026-11-10

## Context

The scope (`docs/scope.md`) defines what to build but leaves several design questions open, and
some of them determine whether the success checks can be met at all. Decisions made in chat or
in PR comments are hard to find later.

## Decision

Significant design decisions are recorded as Architecture Decision Records in `docs/decisions/`,
one file per decision, numbered sequentially, using `template.md`.

- A decision is **Proposed** while under discussion and **Accepted** once the PR containing it is
  merged.
- Accepted ADRs are not edited for substance. A changed decision gets a new ADR that supersedes
  the old one, and the old one's status is updated to point at it.
- `docs/scope.md` and `docs/design.md` link to the ADRs that shape them.

## Consequences

Every non-obvious choice has a written rationale that can be reviewed in a PR. Writing an ADR
costs a little time per decision.

## Alternatives considered

- **Decisions in `docs/design.md` only.** Mixes current state with history; the reasoning behind
  a change gets lost when the design is rewritten.
- **Decisions in GitHub issues.** Not versioned with the code and not available offline.
