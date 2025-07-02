# Basic Template Tag Usage

The `{% includecontents %}` tag is the foundation of Django IncludeContents. It works similarly to Django's built-in `{% include %}` tag, but allows you to pass content blocks to the included template.

## Basic Syntax

```django
{% load includecontents %}
{% includecontents "template_name.html" %}
    Content to pass to the template
{% endincludecontents %}
```

The content between the opening and closing tags becomes available as the `{{ contents }}` variable in the included template.

## Simple Example

**templates/greeting.html**
```html
<div class="greeting">
    <h1>Hello!</h1>
    <p>{{ contents }}</p>
</div>
```

**Usage:**
```django
{% load includecontents %}
{% includecontents "greeting.html" %}
    Welcome to our website!
{% endincludecontents %}
```

**Result:**
```html
<div class="greeting">
    <h1>Hello!</h1>
    <p>Welcome to our website!</p>
</div>
```

## Passing Variables

You can pass variables to the included template just like with the standard `{% include %}` tag:

```django
{% includecontents "greeting.html" name="John" age=25 %}
    It's great to have you here!
{% endincludecontents %}
```

**templates/greeting.html**
```html
<div class="greeting">
    <h1>Hello, {{ name }}!</h1>
    <p>Age: {{ age }}</p>
    <p>{{ contents }}</p>
</div>
```

## Context Isolation

Unlike the standard `{% include %}` tag, the included template runs in an isolated context. This means:

1. **Only explicitly passed variables are available** in the included template
2. **Parent template variables are not automatically inherited**
3. **Components are self-contained and predictable**

### Example of Isolation

**Parent template:**
```django
{% load includecontents %}
{% with message="Hello from parent" %}
    {% includecontents "child.html" %}
        Child content
    {% endincludecontents %}
{% endwith %}
```

**templates/child.html**
```html
<div>
    <p>Message: {{ message }}</p>  <!-- This will be empty! -->
    <p>Contents: {{ contents }}</p>
</div>
```

**Result:**
```html
<div>
    <p>Message: </p>  <!-- Empty because message wasn't passed explicitly -->
    <p>Contents: Child content</p>
</div>
```

**Correct usage:**
```django
{% load includecontents %}
{% with message="Hello from parent" %}
    {% includecontents "child.html" message=message %}
        Child content
    {% endincludecontents %}
{% endwith %}
```

## Template Resolution

The `{% includecontents %}` tag follows Django's standard template resolution:

- **Relative paths**: `"components/card.html"` looks in your `DIRS` and app template directories
- **App-specific**: `"myapp/card.html"` for app-specific templates
- **Absolute paths**: Not recommended, but supported

## Error Handling

### Template Not Found
```django
{% includecontents "nonexistent.html" %}
    Content
{% endincludecontents %}
```
Raises `TemplateDoesNotExist` exception.

### Syntax Errors
```django
{% includecontents %}  <!-- Missing template name -->
    Content
{% endincludecontents %}
```
Raises `TemplateSyntaxError`.

## Performance Considerations

- **Template caching**: Included templates are cached by Django's template system
- **Context creation**: Each inclusion creates a new isolated context
- **Rendering**: Content blocks are rendered once and cached during the tag execution

## Advanced Features

The basic `{% includecontents %}` tag supports several advanced features:

- **[Named Contents Blocks](named-contents.md)**: Multiple content sections within a single component
- **[Dynamic Template Names](../advanced/component-patterns.md#dynamic-templates)**: Use variables for template names
- **[Conditional Inclusion](../advanced/component-patterns.md#conditional-components)**: Conditionally include templates

## Comparison with Standard Include

| Feature | `{% include %}` | `{% includecontents %}` |
|---------|-----------------|-------------------------|
| Pass content blocks | ❌ | ✅ |
| Context inheritance | ✅ Full | ❌ Isolated |
| Performance | Slightly faster | Minimal overhead |
| Reusability | Limited | High |
| Component-like behavior | ❌ | ✅ |

## Next Steps

- Learn about [Named Contents Blocks](named-contents.md) for more complex components
- Explore the [HTML Component Syntax](../components/html-syntax.md) for a more modern approach
- Check out [Component Patterns](../advanced/component-patterns.md) for best practices