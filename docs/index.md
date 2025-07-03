# Django IncludeContents

A powerful Django package that brings component-like functionality to Django templates through enhanced template tags and optional HTML component syntax.

## What is Django IncludeContents?

Django IncludeContents provides two main features:

1. **Enhanced Template Tags**: The `{% includecontents %}` tag allows you to pass content blocks to included templates, creating reusable components
2. **HTML Component Syntax**: An optional custom template engine that lets you write components using HTML-like syntax

## Key Features

- **🧩 Component-like Templates**: Create reusable template components with isolated contexts
- **📝 HTML Syntax**: Use familiar HTML-like syntax for components (e.g., `<include:my-card>`)
- **🎯 Props System**: Define required and optional props with validation and defaults
- **🎨 CSS Class Management**: Advanced class handling with conditional and extended classes
- **🔀 Conditional Wrapping**: Clean conditional HTML wrapper syntax with `{% wrapif %}`
- **📄 Multi-line Tags**: Support for multi-line template tags for better readability
- **⚡ Developer Experience**: Great integration with Prettier, VS Code, and Tailwind CSS

## Quick Example

=== "HTML Component Syntax"

    ```html
    <include:card title="Hello">
        <p>This content gets passed to the component</p>
    </include:card>
    ```

=== "Template Tag Syntax"

    ```django
    {% load includecontents %}
    {% includecontents "components/card.html" title="Hello" %}
        <p>This content gets passed to the component</p>
    {% endincludecontents %}
    ```

Both examples render the same component defined in `templates/components/card.html`:

```html
<div class="card">
    <h2>{{ title }}</h2>
    <div class="content">
        {{ contents }}
    </div>
</div>
```

## Getting Started

Ready to add component-like functionality to your Django templates?

[Get Started →](getting-started/installation.md){ .md-button .md-button--primary }
[Quick Start Guide →](getting-started/quickstart.md){ .md-button }

## Why Django IncludeContents?

### Traditional Django Templates
```django
<!-- Lots of repetitive HTML -->
<div class="card border rounded p-4">
    <h2 class="text-xl font-bold">{{ title1 }}</h2>
    <div class="content">{{ content1 }}</div>
</div>

<div class="card border rounded p-4">
    <h2 class="text-xl font-bold">{{ title2 }}</h2>
    <div class="content">{{ content2 }}</div>
</div>
```

### With Django IncludeContents
```html
<include:card title="{{ title1 }}">{{ content1 }}</include:card>
<include:card title="{{ title2 }}">{{ content2 }}</include:card>
```

Clean, reusable, and maintainable!