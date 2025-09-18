# Customisation Tips

Tune the showcase to match your workflow by curating component categories, adding realistic data, and tailoring the frontend experience.

## Organise Components

Group related templates into subdirectories (for example `layout/cards/`) so they appear under intentional categories. Override the category in metadata when you want a component to live elsewhere without moving the file.

## Seed Rich Examples

Populate the `examples` section in metadata with multiple states—loading, success, error—to give reviewers a quick sense of variability. Include both prop overrides and descriptive copy so teammates know when to use each variant.

## Style and Layout Overrides

The showcase UI is served from `showcase/templates/showcase/` and `showcase/static/showcase/`. Copy these assets into your project and adjust Django’s template loader order if you need to rebrand the catalog or add project-specific guidance in the sidebar.

## Integrate with Tooling

Pair the showcase with the example project or your main site. Running `uv run python example_project/manage.py runserver` provides a dedicated sandbox, while mounting the URLs inside your product makes it easier for designers and QA to sanity check components alongside real data.

## Keep Security in Mind

The preview endpoint accepts arbitrary content, so keep it accessible only to trusted users in production environments. Leave CSRF enabled, and consider wrapping the showcase routes behind authentication if you deploy them outside local development.

### Restrict access through settings

- `SHOWCASE_DEBUG_ONLY = True` hides all showcase views unless `DEBUG` is enabled.
- `SHOWCASE_REQUIRE_LOGIN = True` forces users to authenticate before reaching the catalog or preview endpoint.

Define either value in your Django settings module to match your rollout policy.
