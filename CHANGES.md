# Change Log

This log shows interesting changes that happen for each release of `django-includecontents`.

<!-- towncrier release notes start -->

# Version 3.1.1 (2025-08-06)

### Features

- Improved icon error reporting to show all missing or invalid icons at once, making it easier for developers to fix configuration issues in a single pass

### Bugfixes

- Fixed compatibility issue with Django 5.2 where invalid icons could cause a TypeError in static file serving instead of returning a proper 404 error


# Version 3.1 (2025-08-06)

### Features

- Add file-based caching system for Iconify API responses to improve performance and enable offline development. Icons fetched from the Iconify API can now be cached locally and reused in subsequent builds, configured via `api_cache_root` and `api_cache_static_path` settings.
- Icon sprites now preserve `style` attributes containing CSS variables (e.g., `style="fill: var(--icon-color)"`), enabling advanced theming and interactive hover effects that work across the shadow DOM boundary. See the new [Styling with CSS Variables](https://django-includecontents.readthedocs.io/en/latest/icons/styling-with-css-variables/) documentation for examples.


# Version 3.0.1 (2025-08-06)

### Features

- Icon sprite build failures now fail loudly with clear error messages instead of silently returning empty SVGs. This makes configuration errors, missing files, and API failures immediately visible during development and deployment.

### Bugfixes

- Fixed icon symbol IDs to use component names (e.g., "home") instead of full identifiers (e.g., "mdi-home"). Icons are now consistently referenced by their component names in both templates and generated sprites.

### Deprecations and Removals

- Removed all storage backend classes and configuration. The icon system now uses only in-memory caching with Django's static files system for production serving. This is a breaking change - remove `storage` and `storage_options` from your `INCLUDECONTENTS_ICONS` settings.

### Misc

- Simplified icon system architecture by removing 1,360+ lines of code. Sprites are now cached in memory during development and served from STATIC_ROOT in production via standard Django static files, eliminating the need for complex storage configuration.


# Version 3.0 (2025-08-06)

### Features

- Add icon system with automatic SVG sprite generation. Features `{% icon %}` template tag and `<icon:name>` HTML syntax support.


# Version 2.5.2 (2025-08-04)

### Bugfixes

- Fix context processor variables not being available in nested HTML components


# Version 2.5.1 (2025-08-01)

### Bugfixes

- Fix JavaScript event modifiers like @click.stop not being passed to child components


# Version 2.5 (2025-07-25)

### Features

- Add `...attrs` spread syntax to forward undefined attributes from parent to child components


# Version 2.4.1 (2025-07-24)

### Bugfixes

- Fix object passing in component attributes to preserve actual objects instead of string representations when using pure variable syntax like `deck="{{ deck }}"`.


# Version 2.4 (2025-07-24)

### Features

- Add support for JavaScript framework event attributes like `@click`, `v-on:`, `x-on:`, and `:` (binding shorthand) in component attributes
- Add support for mixed content in component attributes, allowing combinations of static text and Django template syntax (e.g., `class="btn {{ variant }}"`, `href="/products/{{ id }}/"`, and even template tags like `class="{% if active %}active{% endif %}"`).


# Version 2.3 (2025-07-23)

### Features

- HTML-based components now have access to all context variables provided by context processors, not just the request object and CSRF token

  This ensures consistent behavior between HTML components and regular Django templates.


# Version 2.2 (2025-07-22)

### Features

- Support multiple space-separated values in enum props (e.g., `variant="primary icon"`) to enable combining visual modifiers.

### Bugfixes

- Fix parsing of multiline closing tags (e.g., `</include:item\n>`) in HTML component syntax.


# Version 2.1.1 (2025-07-02)

### Bugfixes

- Fixed self-closing component tags within nested components incorrectly incrementing the nesting level, causing "Unclosed tag" errors.


# Version 2.1 (2025-07-02)

### Features

- Add Django template tag support in component attributes. Component attributes now fully support Django template syntax including `{% url %}`, `{{ variables }}`, `{% if %}` conditionals, and all other template tags.

  ```html
  <include:ui-button 
    variant="primary" 
    href="{% url 'settings' %}" 
    class="btn {% if large %}btn-lg{% endif %}"
  >
    Save Settings
  </include:ui-button>
  ```

### Bugfixes

- Fix duplicate content block names error when nesting components with same named content blocks


# Version 2.0 (2025-07-01)

### Features

- Add HTML-style `<content:name>` syntax for named content blocks in components. This provides a more HTML-consistent alternative to `{% contents %}` tags while maintaining full backwards compatibility.
- Add class prepend syntax for component attrs.

  Classes can now be prepended with `{% attrs class="card &" %}` syntax.

  - Append `" &"` to prepend component classes before user-provided classes
  - Complements existing `"& "` syntax which appends after user classes
  - Useful when CSS specificity or utility class ordering matters
- Add enum validation for component props.

  Props can now be defined with allowed values: `{# props variant=primary,secondary,accent #}`

  - Validates prop values against the allowed list
  - Sets both the prop value and a camelCased boolean (e.g., `variant="primary"` and `variantPrimary=True`)
  - Optional enums start with empty: `size=,small,medium,large`
  - Hyphens are camelCased: `dark-mode` → `variantDarkMode`
- Add {% wrapif %} template tag for conditional wrapping.

  The new `{% wrapif %}` tag provides a clean way to conditionally wrap content with HTML elements:

  - **Shorthand syntax**: `{% wrapif condition then "tag" attr=value %}content{% endwrapif %}`
  - **Full template syntax**: Supports `{% contents %}` blocks for complex wrappers
  - **Multiple conditions**: `{% wrapelif %}` and `{% wrapelse %}` for if/elif/else patterns
  - **Complex conditions**: Inherits all Django template operators (and, or, not, comparisons, in)
  - **Multiple named contents**: Support for multiple content blocks in full syntax
  - **Attribute handling**: Proper escaping and boolean attribute support

  This reduces template boilerplate and improves readability when conditionally wrapping content.
- Added `|not` template filter for negating boolean values in conditional class attributes


# Version 1.2.1 (2024-11-19)

### Bugfixes

- Make csrf_token work from within components


# Version 1.2 (2024-11-12)

### Features

- Added support for Django-style template variables in component attributes: `title="{{ myTitle }}"`. The old style `title={myTitle}` is still supported but will be deprecated in a future version.

### Bugfixes

- Short-hand syntax props weren't being taken into account by the required attrs check.


# Version 1.1.1 (2024-07-25)

### Bugfixes

- Fix a bug where the component context wasn't being set correctly, especially noticeable inside of a loop. ([5])

[5]: https://github.com/SmileyChris/django-includecontents/issues/5


# Version 1.1 (2024-06-03)

### Bugfixes

- Allow attributes with dashes which don't have values. For example, `<include:foo x-data />`. ([1])

[1]: https://github.com/SmileyChris/django-includecontents/issues/1


# Version 1.0 (2024-05-16)

### Features

- Update the template engine location so that it will be picked up as the standard Django engine when replaced.

### Improved Documentation

- Fix some grammar.
- Add a note about how to workaround Prettier stripping AlpineJS' `x-data` quotes.

### Deprecations and Removals

- Since the template engine location has changed, any users of pre 1.0 versions will need to update their Django settings to point to the new location:
  
  ```python
  TEMPLATES = [
      {
          "BACKEND": "includecontents.django.DjangoTemplates",
          ...
      },
  ]
  ```

# Version 0.8 (2024-05-09)

### Features

- Add shorthand attribute syntax (`<include:foo {title}>`).

### Bugfixes

- Fix component context isolation.

# Version 0.7 (2024-05-01)

### Features

- Allow self-closing tags. For example, `<include:foo />`.
- Handle &gt; inside `<include:` tags.
- Allow kebab-case attributes. For example, `<include:foo x-data="bar" />`.

### Improved Documentation

- Add a note about `pretier-plugin-jinja-template`.
- Readme improvements.