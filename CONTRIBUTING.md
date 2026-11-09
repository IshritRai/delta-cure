# Contributing

Thanks for helping build delta-cure. The project spec lives in [`docs/scope.md`](docs/scope.md)
and the design notes in [`docs/design.md`](docs/design.md).

## Development setup

```bash
python3.11 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
pre-commit install
```

## Workflow

- **Plan before building.** Each milestone starts with a written plan that is reviewed and
  approved before implementation begins.
- **One milestone, one branch, one pull request.** Every milestone has a GitHub issue; its PR
  references that issue (e.g. `Closes #3`).
- **`main` is protected.** All changes land through pull requests; do not push directly to `main`.
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
ruff check .
ruff format --check .
mypy
pytest
```

CI runs the same checks on every pull request.

## Code standards

- Type hints and docstrings (Google style) on every public function, class and module.
- Fix random seeds for anything stochastic so runs are reproducible.
- No hardcoded file paths, credentials or secrets; read them from configuration or environment
  variables.
- Pin every dependency to an exact version in `pyproject.toml`, and add a dependency only when the
  code that needs it lands.
- When using a library API you have not used before, confirm it exists in the installed version
  by checking its documentation or source.

## Results and numbers

Every result, metric or benchmark figure in the README or docs must come from a run of this
repository's code that anyone can reproduce. Do not include estimated, target or borrowed numbers.
Record how each number was produced (command, seed, commit).

## Design decisions

Record significant design decisions as short ADRs in [`docs/decisions/`](docs/decisions/).
