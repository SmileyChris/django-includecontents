# Migration Guide

This guide helps you migrate between different versions of Django IncludeContents and convert from template tag syntax to HTML component syntax.

## Template Tags to HTML Components

The most common migration is from template tag syntax to the modern HTML component syntax.

### Basic Migration

**Before (Template Tags):**
```django
{% load includecontents %}
{% includecontents "components/card.html" title="Hello World" %}
    <p>This is the card content.</p>
{% endincludecontents %}
```

**After (HTML Components):**
```html
<include:card title="Hello World">
    <p>This is the card content.</p>
</include:card>
```

### Named Content Blocks

**Before (Template Tags):**
```django
{% load includecontents %}
{% includecontents "components/layout.html" title="My Page" %}
    <p>Main content goes here.</p>
    
    {% contents sidebar %}
        <nav>Navigation links</nav>
    {% endcontents %}
    
    {% contents footer %}
        <p>Footer content</p>
    {% endcontents %}
{% endincludecontents %}
```

**After (HTML Components):**
```html
<include:layout title="My Page">
    <p>Main content goes here.</p>
    
    <content:sidebar>
        <nav>Navigation links</nav>
    </content:sidebar>
    
    <content:footer>
        <p>Footer content</p>
    </content:footer>
</include:layout>
```

### Variable Attributes

**Before (Template Tags):**
```django
{% includecontents "components/button.html" text=button_text type=form_type disabled=is_disabled %}
    Additional content
{% endincludecontents %}
```

**After (HTML Components):**
```html
<include:button text="{{ button_text }}" type="{{ form_type }}" disabled="{{ is_disabled }}">
    Additional content
</include:button>
```

### Complex Expressions

**Before (Template Tags):**
```django
{% includecontents "components/user-card.html" user=user show_email=user.is_staff|yesno:"true,false" %}
    Welcome message content
{% endincludecontents %}
```

**After (HTML Components):**
```html
<include:user-card user="{{ user }}" show-email="{{ user.is_staff|yesno:'true,false' }}">
    Welcome message content
</include:user-card>
```

## Setup Migration

### Enable HTML Component Syntax

To migrate from template tags to HTML components, you need to configure the custom template engine:

**1. Update your Django settings:**

```python
# settings.py
TEMPLATES = [
    {
        'BACKEND': 'includecontents.django.Engine',  # Changed from DjangoTemplates
        'DIRS': [BASE_DIR / 'templates'],
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

**2. Remove template tag loading:**

Since HTML components work automatically, you can remove `{% load includecontents %}` from templates that use HTML syntax.

**Before:**
```django
{% load includecontents %}
<include:card title="Hello">Content</include:card>
```

**After:**
```html
<include:card title="Hello">Content</include:card>
```

### Mixed Environment

You can use both syntaxes during migration:

```html
<!-- New HTML syntax -->
<include:card title="Modern Card">
    <!-- Old template tag syntax still works -->
    {% load includecontents %}
    {% includecontents "components/old-component.html" %}
        Legacy content
    {% endincludecontents %}
</include:card>
```

## Component File Migration

### Directory Organization

Organize your components for better maintainability:

**Before:**
```
templates/
├── card.html
├── user_profile.html
├── button.html
└── form_field.html
```

**After:**
```
templates/
└── components/
    ├── card.html
    ├── user-profile.html          # Kebab-case naming
    ├── forms/
    │   ├── button.html
    │   └── field.html
    └── ui/
        └── modal.html
```

### File Naming Conventions

Update file names to follow conventions:

**Before:**
- `user_profile.html` → **After:** `user-profile.html`
- `FormField.html` → **After:** `form-field.html`
- `BUTTON.html` → **After:** `button.html`

### Component Props

Add props documentation to your components:

**Before:**
```html
<!-- templates/components/card.html -->
<div class="card {{ class }}">
    <h3>{{ title }}</h3>
    <div>{{ contents }}</div>
</div>
```

**After:**
```html
<!-- templates/components/card.html -->
{# props title, class="" #}
<div {% attrs class="card" %}>
    <h3>{{ title }}</h3>
    <div>{{ contents }}</div>
</div>
```

## Automated Migration Tools

### Find and Replace Patterns

Use these regex patterns to help automate migration:

**1. Basic includecontents tags:**
```regex
# Find:
{% includecontents "components/([^"]+)\.html"([^%]*) %}
(.*?)
{% endincludecontents %}

# Replace with:
<include:$1$2>
$3
</include:$1>
```

**2. Load statements:**
```regex
# Find:
{% load includecontents %}\n

# Replace with:
(empty - remove the line)
```

### Migration Script

Here's a Python script to help with basic migration:

```python
#!/usr/bin/env python3
import re
import os
from pathlib import Path

def migrate_template_file(file_path):
    """Migrate a single template file from template tags to HTML syntax."""
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Remove load statements
    content = re.sub(r'{%\s*load\s+includecontents\s*%}\n?', '', content)
    
    # Convert basic includecontents
    pattern = r'{%\s*includecontents\s+"components/([^"]+)\.html"([^%]*?)\s*%}(.*?){%\s*endincludecontents\s*%}'
    
    def replace_tag(match):
        component_name = match.group(1)
        attributes = match.group(2).strip()
        content_block = match.group(3)
        
        return f'<include:{component_name}{attributes}>{content_block}</include:{component_name}>'
    
    content = re.sub(pattern, replace_tag, content, flags=re.DOTALL)
    
    # Write back
    with open(file_path, 'w') as f:
        f.write(content)

def migrate_templates(template_dir):
    """Migrate all templates in a directory."""
    for template_file in Path(template_dir).rglob('*.html'):
        print(f"Migrating {template_file}")
        migrate_template_file(template_file)

if __name__ == '__main__':
    migrate_templates('templates/')
```

## Version Migrations

### Upgrading from 1.x to 2.x

**Key Changes:**
- HTML component syntax introduced
- Custom template engine available
- Improved props system with validation
- New `{% attrs %}` template tag

**Migration Steps:**

1. **Update package:**
   ```bash
   pip install --upgrade django-includecontents
   ```

2. **Optional: Enable HTML syntax:**
   ```python
   # settings.py - Optional upgrade
   TEMPLATES = [{
       'BACKEND': 'includecontents.django.Engine',
       # ... other settings
   }]
   ```

3. **Update components to use new features:**
   ```html
   <!-- Before -->
   <div class="card {{ class }}">
   
   <!-- After -->
   <div {% attrs class="card" %}>
   ```

### Breaking Changes

**Version 2.0:**
- No breaking changes - fully backward compatible
- Template tag syntax continues to work
- Existing components work without modification

## Testing Migration

### Test Strategy

1. **Before migration:**
   ```bash
   # Run your test suite
   python manage.py test
   
   # Test key pages manually
   python manage.py runserver
   ```

2. **During migration:**
   ```bash
   # Test each migrated template
   python manage.py test apps.tests.test_templates
   
   # Use Django's template debugging
   # settings.py
   TEMPLATES[0]['OPTIONS']['debug'] = True
   ```

3. **After migration:**
   ```bash
   # Full test suite
   python manage.py test
   
   # Performance testing
   python manage.py test --debug-mode
   ```

### Common Migration Issues

**1. Missing component files:**
```
TemplateDoesNotExist: components/my-component.html
```
- **Solution:** Ensure component files are in `templates/components/`

**2. Context variables not available:**
```html
<!-- Component shows empty values -->
```
- **Solution:** Remember context isolation - pass variables explicitly

**3. Attribute parsing errors:**
```
TemplateSyntaxError: Invalid attribute syntax
```
- **Solution:** Quote attribute values: `attribute="{{ value }}"`

## Rollback Plan

If you need to rollback the migration:

### Rollback HTML Components to Template Tags

**1. Revert settings:**
```python
# settings.py
TEMPLATES = [{
    'BACKEND': 'django.template.backends.django.DjangoTemplates',
    # ... original settings
}]
```

**2. Add back load statements:**
```django
{% load includecontents %}
```

**3. Convert HTML syntax back:**
```html
<!-- From: -->
<include:card title="Hello">Content</include:card>

<!-- To: -->
{% includecontents "components/card.html" title="Hello" %}
    Content
{% endincludecontents %}
```

## Migration Checklist

### Pre-Migration
- [ ] Backup your templates directory
- [ ] Document current component usage
- [ ] Test current functionality thoroughly
- [ ] Plan component organization structure

### During Migration
- [ ] Update Django settings (if using HTML syntax)
- [ ] Migrate components file by file
- [ ] Test each migrated component
- [ ] Update internal documentation

### Post-Migration
- [ ] Run full test suite
- [ ] Test all user-facing pages
- [ ] Update team documentation
- [ ] Plan future component development

## Template Engine Migrations

### Migrating from Jinja2 to Django Templates

If you're currently using Jinja2 and want to adopt Django IncludeContents, you'll need to migrate your templates to Django's template syntax:

**Common Jinja2 to Django conversions:**

| Jinja2 | Django Templates |
|--------|------------------|
| `{{ variable \| filter }}` | `{{ variable\|filter }}` (no spaces around pipe) |
| `{% if condition %}` | `{% if condition %}` (same) |
| `{% for item in items %}` | `{% for item in items %}` (same) |
| `{{ loop.index }}` | `{{ forloop.counter }}` |
| `{{ loop.first }}` | `{{ forloop.first }}` |
| `{% macro name() %}` | No direct equivalent - use `{% includecontents %}` |

**Jinja2 alternatives within Django:**

Instead of migrating from Jinja2, consider:
1. **Dual template setup**: Use Django templates for components, Jinja2 for main templates
2. **Macro-based approach**: Implement component-like functionality with Jinja2 macros
3. **Custom Jinja2 extension**: See the [Jinja2 Setup Guide](../getting-started/jinja2-setup.md) for implementation details

### Considerations for Mixed Environments

**Option 1: Dual template engines**
```python
# settings.py
TEMPLATES = [
    {
        'BACKEND': 'includecontents.django.DjangoTemplates',  # For components
        'DIRS': [BASE_DIR / 'templates/components'],
        'APP_DIRS': False,
    },
    {
        'BACKEND': 'django.template.backends.jinja2.Jinja2',  # For main templates
        'DIRS': [BASE_DIR / 'templates/jinja2'],
        'APP_DIRS': True,
    },
]
```

**Option 2: Bridge pattern**
Use Django's `render_to_string()` from within Jinja2 templates to render Django components:

```jinja2
{# Jinja2 template #}
{{ django_component('components/card.html', title='Hello', content=content_var) }}
```

For detailed implementation, see the [Jinja2 Setup Guide](../getting-started/jinja2-setup.md).

## Getting Help

If you encounter issues during migration:

1. **Check the [Troubleshooting Guide](troubleshooting.md)**
2. **Review component examples in the documentation**
3. **Test with minimal examples first**
4. **For Jinja2 questions, see the [Jinja2 Setup Guide](../getting-started/jinja2-setup.md)**
5. **Ask for help on GitHub Issues**

## Next Steps

After successful migration:
- **[Learn advanced component patterns](../building-components/component-patterns.md)**
- **[Set up IDE integration](../tooling-integration/vscode-setup.md)**
- **[Explore CSS styling features](../building-components/css-and-styling.md)**
