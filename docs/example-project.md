# Example Project Guide

The `example_project/` directory contains a minimal Django site that demonstrates the showcase app, includecontents engine, and default settings. Use it as a sandbox when building or testing components without wiring them into a full product.

## Project Layout

- `manage.py` – entry point for admin and runserver commands.
- `settings.py` – enables the includecontents template engine, registers `showcase`, and configures SQLite plus static files.
- `templates/` – houses sample components and the base layout rendered by the showcase.
- `urls.py` – routes the showcase at `/showcase/` alongside the default admin.

## Running Locally

1. Install dependencies with extras: `uv run pip install -e ".[test]"` ensures Django and tooling are available.
2. Apply migrations and start the server:
   ```bash
   uv run python example_project/manage.py migrate
   uv run python example_project/manage.py runserver
   ```
3. Visit `http://127.0.0.1:8000/showcase/` to explore the bundled components.

Because the settings file keeps `DEBUG = True`, the project reloads on template changes and serves static files directly from `example_project/static/`.

## Included Components

The sandbox ships with a small component library so the showcase has something to display immediately:

- `forms/button.html` – CTA button with variant, size, optional icon, and anchor support.
- `feedback/alert.html` – Status banner that handles icons, dismiss buttons, and rich content.
- `layout/feature-card.html` – Flexible callout card with a `footer` content block for custom actions.
- `marketing/hero.html` – Landing hero with eyebrow text, CTA buttons, and an `actions` slot.

Each template sits beside a matching YAML file (for example `button.yaml`) providing metadata, examples, and prop descriptions consumed by the showcase.

## Extending the Sandbox

Drop new components into `templates/components/` and they will appear automatically in the showcase. If you need custom data for previews, place a matching `*.yaml` or `*.toml` file next to the template—`button.html` pairs with `button.yaml`—and the registry will pick it up. Icons are pre-configured through `INCLUDECONTENTS_ICONS`, so you can experiment with sprite generation by populating that dictionary while the dev server is running.

Keep the example project focused on illustrative patterns—avoid adding business logic or production secrets. When a component graduates to your main application, copy the template and its metadata, leaving the sandbox ready for the next experiment.
