# Installation

Django IncludeContents can be installed and configured in multiple ways depending on your needs.

## Requirements

- Python 3.8+
- Django 3.2+
- Django templates OR Jinja2 templates (both supported!)

## Install the Package

```bash
pip install django-includecontents
```

## Configuration Options

Choose your template engine and configuration:

### Option 1: Django Templates with Custom Engine (Recommended)

This option enables the HTML component syntax (`<include:component>`) and automatically loads the template tags.

Replace the default Django template backend in your `settings.py`:

```python
TEMPLATES = [
    {
        'BACKEND': 'includecontents.django.DjangoTemplates',
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

!!! tip "Benefits of the Custom Engine"
    - HTML component syntax: `<include:my-card>`
    - Multi-line template tags
    - Auto-loaded template tags (no need for `{% load includecontents %}`)
    - All standard Django template functionality preserved

### Option 2: Traditional Django Setup

If you prefer to use only the template tags without the HTML syntax, add the app to `INSTALLED_APPS`:

```python
INSTALLED_APPS = [
    # ... your other apps
    'includecontents',
]
```

Then load the template tags in your templates:

```django
{% load includecontents %}
```

### Option 3: Jinja2 Templates

For Jinja2 users, register the extension in your Jinja2 environment:

```python
# settings.py
from jinja2 import Environment
from includecontents.jinja2 import IncludeContentsExtension

def environment(**options):
    env = Environment(extensions=[IncludeContentsExtension], **options)
    return env

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.jinja2.Jinja2',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'environment': 'myproject.jinja2.environment',
        },
    },
]
```

For detailed Jinja2 setup, see the [Jinja2 Setup Guide](jinja2-setup.md).

## Verify Installation

Create a simple test to verify everything is working:

=== "With Custom Engine"

    **templates/components/hello.html**
    ```html
    <div>Hello, {{ name }}! {{ contents }}</div>
    ```

    **In your template**
    ```html
    <include:hello name="World">
        Welcome to Django IncludeContents!
    </include:hello>
    ```

=== "Traditional Setup"

    **templates/hello.html**
    ```html
    <div>Hello, {{ name }}! {{ contents }}</div>
    ```

    **In your template**
    ```django
    {% load includecontents %}
    {% includecontents "hello.html" name="World" %}
        Welcome to Django IncludeContents!
    {% endincludecontents %}
    ```

=== "Jinja2 Setup"

    **templates/components/hello.html**
    ```html
    <div>Hello, {{ name }}! {{ contents }}</div>
    ```

    **In your template**
    ```jinja2
    {% includecontents "hello" name="World" %}
        Welcome to Django IncludeContents!
    {% endincludecontents %}

    {# HTML syntax also works: #}
    <include:hello name="World">
        Welcome to Django IncludeContents!
    </include:hello>
    ```

Both should output:
```html
<div>Hello, World! Welcome to Django IncludeContents!</div>
```

## Icons Setup (Optional)

If you plan to use the icon system, add the icon finder to your static files configuration:

```python
# settings.py
STATICFILES_FINDERS = [
    'includecontents.icons.finders.IconSpriteFinder',  # Must be first for icons
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
]
```

!!! important "Order Matters"
    The `IconSpriteFinder` must be **first** in the list to prevent source SVG files from being served twice.

Then configure your icons:

```python
# settings.py
INCLUDECONTENTS_ICONS = {
    'icons': [
        'mdi:home',
        'tabler:user',
        # ... more icons
    ]
}
```

Now you can use icons in your templates:

```html
<icon:home class="w-6 h-6" />
```

For complete icon documentation, see the [Icons Guide](../icons.md).

## Development Installation

If you want to contribute to the project or run the tests:

```bash
# Clone the repository
git clone https://github.com/SmileyChris/django-includecontents.git
cd django-includecontents

# Install with test dependencies
pip install -e ".[test]"

# Run tests
pytest
```

For complete development setup instructions, see the [Development Guide](../reference/development.md).

## Next Steps

Now that you have Django IncludeContents installed, let's create your first component:

[Quick Start Guide →](quickstart.md){ .md-button .md-button--primary }