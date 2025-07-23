# Change Log

This log shows interesting changes that happen for each release of `django-includecontents`.

<!-- towncrier release notes start -->

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