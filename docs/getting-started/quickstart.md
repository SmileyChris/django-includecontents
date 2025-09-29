# Quick Start

Get up and running with Django IncludeContents in 5 minutes! This guide assumes you have Django IncludeContents [installed](installation.md) with the custom template engine.

!!! note "Template Engine Support"
    This guide uses HTML component syntax (`<include:component>`). This syntax works with:

    - **Django**: Custom template engine required
    - **Jinja2**: Works automatically with the extension

    For template tag syntax (`{% includecontents %}`), see [template tag examples](../using-components/template-tag-syntax.md).

## Create Your First Component

### 1. Create a Component Template

Create a `components` directory in your templates folder and add your first component:

**templates/components/welcome-card.html**
```html
{# props title, subtitle="" #}
<div class="card border rounded-lg p-6 shadow-sm">
    <h2 class="text-2xl font-bold text-gray-900">{{ title }}</h2>
    {% if subtitle %}
        <p class="text-gray-600 mt-2">{{ subtitle }}</p>
    {% endif %}
    <div class="mt-4">
        {{ contents }}
    </div>
</div>
```

### 2. Use the Component

In any template, use your component with HTML-like syntax:

**templates/home.html**
```html
<include:welcome-card title="Welcome!" subtitle="Getting started is easy">
    <p>This is your first Django IncludeContents component!</p>
    <p>You can include any HTML content here.</p>
</include:welcome-card>
```

### 3. See the Result

The component renders as:

```html
<div class="card border rounded-lg p-6 shadow-sm">
    <h2 class="text-2xl font-bold text-gray-900">Welcome!</h2>
    <p class="text-gray-600 mt-2">Getting started is easy</p>
    <div class="mt-4">
        <p>This is your first Django IncludeContents component!</p>
        <p>You can include any HTML content here.</p>
    </div>
</div>
```

## Understanding the Example

Let's break down what happened:

1. **Component Definition**: `{# props title, subtitle="" #}` defines that this component requires a `title` and has an optional `subtitle`
2. **HTML Syntax**: `<include:welcome-card>` tells Django to render the `components/welcome-card.html` template
3. **Props**: `title="Welcome!"` and `subtitle="Getting started is easy"` are passed as template variables
4. **Content**: Everything between the opening and closing tags becomes the `{{ contents }}` variable

## Common Patterns

### Using Variables from Context

```html
<include:welcome-card title="{{ user.name }}" subtitle="Welcome back!">
    <p>You have {{ notifications.count }} new notifications.</p>
</include:welcome-card>
```

### Conditional Rendering

```html
{% if user.is_authenticated %}
    <include:welcome-card title="Welcome back, {{ user.name }}!">
        <p>Ready to continue where you left off?</p>
    </include:welcome-card>
{% else %}
    <include:welcome-card title="Welcome, Guest!">
        <p><a href="{% url 'login' %}">Sign in</a> to get started.</p>
    </include:welcome-card>
{% endif %}
```

### Named Content Blocks

For more complex components, use named content blocks:

**templates/components/layout-card.html**
```html
<div class="card">
    <header class="card-header">
        {{ contents.header }}
    </header>
    <main class="card-body">
        {{ contents }}
    </main>
    {% if contents.footer %}
        <footer class="card-footer">
            {{ contents.footer }}
        </footer>
    {% endif %}
</div>
```

**Usage:**
```html
<include:layout-card>
    <content:header>
        <h1>My Title</h1>
    </content:header>
    
    <p>This is the main content area.</p>
    
    <content:footer>
        <button>Action</button>
    </content:footer>
</include:layout-card>
```

## Without the Custom Engine

If you're using the traditional setup (without the custom template engine), the syntax is slightly different:

```django
{% load includecontents %}

{% includecontents "components/welcome-card.html" title="Welcome!" subtitle="Getting started is easy" %}
    <p>This is your first Django IncludeContents component!</p>
    <p>You can include any HTML content here.</p>
{% endincludecontents %}
```

## Next Steps

Now that you've created your first component, explore more features:

- **[Template Tag Usage](../using-components/template-tag-syntax.md)**: Learn about the `{% includecontents %}` tag
- **[HTML Components](../using-components/html-syntax.md)**: Dive deeper into component syntax
- **[Props & Attrs](../using-components/props-and-attrs.md)**: Master the props system
- **[Wrapif Tag](../using-components/wrapif-tag.md)**: Learn conditional wrapping

Ready to build more complex components? Check out the [Component Patterns](../building-components/component-patterns.md) guide!