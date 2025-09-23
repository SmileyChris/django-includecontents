# Django IncludeContents
[![PyPI version](https://img.shields.io/pypi/v/django-includecontents)](https://pypi.org/project/django-includecontents/)
[![Django Support](https://img.shields.io/pypi/djversions/django-includecontents.svg)](https://pypi.org/project/django-includecontents/)

Component-like Django template tags with HTML syntax support. **Full feature parity** between Django templates and Jinja2.

## Features

- **🧩 Component Templates**: Create reusable template components with isolated contexts
- **📝 HTML Syntax**: Use familiar HTML-like syntax for components (`<include:my-card>`)
- **🎯 Props System**: Define required and optional props with validation
- **🎨 Advanced Styling**: Conditional classes, extended classes, and CSS utilities
- **🔀 Conditional Wrapping**: Clean conditional HTML wrapper syntax with `{% wrapif %}`
- **🎭 Icon System**: SVG sprite generation from Iconify icons and local SVG files (`<icon:home>`)

## Quick Start

### Installation

```bash
pip install django-includecontents
```

### Setup

Choose your template engine:

=== "Django Templates"

    Replace your Django template backend in `settings.py`:

    ```python
    TEMPLATES = [
        {
            'BACKEND': 'includecontents.django.DjangoTemplates',
            # ... rest of your template config
        },
    ]
    ```

=== "Jinja2"

    Add the Jinja2 extension in `settings.py`:

    ```python
    TEMPLATES = [
        {
            'BACKEND': 'django.template.backends.jinja2.Jinja2',
            'OPTIONS': {
                'extensions': [
                    'includecontents.jinja2.IncludeContentsExtension',
                ],
            },
        },
    ]
    ```

    See [Jinja2 Setup](https://smileychris.github.io/django-includecontents/getting-started/jinja2-setup/) for complete instructions.

### Create a Component

**templates/components/welcome-card.html**
```html
{# props title, subtitle="" #}
<div class="card">
    <h2>{{ title }}</h2>
    {% if subtitle %}<p>{{ subtitle }}</p>{% endif %}
    <div class="content">{{ contents }}</div>
</div>
```

### Use the Component

```html
<include:welcome-card title="Hello World" subtitle="Getting started">
    <p>Your component content goes here!</p>
</include:welcome-card>
```

### Result

```html
<div class="card">
    <h2>Hello World</h2>
    <p>Getting started</p>
    <div class="content">
        <p>Your component content goes here!</p>
    </div>
</div>
```

## Template Tag Syntax

If you prefer traditional Django template syntax:

```django
{% load includecontents %}
{% includecontents "components/welcome-card.html" title="Hello World" subtitle="Getting started" %}
    <p>Your component content goes here!</p>
{% endincludecontents %}
```

## Documentation

📚 **[Full Documentation](https://smileychris.github.io/django-includecontents/)**

- **[Getting Started](https://smileychris.github.io/django-includecontents/getting-started/installation/)** - Installation and setup
- **[Jinja2 Setup](https://smileychris.github.io/django-includecontents/getting-started/jinja2-setup/)** - Jinja2 template engine setup
- **[Quick Start Guide](https://smileychris.github.io/django-includecontents/getting-started/quickstart/)** - Get started in 5 minutes
- **[HTML Components](https://smileychris.github.io/django-includecontents/using-components/html-syntax/)** - Modern component syntax
- **[Best Practices](https://smileychris.github.io/django-includecontents/building-components/best-practices/)** - Building great components

## Examples

### Named Content Blocks

```html
<include:article title="My Article">
    <content:header>
        <h1>Article Title</h1>
        <p>By {{ author }}</p>
    </content:header>
    
    <p>Main article content...</p>
    
    <content:sidebar>
        <h3>Related Links</h3>
    </content:sidebar>
</include:article>
```

### Conditional Wrapping

```django
{% load includecontents %}
{% wrapif user.is_authenticated %}
    <a href="/profile" class="user-link">
        {% contents %}Welcome, {{ user.name }}{% endcontents %}
    </a>
{% endwrapif %}
```

### Modern JavaScript Framework Integration

```html
<!-- Vue.js and Alpine.js attributes work seamlessly -->
<include:button @click="handleClick()" :disabled="isLoading">
    Submit
</include:button>

<include:modal x-on:click="open = false" x-show="open">
    Modal content
</include:modal>

<!-- Nested attributes for complex components -->
<include:form inner.class="form-control" button.@click="submit()">
    Form content
</include:form>
```

### Dynamic Components

```html
<include:button variant="primary" {disabled} class:loading="{{ is_processing }}">
    {% if is_processing %}Processing...{% else %}Submit{% endif %}
</include:button>
```

### Icons

```python
# settings.py
STATICFILES_FINDERS = [
    'includecontents.icons.finders.IconSpriteFinder',  # Must be first for icons
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
]

INCLUDECONTENTS_ICONS = {
    'icons': [
        'mdi:home',        # Use as <icon:home>
        'tabler:user',     # Use as <icon:user>
        'icons/logo.svg'   # Use as <icon:logo>
    ]
}
```

> **Note:** Icon names auto-generate from config: `'mdi:home'` → `<icon:home>`, `'icons/logo.svg'` → `<icon:logo>`

```html
<icon:home class="w-6 h-6" />
<icon:user class="avatar" use.role="img" />
<icon:logo class="brand" />
```

## Requirements

- **Python**: 3.8+
- **Django**: 3.2+

## License

MIT License. See [LICENSE](LICENSE) for details.

## Contributing

Contributions welcome! Please see our [GitHub Issues](https://github.com/SmileyChris/django-includecontents/issues) for bug reports and feature requests.

## Support

- 📖 [Documentation](https://smileychris.github.io/django-includecontents/)
- 🐛 [Issue Tracker](https://github.com/SmileyChris/django-includecontents/issues)
- 💬 [Discussions](https://github.com/SmileyChris/django-includecontents/discussions)