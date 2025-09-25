# Showcase Templates Documentation

Showcase templates provide a way to create comprehensive demonstrations of your components, showing all their variants, states, and configurations in a single, well-organized view. They override the default interactive preview mode with a custom, static showcase.

## Overview

When you create a component template, you can optionally create a corresponding showcase template that provides a comprehensive demonstration of that component. This is particularly useful for:

- Demonstrating all variants of a component (primary, secondary, ghost buttons)
- Showing different sizes and states (small, medium, large, disabled)
- Displaying real-world usage examples
- Creating component galleries for design review
- Providing visual regression testing references

## How It Works

The showcase system automatically detects and uses showcase templates based on a simple naming convention:

```
components/
├── showcase/                    # Showcase demo components (namespace)
│   └── forms/
│       ├── button.html          # Demo button component
│       └── button.showcase.html # Showcase template
├── forms/                       # Your project components
│   ├── my-button.html           # Your actual component
│   └── my-button.showcase.html  # Your component's showcase (optional)
```

When a showcase template exists:
- The component detail page shows a "🎭 Custom Showcase" badge
- The preview section displays your showcase instead of the interactive props editor
- The HTML/Django code tabs are hidden (since showcase is static)
- Examples section still appears if defined in metadata

## Namespace Considerations

**Important**: The showcase app includes its own demo components under the `components/showcase/` namespace to avoid collisions with your project's components. When creating showcase templates, you can:

1. **Reference showcase demo components** using paths like `components/showcase/forms/button.html`
2. **Reference your own components** using their regular paths like `components/forms/my-button.html`

The namespace separation ensures that showcase demo components don't interfere with your actual project components.

## Creating a Showcase Template

### 1. Basic Structure

Create a file with the `.showcase.html` suffix next to your component:

```html
{% extends "showcase/preview.html" %}
{% load includecontents %}

{% block content %}
<div class="my-component-showcase">
    <h3>Component Name Showcase</h3>
    <p>Brief description of what this showcase demonstrates.</p>

    <!-- Your showcase sections here -->
</div>
{% endblock content %}

{% block styles %}
    {{ block.super }}
<style>
/* Custom styles for your showcase */
.my-component-showcase {
    font-family: system-ui, -apple-system, sans-serif;
    padding: 1rem;
    max-width: 800px;
    margin: 0 auto;
}
</style>
{% endblock styles %}
```

### 2. Using Your Components

Use the `{% includecontents %}` tag to render your components with different props:

```html
{% block content %}
<div class="button-showcase">
    <!-- Primary Variants -->
    <section class="showcase-section">
        <h4>Primary Variants</h4>
        <div class="button-grid">
            <div class="button-demo">
                {% includecontents "components/showcase/forms/button.html" with label="Small Primary" variant="primary" size="sm" %}{% endincludecontents %}
                <small>Small</small>
            </div>
            <div class="button-demo">
                {% includecontents "components/showcase/forms/button.html" with label="Medium Primary" variant="primary" size="md" %}{% endincludecontents %}
                <small>Medium (default)</small>
            </div>
        </div>
    </section>

    <!-- Disabled States -->
    <section class="showcase-section">
        <h4>Disabled States</h4>
        <div class="button-grid">
            <div class="button-demo">
                {% includecontents "components/showcase/forms/button.html" with label="Disabled" variant="primary" disabled=True %}{% endincludecontents %}
                <small>Disabled Primary</small>
            </div>
        </div>
    </section>
</div>
{% endblock content %}
```

### 3. Context Available

Your showcase template has access to:

- `request` - The current HTTP request
- `component` - ComponentInfo instance with metadata
- `props` - Currently empty dict (showcases don't use interactive props)
- `content` - Currently empty string
- `content_blocks` - Currently empty dict
- `attrs` - Attrs helper instance

## Showcase Template Guidelines

### Structure Your Showcase

Organize your showcase into logical sections:

```html
<div class="component-showcase">
    <h3>Component Name</h3>
    <p>Brief description</p>

    <!-- Section 1: Basic variants -->
    <section class="showcase-section">
        <h4>Basic Variants</h4>
        <!-- Component examples -->
    </section>

    <!-- Section 2: Sizes -->
    <section class="showcase-section">
        <h4>Sizes</h4>
        <!-- Size examples -->
    </section>

    <!-- Section 3: States -->
    <section class="showcase-section">
        <h4>States</h4>
        <!-- State examples -->
    </section>
</div>
```

### Use Consistent Demo Layout

Create a consistent layout for your component demonstrations:

```html
<div class="demo-grid">
    <div class="demo-item">
        {% includecontents "components/your-component.html" with prop="value" %}{% endincludecontents %}
        <small>Description</small>
    </div>
</div>
```

### Include Helpful Labels

Add descriptive labels under each example:

```html
<div class="button-demo">
    {% includecontents "components/forms/button.html" with label="Save" variant="primary" icon_before="💾" %}{% endincludecontents %}
    <small>Primary with icon</small>
</div>
```

## Styling Your Showcase

### Use the Styles Block

Include your showcase-specific styles:

```html
{% block styles %}
    {{ block.super }}  <!-- Include base preview styles -->
<style>
.my-showcase {
    /* Your styles here */
}
</style>
{% endblock styles %}
```

### Common CSS Patterns

Here are some useful CSS patterns for showcases:

```css
/* Main showcase container */
.component-showcase {
    font-family: system-ui, -apple-system, sans-serif;
    padding: 1rem;
    max-width: 800px;
    margin: 0 auto;
}

/* Section headers */
.component-showcase h3 {
    margin-top: 0;
    color: #1e293b;
    border-bottom: 2px solid #e2e8f0;
    padding-bottom: 0.5rem;
}

.component-showcase h4 {
    color: #334155;
    margin-bottom: 1rem;
    font-size: 1.125rem;
}

/* Demo grids */
.demo-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 1rem;
    margin-bottom: 2rem;
}

/* Individual demo items */
.demo-item {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 0.5rem;
    padding: 1rem;
    border: 1px solid #e2e8f0;
    border-radius: 8px;
    background: #fff;
    transition: all 0.2s;
}

.demo-item:hover {
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
    border-color: #cbd5e1;
}

/* Demo labels */
.demo-item small {
    color: #64748b;
    font-size: 0.75rem;
    text-align: center;
    font-weight: 500;
}
```

## Example: Button Showcase

Here's a complete example of a button showcase template:

```html
{% extends "showcase/preview.html" %}
{% load includecontents %}

{% block content %}
<div class="button-showcase">
    <h3>Button Component</h3>
    <p>A comprehensive demonstration of the button component in various configurations.</p>

    <!-- Primary Variants -->
    <section class="showcase-section">
        <h4>Primary Variants</h4>
        <div class="button-grid">
            <div class="button-demo">
                {% includecontents "components/showcase/forms/button.html" with label="Small Primary" variant="primary" size="sm" %}{% endincludecontents %}
                <small>Small</small>
            </div>
            <div class="button-demo">
                {% includecontents "components/showcase/forms/button.html" with label="Medium Primary" variant="primary" size="md" %}{% endincludecontents %}
                <small>Medium (default)</small>
            </div>
            <div class="button-demo">
                {% includecontents "components/showcase/forms/button.html" with label="Large Primary" variant="primary" size="lg" %}{% endincludecontents %}
                <small>Large</small>
            </div>
        </div>
    </section>

    <!-- With Icons -->
    <section class="showcase-section">
        <h4>Buttons with Icons</h4>
        <div class="button-grid">
            <div class="button-demo">
                {% includecontents "components/showcase/forms/button.html" with label="Save" variant="primary" icon_before="💾" %}{% endincludecontents %}
                <small>Icon Before</small>
            </div>
            <div class="button-demo">
                {% includecontents "components/showcase/forms/button.html" with label="Download" variant="secondary" icon_after="⬇️" %}{% endincludecontents %}
                <small>Icon After</small>
            </div>
        </div>
    </section>

    <!-- Disabled States -->
    <section class="showcase-section">
        <h4>Disabled States</h4>
        <div class="button-grid">
            <div class="button-demo">
                {% includecontents "components/showcase/forms/button.html" with label="Disabled" variant="primary" disabled=True %}{% endincludecontents %}
                <small>Disabled Primary</small>
            </div>
        </div>
    </section>
</div>
{% endblock content %}

{% block styles %}
    {{ block.super }}
<style>
.button-showcase {
    font-family: system-ui, -apple-system, sans-serif;
    padding: 1rem;
    max-width: 800px;
    margin: 0 auto;
}

.button-showcase h3 {
    margin-top: 0;
    color: #1e293b;
    border-bottom: 2px solid #e2e8f0;
    padding-bottom: 0.5rem;
}

.showcase-section {
    margin-bottom: 2rem;
}

.showcase-section h4 {
    color: #334155;
    margin-bottom: 1rem;
    font-size: 1.125rem;
}

.button-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 1rem;
}

.button-demo {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 0.5rem;
    padding: 1rem;
    border: 1px solid #e2e8f0;
    border-radius: 8px;
    background: #fff;
    transition: all 0.2s;
}

.button-demo:hover {
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
    border-color: #cbd5e1;
}

.button-demo small {
    color: #64748b;
    font-size: 0.75rem;
    text-align: center;
    font-weight: 500;
}
</style>
{% endblock styles %}
```

## Best Practices

### 1. Show All Important Variants

Include examples of:
- All visual variants (primary, secondary, etc.)
- All sizes (small, medium, large)
- All states (default, hover, focus, disabled)
- With and without optional props (icons, etc.)
- Different content lengths
- Edge cases

### 2. Organize Logically

Group related examples together:
- Basic variants first
- Sizes and states
- Advanced features
- Edge cases last

### 3. Use Descriptive Labels

Each example should have a clear, descriptive label explaining what it demonstrates.

### 4. Keep It Focused

Don't include too many examples - focus on the most important and representative ones.

### 5. Make It Responsive

Ensure your showcase works well on different screen sizes:

```css
.demo-grid {
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
}

@media (max-width: 768px) {
    .demo-grid {
        grid-template-columns: 1fr;
    }
}
```

## Integration with Component Metadata

Showcase templates work alongside your component metadata (YAML/TOML files). The metadata still provides:

- Component description
- Props documentation
- Examples (shown below the showcase)
- Best practices
- Accessibility notes

The showcase complements this by providing visual demonstrations.

## When to Use Showcase Templates

Use showcase templates when:

- Your component has many variants that are best shown visually
- You want to demonstrate real-world usage patterns
- You need comprehensive visual documentation
- You're creating a design system reference
- You want to provide visual regression test references

Don't use showcase templates for:
- Simple components with few variants
- Components where interactive prop editing is more valuable
- Components that need real user interaction to demonstrate

## Troubleshooting

### Showcase Not Appearing

1. Check file naming: `component.showcase.html` next to `component.html`
2. Verify the showcase template extends `showcase/preview.html`
3. Check for syntax errors in your showcase template

### Styling Issues

1. Ensure you're using the `{% block styles %}` correctly
2. Include `{{ block.super }}` to inherit base preview styles
3. Check for CSS conflicts with component styles

### Component Rendering Issues

1. Verify your `{% includecontents %}` syntax
2. Check that prop values match your component's expectations
3. Ensure required props are provided

## Advanced Features

### Custom Base Template

You can create a custom base template for your showcases:

```html
<!-- templates/my_showcase_base.html -->
{% extends "showcase/preview.html" %}

{% block styles %}
    {{ block.super }}
    <link rel="stylesheet" href="{% static 'css/my-showcase.css' %}" />
{% endblock styles %}
```

Then use it in your showcases:

```html
{% extends "my_showcase_base.html" %}
```

### Interactive Elements

You can include JavaScript for interactive demonstrations:

```html
{% block scripts %}
    {{ block.super }}
<script>
// Custom showcase interactions
document.querySelectorAll('.demo-item').forEach(item => {
    item.addEventListener('click', () => {
        item.classList.toggle('highlighted');
    });
});
</script>
{% endblock scripts %}
```

### Dynamic Content

Use Django template logic for dynamic showcases:

```html
{% for variant in "primary,secondary,ghost"|split:"," %}
    <div class="button-demo">
        {% includecontents "components/forms/button.html" with label="Button" variant=variant %}{% endincludecontents %}
        <small>{{ variant|title }}</small>
    </div>
{% endfor %}
```

This comprehensive documentation should help developers understand and effectively use the showcase template system to create beautiful, informative component demonstrations.