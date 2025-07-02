# Wrapif Tag

The `{% wrapif %}` tag provides a clean way to conditionally wrap content with HTML elements, eliminating the need to repeat opening and closing tags in conditional blocks.

## Basic Syntax

```django
{% load includecontents %}
{% wrapif condition %}
    <wrapper-element attribute="value">
        {% contents %}Default content{% endcontents %}
    </wrapper-element>
{% endwrapif %}
```

## Shorthand Syntax

For simple cases, use the compact `then` syntax:

```django
{% wrapif condition then "element" attribute="value" %}
    Content to wrap
{% endwrapif %}
```

## Simple Examples

### Basic Conditional Wrapping

```django
{% wrapif user.is_authenticated then "a" href="/dashboard" class="user-link" %}
    Welcome, {{ user.name }}
{% endwrapif %}
```

**When `user.is_authenticated` is True:**
```html
<a href="/dashboard" class="user-link">Welcome, John</a>
```

**When `user.is_authenticated` is False:**
```html
Welcome, John
```

### Traditional vs Wrapif

=== "Without Wrapif (Repetitive)"

    ```django
    {% if show_link %}
        <a href="{{ url }}" class="link">
            Click here for {{ title }}
        </a>
    {% else %}
        Click here for {{ title }}
    {% endif %}
    ```

=== "With Wrapif (Clean)"

    ```django
    {% wrapif show_link then "a" href=url class="link" %}
        Click here for {{ title }}
    {% endwrapif %}
    ```

## Full Template Syntax

For complex wrappers, use the full template syntax with `{% contents %}` blocks:

```django
{% wrapif user.is_premium %}
    <div class="premium-content">
        <div class="premium-badge">Premium</div>
        <div class="content">
            {% contents %}{{ article.content }}{% endcontents %}
        </div>
        <div class="premium-footer">
            {% contents footer %}Exclusive content{% endcontents %}
        </div>
    </div>
{% endwrapif %}
```

## Conditional Variants

### Wrapelse

Provide an alternative wrapper when the condition is false:

```django
{% wrapif user.is_active then "a" href="/profile" %}
{% wrapelse "span" class="disabled" %}
    {{ user.name }}
{% endwrapif %}
```

**When active:**
```html
<a href="/profile">John Doe</a>
```

**When inactive:**
```html
<span class="disabled">John Doe</span>
```

### Wrapelif

Handle multiple conditions with `{% wrapelif %}`:

```django
{% wrapif priority == "high" then "strong" class="text-red" %}
{% wrapelif priority == "medium" then "em" class="text-yellow" %}
{% wrapelif priority == "low" then "span" class="text-gray" %}
{% wrapelse "span" %}
    {{ task.title }}
{% endwrapif %}
```

### Complex Conditions

The tag supports all Django template conditional operators:

```django
{% wrapif user.is_authenticated and user.is_staff then "div" class="admin-panel" %}
    Admin controls
{% endwrapif %}

{% wrapif price > 100 then "span" class="expensive" %}
    ${{ price }}
{% endwrapif %}

{% wrapif status in "published,featured" then "mark" class="highlight" %}
    {{ article.title }}
{% endwrapif %}
```

## Advanced Usage

### Dynamic Attributes

Use template variables for dynamic attributes:

```django
{% wrapif show_button then "button" type="button" class=button_class data-action=action %}
    {{ button_text }}
{% endwrapif %}
```

### Nested Wrapif

Wrapif tags can be nested for complex conditional structures:

```django
{% wrapif show_section then "section" class="main-content" %}
    {% wrapif show_header then "header" class="section-header" %}
        <h1>{{ section.title }}</h1>
    {% endwrapif %}
    
    <div class="section-body">
        {{ section.content }}
    </div>
    
    {% wrapif show_footer then "footer" class="section-footer" %}
        <p>Updated: {{ section.updated_at|date }}</p>
    {% endwrapif %}
{% endwrapif %}
```

### Multiple Named Contents

When using full template syntax, you can have multiple named content blocks:

```django
{% wrapif show_card %}
    <div class="card">
        {% if contents.header %}
            <div class="card-header">
                {{ contents.header }}
            </div>
        {% endif %}
        
        <div class="card-body">
            {% contents %}Main content{% endcontents %}
        </div>
        
        {% if contents.footer %}
            <div class="card-footer">
                {{ contents.footer }}
            </div>
        {% endif %}
    </div>
{% endwrapif %}
```

**Usage:**
```django
{% wrapif user.has_premium %}
    {% contents header %}Premium Feature{% endcontents %}
    
    This content is only shown to premium users.
    
    {% contents footer %}
        <a href="/upgrade">Upgrade your account</a>
    {% endcontents %}
{% endwrapif %}
```

## Common Use Cases

### Conditional Links

```django
{% wrapif article.url then "a" href=article.url target="_blank" %}
    {{ article.title }}
{% endwrapif %}
```

### Dynamic Headings

```django
{% wrapif level == 1 then "h1" %}
{% wrapelif level == 2 then "h2" %}
{% wrapelif level == 3 then "h3" %}
{% wrapelse "p" %}
    {{ heading_text }}
{% endwrapif %}
```

### Responsive Containers

```django
{% wrapif is_mobile then "div" class="mobile-container" %}
{% wrapelse "div" class="desktop-container" %}
    {{ content }}
{% endwrapif %}
```

### Permission-Based Wrapping

```django
{% wrapif user.can_edit then "div" class="editable" data-edit-url=edit_url %}
    {{ content }}
    {% if user.can_edit %}
        <button class="edit-btn">Edit</button>
    {% endif %}
{% endwrapif %}
```

### Form Field Validation

```django
{% wrapif field.errors then "div" class="field-group error" %}
{% wrapelse "div" class="field-group" %}
    <label for="{{ field.id_for_label }}">{{ field.label }}</label>
    {{ field }}
    {% if field.errors %}
        <div class="error-messages">
            {% for error in field.errors %}
                <span class="error">{{ error }}</span>
            {% endfor %}
        </div>
    {% endif %}
{% endwrapif %}
```

## Boolean Attributes

The wrapif tag properly handles boolean HTML attributes:

```django
{% wrapif is_required then "input" type="text" required %}
{% endwrapif %}
```

When `is_required` is `True`, outputs:
```html
<input type="text" required>
```

When `is_required` is `False`, outputs:
```html
<input type="text">
```

## Performance Considerations

- **Condition evaluation**: Conditions are evaluated once per render
- **Content rendering**: Content is only rendered when the condition matches
- **Template caching**: Wrapper templates benefit from Django's template caching

## Error Handling

### Invalid Syntax

```django
{% wrapif %}  <!-- Missing condition -->
    Content
{% endwrapif %}
```
Raises `TemplateSyntaxError: wrapif tag requires a condition`.

### Malformed Elements

```django
{% wrapif True then "invalid-element-name" %}
    Content
{% endwrapif %}
```
Outputs HTML as-is, but may not be valid HTML.

## Best Practices

### 1. Use Descriptive Conditions

```django
{% wrapif user.can_edit_article then "div" class="editable" %}    <!-- ✅ Good -->
{% wrapif flag then "div" %}                                      <!-- ❌ Unclear -->
```

### 2. Keep Wrapper Logic Simple

For complex wrappers, consider creating a dedicated component instead:

```django
<!-- ✅ Good: Simple wrapper -->
{% wrapif is_featured then "mark" class="featured" %}
    {{ title }}
{% endwrapif %}

<!-- ❌ Consider a component: Too complex for wrapif -->
{% wrapif show_complex_layout %}
    <div class="complex">
        <div class="header">
            <span class="icon"></span>
            <h3>{{ title }}</h3>
        </div>
        <div class="body">
            {% contents %}...{% endcontents %}
        </div>
    </div>
{% endwrapif %}
```

### 3. Combine with Other Tags

Wrapif works well with other Django IncludeContents features:

```django
{% wrapif show_container then "div" class="container" %}
    {% includecontents "components/card.html" title=title %}
        {{ content }}
    {% endincludecontents %}
{% endwrapif %}
```

## Next Steps

- Explore [HTML Component Syntax](../components/html-syntax.md) for modern component development
- Learn about [Props & Attrs](../components/props-and-attrs.md) for component attributes
- Check out [Component Patterns](../advanced/component-patterns.md) for advanced techniques