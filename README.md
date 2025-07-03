# Django IncludeContents

[![PyPI version](https://badge.fury.io/py/django-includecontents.svg)](https://badge.fury.io/py/django-includecontents)
[![Python Support](https://img.shields.io/pypi/pyversions/django-includecontents.svg)](https://pypi.org/project/django-includecontents/)
[![Django Support](https://img.shields.io/pypi/djversions/django-includecontents.svg)](https://pypi.org/project/django-includecontents/)

Component-like Django template tags with HTML syntax support.

## Features

- **🧩 Component Templates**: Create reusable template components with isolated contexts
- **📝 HTML Syntax**: Use familiar HTML-like syntax for components (`<include:my-card>`)
- **🎯 Props System**: Define required and optional props with validation
- **🎨 Advanced Styling**: Conditional classes, extended classes, and CSS utilities
- **🔀 Conditional Wrapping**: Clean conditional HTML wrapper syntax with `{% wrapif %}`

## Quick Start

### Installation

```bash
pip install django-includecontents
```

### Setup

Replace your Django template backend in `settings.py`:

```python
TEMPLATES = [
    {
        'BACKEND': 'includecontents.django.DjangoTemplates',
        # ... rest of your template config
    },
]
```

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
{% wrapif user.is_authenticated then "a" href="/profile" class="user-link" %}
    Welcome, {{ user.name }}
{% endwrapif %}
```

### Dynamic Components

```html
<include:button variant="primary" {disabled} class:loading="{{ is_processing }}">
    {% if is_processing %}Processing...{% else %}Submit{% endif %}  
</include:button>
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