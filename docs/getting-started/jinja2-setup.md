# Jinja2 Setup

Django IncludeContents provides full support for Jinja2 templates through a custom extension. This allows you to use components, HTML syntax, and all major features with Jinja2.

!!! info "Feature Compatibility"
    Jinja2 support includes:

    - ✅ **Component system**: Full `{% includecontents %}` tag support
    - ✅ **HTML component syntax**: `<include:component>` via preprocessing
    - ✅ **Props and validation**: Required prop validation and defaults
    - ✅ **Enum prop validation**: Full validation with helpful error messages
    - ✅ **Named content blocks**: `{% contents %}` and `<content:name>`
    - ✅ **Attrs system**: Undefined attribute handling
    - ✅ **Context isolation**: Components render in isolated contexts
    - ✅ **Icon system**: Full support including HTML syntax `<icon:name>`
    - ❌ **WrapIf tag**: Not available (use Jinja2 conditionals instead)

## Installation

### 1. Install Django IncludeContents

```bash
pip install django-includecontents
```

### 2. Configure Jinja2 Backend

Add the Jinja2 backend to your `TEMPLATES` setting in `settings.py`:

```python
# settings.py
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.jinja2.Jinja2',
        'DIRS': [
            BASE_DIR / 'jinja2',  # Your Jinja2 templates directory
        ],
        'APP_DIRS': True,
        'OPTIONS': {
            'environment': 'myproject.jinja2.environment',
            'extensions': [
                'includecontents.jinja2.IncludeContentsExtension',
            ],
        },
    },
    # You can also keep Django templates alongside Jinja2
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            BASE_DIR / 'templates',
        ],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]
```

### 3. Create Jinja2 Environment

Create a Jinja2 environment configuration file:

**myproject/jinja2.py**
```python
from django.contrib.staticfiles.storage import staticfiles_storage
from django.urls import reverse
from jinja2 import Environment


def environment(**options):
    env = Environment(**options)
    env.globals.update({
        'static': staticfiles_storage.url,
        'url': reverse,
    })
    return env
```

This gives your Jinja2 templates access to Django's `static()` and `url()` functions.

### 4. Add to Installed Apps

Make sure `includecontents` is in your `INSTALLED_APPS`:

```python
# settings.py
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'includecontents',  # Add this
    'myapp',
]
```

## Directory Structure

Organize your templates with separate directories for Django and Jinja2:

```
myproject/
├── templates/          # Django templates
│   └── components/
│       └── card.html
├── jinja2/            # Jinja2 templates
│   ├── components/
│   │   └── card.html
│   ├── base.html
│   └── index.html
└── myproject/
    └── jinja2.py      # Environment config
```

## Basic Usage

### Template Tag Syntax

Use the `{% includecontents %}` tag in Jinja2 templates:

**jinja2/components/card.html**
```html
{# props title, subtitle="" #}
<div class="card">
    <h2>{{ title }}</h2>
    {% if subtitle %}
        <p class="subtitle">{{ subtitle }}</p>
    {% endif %}
    <div class="content">
        {{ contents }}
    </div>
</div>
```

**jinja2/index.html**
```html
<!DOCTYPE html>
<html>
<head>
    <title>My Site</title>
</head>
<body>
    {% includecontents "components/card.html" title="Welcome" subtitle="Getting started" %}
        <p>This is your first Jinja2 component!</p>
    {% endincludecontents %}
</body>
</html>
```

### HTML Component Syntax

The extension automatically preprocesses HTML component syntax:

**jinja2/index.html**
```html
<!DOCTYPE html>
<html>
<head>
    <title>My Site</title>
</head>
<body>
    <include:card title="Welcome" subtitle="Getting started">
        <p>This is your first Jinja2 component with HTML syntax!</p>
    </include:card>
</body>
</html>
```

## Named Content Blocks

Support for named content blocks works identically to Django:

**jinja2/components/layout.html**
```html
<div class="layout">
    <header>
        {{ contents.header }}
    </header>
    <main>
        {{ contents }}
    </main>
    {% if contents.footer %}
        <footer>
            {{ contents.footer }}
        </footer>
    {% endif %}
</div>
```

**Usage:**
```html
<include:layout>
    <content:header>
        <h1>Page Title</h1>
    </content:header>

    <p>Main page content here.</p>

    <content:footer>
        <p>&copy; 2024 My Company</p>
    </content:footer>
</include:layout>
```

## Props and Attributes

The full props system works in Jinja2, including enum validation:

**jinja2/components/button.html**
```html
{# props variant=primary,secondary,danger size=small,medium,large disabled=false #}
<button
    class="btn btn-{{ variant }} btn-{{ size }}"
    {% if disabled %}disabled{% endif %}
    {{ attrs }}
>
    {{ contents }}
</button>
```

**Usage:**
```html
<include:button
    variant="success"
    size="large"
    onclick="alert('Clicked!')"
    data-id="123"
>
    Save Changes
</include:button>
```

**Enum Validation:**
If you use an invalid enum value, you'll get a helpful error message:

```html
<!-- This will raise a TemplateRuntimeError -->
<include:button variant="invalid">Button</include:button>
```

Error message:
```
Invalid value "invalid" for attribute "variant" in component 'components/button.html'.
Allowed values: 'primary', 'secondary', 'danger'. Did you mean "primary"?
Example: <include:button variant="primary">
```

## Icon System

Icons work seamlessly with Jinja2. First configure icons in settings:

```python
# settings.py
STATICFILES_FINDERS = [
    'includecontents.icons.finders.IconSpriteFinder',  # Must be first
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
]

INCLUDECONTENTS_ICONS = {
    'icons': [
        'mdi:home',
        'mdi:user',
        'tabler:star',
        'icons/logo.svg',  # Local SVG files
    ]
}
```

Then use icons in Jinja2 templates:

```html
<!-- HTML syntax (works automatically) -->
<icon:home class="nav-icon" />
<icon:user class="avatar" />

<!-- Template function syntax (also available) -->
{{ icon('home', class='nav-icon') }}
{{ icon('user', class='avatar') }}

<!-- Mixed usage -->
<icon:star class="rating-icon" />
<div>Rating: {{ icon('star', class='small') }}</div>
```

!!! note "Icon Function"
    The `icon()` function is automatically available in Jinja2 templates when using the IncludeContentsExtension. No manual environment setup required.

## Context and Variables

### Django Context Processors

Django context processors work with Jinja2 when configured properly:

**myproject/jinja2.py**
```python
from django.contrib.auth.context_processors import auth
from django.contrib.messages.context_processors import messages
from django.template.context_processors import request
from jinja2 import Environment


def environment(**options):
    env = Environment(**options)
    env.globals.update({
        'static': staticfiles_storage.url,
        'url': reverse,
    })
    return env
```

### Passing Variables to Components

Variables are passed the same way as Django:

```html
<!-- From view context -->
<include:user-card user="{{ user }}" />

<!-- Template variables -->
{% set current_user = request.user %}
<include:user-card user="{{ current_user }}" />

<!-- With filters -->
<include:product-list products="{{ products|list }}" />
```

## Differences from Django Templates

### Syntax Differences

| Feature | Django | Jinja2 |
|---------|--------|--------|
| Comments | `{# comment #}` | `{# comment #}` |
| Variables | `{{ variable }}` | `{{ variable }}` |
| Tags | `{% tag %}` | `{% tag %}` |
| Loops | `{% for %}...{% endfor %}` | `{% for %}...{% endfor %}` |
| Conditionals | `{% if %}...{% endif %}` | `{% if %}...{% endif %}` |
| Template loading | `{% load tag_library %}` | Extensions in settings |

### Jinja2 Advantages

```html
<!-- Inline expressions -->
<include:card title="{{ 'Welcome ' + user.name }}" />

<!-- List/dict literals -->
<include:data items="{{ [1, 2, 3] }}" config="{{ {'theme': 'dark'} }}" />

<!-- Method calls -->
<include:user-info name="{{ user.get_full_name() }}" />

<!-- Advanced filters -->
<include:article content="{{ article.body|markdown|safe }}" />
```

### WrapIf Alternative

Since `{% wrapif %}` isn't available in Jinja2, use conditional macros:

```html
<!-- Jinja2 macro approach -->
{% macro wrap_if(condition, tag, attrs='', class='') %}
  {% if condition %}
    <{{ tag }}{% if attrs %} {{ attrs }}{% endif %}{% if class %} class="{{ class }}"{% endif %}>
  {% endif %}
  {{ caller() }}
  {% if condition %}</{{ tag }}>{% endif %}
{% endmacro %}

<!-- Usage -->
{% call wrap_if(user.is_authenticated, 'div', class='authenticated') %}
    Welcome back, {{ user.name }}!
{% endcall %}
```

## Testing Your Setup

Create a simple test to verify everything works:

**jinja2/test.html**
```html
<!DOCTYPE html>
<html>
<head>
    <title>Test Components</title>
</head>
<body>
    <h1>Component Test</h1>

    <!-- Test template tag syntax -->
    {% includecontents "components/card.html" title="Template Tag" %}
        <p>This uses template tag syntax.</p>
    {% endincludecontents %}

    <!-- Test HTML syntax -->
    <include:card title="HTML Syntax">
        <p>This uses HTML component syntax.</p>
    </include:card>

    <!-- Test named contents -->
    <include:card title="Named Contents">
        <p>Main content</p>
        <content:footer>
            <small>Footer content</small>
        </content:footer>
    </include:card>
</body>
</html>
```

**views.py**
```python
from django.shortcuts import render

def test_components(request):
    return render(request, 'test.html', {
        'user': request.user,
    })
```

## Troubleshooting

### Common Issues

**Extension not loading:**
```python
# Check that extension is properly configured
TEMPLATES = [{
    'BACKEND': 'django.template.backends.jinja2.Jinja2',
    'OPTIONS': {
        'extensions': [
            'includecontents.jinja2.IncludeContentsExtension',  # Must be exact
        ],
    },
}]
```

**HTML syntax not working:**
```python
# Ensure you're using Jinja2 backend, not Django backend
# HTML syntax requires preprocessing which only works with Jinja2
```

**Components not found:**
```
# Check template directory structure
jinja2/
└── components/
    └── card.html  # Should be here
```

**Context variables missing:**
```python
# Configure environment properly in jinja2.py
def environment(**options):
    env = Environment(**options)
    env.globals.update({
        'static': staticfiles_storage.url,
        'url': reverse,
        # Add other global functions here
    })
    return env
```

## Next Steps

- Learn about [HTML Component Syntax](../using-components/html-syntax.md) for modern component development
- Explore [Props & Attrs](../using-components/props-and-attrs.md) for component attribute handling
- Check out [Component Patterns](../building-components/component-patterns.md) for real-world examples
- See [Icons](../icons.md) for the complete icon system guide