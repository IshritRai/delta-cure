# Contributing

Thanks for helping build delta-cure. Start with the product requirements in
[`docs/prd.md`](docs/prd.md), the engineering scope in [`docs/scope.md`](docs/scope.md), the design
notes in [`docs/design.md`](docs/design.md) and the decision records in
[`docs/decisions/`](docs/decisions/README.md).

## Development setup

The project uses [uv](https://docs.astral.sh/uv/) to manage Python 3.11, the virtual environment
and the locked dependency tree in `uv.lock`.

```bash
uv sync --locked
uv run pre-commit install
```

`uv sync` creates `.venv/` and installs the project with its development tools at exactly the
versions in `uv.lock`. Prefix commands with `uv run`, or activate `.venv/` first.

## Dependencies

- Every dependency is pinned to an exact version in `pyproject.toml`
  (`uv add "package==X.Y.Z"`, or `uv add --group dev "package==X.Y.Z"` for tools), and the full
  tree, including transitive packages, is locked with hashes in `uv.lock`. Commit both files
  together.
- Add a dependency only when the code that needs it lands.
- Dependabot opens weekly update PRs for Python packages and GitHub Actions. CI audits the locked
  dependencies for known vulnerabilities on every PR.

## Workflow

- **Plan before building.** Each milestone starts with a written plan that is reviewed and
  approved before implementation begins. The approved plan goes into the milestone's issue.
- **One milestone, one branch, one pull request.** Every milestone has a GitHub issue; its PR
  references that issue (e.g. `Closes #3`). Use the pull request template.
- **`main` is protected.** All changes land through pull requests that pass CI; do not push
  directly to `main`.
- **Tests first.** Write a failing test that captures the expected behaviour, then write the code
  that makes it pass.

## Commit messages

Use [Conventional Commits](https://www.conventionalcommits.org/): `feat:`, `fix:`, `test:`,
`docs:`, `refactor:`, `chore:`, `ci:`. Keep the subject line under 72 characters and use the body
to explain why the change is needed.

Commits and PR descriptions carry the author's name only; do not add co-author trailers or
tool-generated attribution lines.

## Before every commit

All of these must pass (the pre-commit hooks run them for you):

```bash
uv run ruff check .
uv run ruff format --check .
uv run mypy
uv run pytest
```

CI runs the same checks on every pull request, plus repository hygiene hooks (whitespace, YAML
and TOML syntax, large files, private keys) and a dependency vulnerability audit. Test coverage
below the threshold in `pyproject.toml` fails the build.

## Code standards

- Type hints and docstrings (Google style) on every public function, class and module.
- Fix random seeds for anything stochastic so runs are reproducible.
- No hardcoded file paths, credentials or secrets; read them from configuration or environment
  variables.
- When using a library API you have not used before, confirm it exists in the installed version
  by checking its documentation or source.

## Results and numbers

Every result, metric or benchmark figure in the README or docs must come from a run of this
repository's code that anyone can reproduce. Do not include estimated, target or borrowed numbers.
Record how each number was produced (command, seed, commit).

## Design decisions

Record significant design decisions as short ADRs in [`docs/decisions/`](docs/decisions/), using
the template there. A changed decision gets a new ADR that supersedes the old one.

## Changelog and releases

- Every PR that changes behaviour, dependencies or docs adds a line under **Unreleased** in
  [`CHANGELOG.md`](CHANGELOG.md).
- Versions follow [Semantic Versioning](https://semver.org/). Each completed milestone is a minor
  release: milestone N → `0.N.0`.
- To release: move the Unreleased entries under a new version heading with the date, bump
  `version` in `pyproject.toml`, merge, then tag the merge commit `v0.N.0` and create a GitHub
  release from the tag.

## Security

Report vulnerabilities privately as described in [`SECURITY.md`](SECURITY.md), not in public
issues.
