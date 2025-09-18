# Showcase Overview

The Showcase app is a developer-facing component catalog for projects that use `django-includecontents`. It automatically lists every component template, renders live previews, and surfaces accompanying documentation so teams can explore and validate UI pieces without leaving the browser.

## Key Features

- Automatic component discovery across all configured template directories
- Side-by-side live preview and prop editor for rapid iteration
- Generated code snippets showing both `{% includecontents %}` and HTML tag syntax
- Optional metadata sidecars (`button.yaml` next to `button.html`) for best practices, accessibility notes, and ready-made examples
- Design token library with visual previews and copy-to-clipboard functionality

## Installation

1. Enable the apps:
   ```python
   INSTALLED_APPS = [
       # ...
       "includecontents",
       "showcase",
   ]
   ```
2. Mount the routes:
   ```python
   from django.urls import include, path

   urlpatterns = [
       # ...
       path("showcase/", include("showcase.urls")),
   ]
   ```
3. Run the development server and open `http://localhost:8000/showcase/`.

## Where to Go Next

- [Learn how components are discovered](component-discovery.md)
- [Document components with metadata](metadata.md)
- [Use the live preview tooling](live-preview.md)
- [Configure iframe preview with your CSS](iframe-preview.md)
- [Work with design tokens](design-tokens.md)
- [Customise the experience for your team](customisation.md)
- Lock it down for non-prod environments with `SHOWCASE_DEBUG_ONLY` or gate access via `SHOWCASE_REQUIRE_LOGIN` (see [Customisation Tips](customisation.md#keep-security-in-mind)).
