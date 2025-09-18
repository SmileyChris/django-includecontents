# Repository Guidelines

## Project Structure & Module Organization
Core package code lives in `includecontents/`, with Django engine helpers under `includecontents/django/` and template tags in `includecontents/templatetags/`. Icon tooling and storage live in `includecontents/icons/`. Tests are organized by feature in `tests/` with supporting templates in `tests/templates/`. Towncrier changelog fragments belong in `changes/`, while user-facing docs are in `docs/` and the demo app sits in `example_project/` for manual testing.

## Build, Test, and Development Commands
Install editable dependencies with extras that you need: `uv run pip install -e ".[test]"` for test tooling, or `".[docs]"` for documentation work. Run the suite with `uv run pytest` and target a file via `uv run pytest tests/test_tag.py::test_basic -v`. Publish artifacts using `uv run pdm build`. Serve docs locally with `uv run mkdocs serve` and build static docs through `uv run mkdocs build`.

## Coding Style & Naming Conventions
Use 4-space indentation and follow idiomatic Python/Django patterns seen in existing modules. Prefer descriptive function names like `render_component` and align template helpers with their HTML tag names. Keep docstrings and inline comments focused on behavior, not mechanics. Format HTML and Jinja templates by running `npm install` once, then `npx prettier --write "**/{templates,jinja2}/**/*.html"` to match the repo style.

## Testing Guidelines
Pytest with pytest-django drives the suite; place new tests in an appropriate `tests/test_*.py` module near related coverage. Name tests after the scenario under validation (`test_multiline_component_closes_blocks`). Use the `integration` marker sparingly and exclude it locally with `uv run pytest -m "not integration"` when you need speed. Add fixtures or helper templates inside `tests/fixtures/` or `tests/templates/` to keep state isolated.

## Commit & Pull Request Guidelines
Commit messages follow a Conventional Commit style (`fix:`, `docs:`, `chore:`) before a short imperative summary. Reference GitHub issues when applicable and note behavioral changes in the body. Pull requests should describe the motivation, outline the approach, and list any manual testing. Attach screenshots or template snippets when UI rendering changes, and confirm `uv run pytest` passes before requesting review.

## Changelog & Release Notes
Do not edit `CHANGES.md` directly; instead add a fragment under `changes/` such as `changes/+lazy-context.feature.md` or `changes/123.bugfix.md`. Keep each fragment to a single bullet-worthy sentence. Draft the compiled changelog with `uv run towncrier --draft` to verify wording. Remove stale fragments after they are consumed in a release.
