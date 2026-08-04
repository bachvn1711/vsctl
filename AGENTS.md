# Repository Guidelines

## Project Structure & Module Organization

This is a Python CLI project using a `src/` layout. Application code is under
`src/vssctl/`: command handlers live in `commands/`, domain and build logic in
`core/`, and the interactive terminal UI in `tui/`. Tests are in `tests/` and
use matching `test_*.py` modules. VSS templates, releases, units, and example
specifications are stored under `workspace/templates/`. Packaging metadata is
defined in `pyproject.toml`; CI automation is in `.github/workflows/`.

## Build, Test, and Development Commands

Create an environment and install the package in editable mode:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e .
```

Run the full test suite with `pytest tests/`. Useful application checks include
`vssctl doctor`, `vssctl validate`, and `vssctl generate --version 6.0`.
`vssctl pipeline` runs the validation, generation, and container workflow; use
`--engine docker` or `--engine podman` when autodetection is unsuitable.

## Coding Style & Naming Conventions

Use Python 3.10+ and four-space indentation. Keep modules, functions, and
variables in `snake_case`; use `PascalCase` for classes and `UPPER_SNAKE_CASE`
for constants. Prefer small, typed functions and reuse models and exceptions
from `src/vssctl/core/`. No formatter or linter is configured, so keep changes
PEP 8-compatible and avoid unrelated formatting churn.

## Testing Guidelines

Tests use pytest. Name files `test_<area>.py` and test functions
`test_<behavior>`. Add or update focused tests for changes to catalog parsing,
validation, generation, publishing, or TUI behavior, then run `pytest tests/`
before submitting. Commands that write generated workspace output should be
tested without committing transient artifacts.

## Commit & Pull Request Guidelines

Recent commits use short, imperative, lowercase summaries, sometimes with a
scope or milestone (for example, `feat: ...`, `fix: ...`, or `milestone 11: ...`).
Keep commits focused. Pull requests should explain the behavior changed, list
validation and test commands run, identify configuration or generated-output
impact, and include screenshots for visible TUI changes. Never commit secrets,
tokens, virtual environments, or generated local output.

## Configuration & Security

Use `.vssctl.yaml` for local paths and defaults. Treat GHCR tokens and other
credentials as secrets; pass them through environment variables or protected CI
secrets rather than source files or command history.
