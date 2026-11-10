# Security policy

## Supported versions

The project is pre-1.0. Only the latest commit on `main` receives fixes.

## Reporting a vulnerability

Please do not open a public issue for a security problem.

Use GitHub's private vulnerability reporting: the **Security** tab → **Report a
vulnerability**. If that option is not available, contact the maintainer directly through
GitHub.

Include what you found, how to reproduce it, and the commit you tested. You can expect an
acknowledgement, an assessment, and a note in `CHANGELOG.md` when a fix is released.

## Scope notes

This service deletes data and models. Reports about incomplete erasure (a deleted record or a
model trained on it surviving in any store) are treated as security issues.

The HTTP API has no authentication in the local demo and must not be exposed beyond localhost
without an authentication layer (see open question Q3 in `docs/prd.md`).
