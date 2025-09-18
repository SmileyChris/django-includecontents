# Iframe Preview System

The showcase component viewer uses an iframe-based preview system to provide complete CSS isolation between your project's component styles and the showcase interface itself.

## How It Works

### CSS Isolation

Components are rendered inside an iframe with their own document context, preventing:
- Showcase interface styles from affecting component appearance
- Component styles from breaking the showcase layout
- Style conflicts between different components

### Template Override

The iframe preview uses the `showcase/preview.html` template which can be overridden in your project to include your design system's CSS files.

#### Basic Override

Create `templates/showcase/preview.html` in your project:

```html
{% extends "showcase/preview.html" %}
{% load static %}

{% block styles %}
    {{ block.super }}
    <link rel="stylesheet" href="{% static 'css/your-design-system.css' %}">
{% endblock %}
```

#### Advanced Override

You can customize the entire preview environment:

```html
{% extends "showcase/preview.html" %}
{% load static %}

{% block styles %}
    {{ block.super }}

    <!-- Your design system CSS -->
    <link rel="stylesheet" href="{% static 'css/design-system.css' %}">
    <link rel="stylesheet" href="{% static 'css/components.css' %}">

    <!-- Fonts -->
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap" rel="stylesheet">

    <!-- Custom preview styling -->
    <style>
        body {
            font-family: 'Inter', sans-serif;
            background: #f8fafc;
            padding: 2rem;
        }
    </style>
{% endblock %}

{% block scripts %}
    {{ block.super }}

    <!-- Add any JavaScript your components need -->
    <script src="{% static 'js/components.js' %}"></script>
{% endblock %}
```

## Automatic Features

### Responsive Sizing

The iframe automatically resizes to match its content height using postMessage communication between the iframe and parent window.

### Example Loading

When a component has examples defined in its metadata, the first example is automatically loaded on page load to provide immediate visual context.

### Error Handling

Preview errors are displayed within the iframe context with proper styling, maintaining the isolation boundary.

## Technical Details

### Dual Endpoint System

The showcase maintains two preview endpoints:

1. **AJAX Endpoint** (`/preview/`): Returns JSON with rendered HTML and template code for the code display
2. **Iframe Endpoint** (`/iframe-preview/`): Returns full HTML document using the preview template

### Communication Protocol

The iframe communicates with the parent window using postMessage for:
- Height adjustments when content changes
- Error states and loading feedback

### Form Submission

Preview updates are handled by dynamically creating and submitting forms to the iframe, allowing for:
- CSRF token handling
- Large content payloads
- Seamless user experience

## Best Practices

### Performance

- Keep your CSS files optimized and minimal
- Use modern CSS features like CSS Grid and Flexbox
- Consider using CSS custom properties for theming

### Accessibility

- Ensure your components work well in the iframe context
- Test keyboard navigation within the preview
- Verify screen reader compatibility

### Development Workflow

1. **Component Development**: Build components with your normal CSS
2. **Showcase Integration**: Add component to templates/components/
3. **Preview Testing**: View in showcase with your project styles
4. **Documentation**: Add metadata files with examples and guidelines

The iframe preview system ensures your components always appear exactly as they will in your application while providing a powerful development and documentation environment.