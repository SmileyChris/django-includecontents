# Change Log

This long shows interesting changes that happen for each release of `django-includecontents`.

<!-- towncrier release notes start -->

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