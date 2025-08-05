# Django IncludeContents

A powerful Django package that brings component-like functionality to Django templates through enhanced template tags and optional HTML component syntax.

## What is Django IncludeContents?

Django IncludeContents provides three powerful features:

1. **Enhanced Template Tags**: The `{% includecontents %}` tag allows you to pass content blocks to included templates, creating reusable components
2. **HTML Component Syntax**: An optional custom template engine that lets you write components using HTML-like syntax
3. **Icon System**: Generate optimized SVG sprite sheets from Iconify icons and your local SVG files

## Key Features

- **🧩 Component-like Templates**: Create reusable template components with isolated contexts
- **📝 HTML Syntax**: Use familiar HTML-like syntax for components (e.g., `<include:my-card>`)
- **🎭 Icon System**: SVG sprite sheets from 150,000+ Iconify icons and local files (e.g., `<icon:home>`)
- **🎯 Props System**: Define required and optional props with validation and defaults
- **🎨 CSS Class Management**: Advanced class handling with conditional and extended classes
- **🔀 Conditional Wrapping**: Clean conditional HTML wrapper syntax with `{% wrapif %}`
- **📄 Multi-line Tags**: Support for multi-line template tags for better readability
- **⚡ Developer Experience**: Great integration with Prettier, VS Code, and Tailwind CSS

## Quick Examples

### Components with HTML Syntax

```html
<!-- Use components like HTML elements -->
<include:card title="Welcome" variant="primary">
    <p>Build reusable components with familiar syntax!</p>
</include:card>

<!-- Icons are just as easy -->
<icon:home class="w-6 h-6" />
<icon:user class="avatar" use.role="img" />
```

### Icon System

```python
# settings.py
INCLUDECONTENTS_ICONS = {
    'icons': [
        'mdi:home',         # Material Design Icons
        'tabler:user',      # Tabler Icons
        'lucide:star',      # Lucide Icons
        'icons/logo.svg',   # Your own SVG files
    ]
}
```

```html
<!-- Icons render as optimized SVG sprites -->
<button class="btn">
    <icon:save use.aria-hidden="true" />
    Save Document
</button>
```

### Traditional Template Tag Syntax

```django
{% load includecontents %}
{% includecontents "components/card.html" title="Welcome" %}
    <p>Build reusable components!</p>
{% endincludecontents %}
```

## Getting Started

Ready to add component-like functionality to your Django templates?

[Get Started →](getting-started/installation.md){ .md-button .md-button--primary }
[Quick Start Guide →](getting-started/quickstart.md){ .md-button }

## Why Django IncludeContents?

### Without Django IncludeContents
```django
<!-- Repetitive component code -->
<div class="card border rounded p-4">
    <h2 class="text-xl font-bold">{{ title1 }}</h2>
    <div class="content">{{ content1 }}</div>
</div>

<!-- Messy icon implementation -->
<img src="{% static 'icons/home.svg' %}" alt="Home" class="w-6 h-6">
<!-- or -->
<i class="fas fa-home"></i>  <!-- Font icons = extra CSS weight -->
```

### With Django IncludeContents
```html
<!-- Clean, reusable components -->
<include:card title="{{ title1 }}">{{ content1 }}</include:card>

<!-- Optimized SVG icons -->
<icon:home class="w-6 h-6" />
```

**Benefits:**
- ✅ Write less, do more
- ✅ Consistent UI components
- ✅ Optimized SVG sprites (no font icon CSS)
- ✅ Better performance and accessibility
- ✅ Easier to maintain