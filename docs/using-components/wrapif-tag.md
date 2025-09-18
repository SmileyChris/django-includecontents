# Wrapif Tag

The `{% wrapif %}` tag provides a clean way to conditionally wrap content with HTML elements, eliminating the need to repeat opening and closing tags in conditional blocks. This tag solves the common problem where you need to wrap content in an element only under certain conditions - without it, you'd have to duplicate your content in both the "if" and "else" branches. With wrapif, you write your content once and the wrapping happens conditionally.

!!! tip "See wrapif in action"
    Try the interactive examples in the [Showcase preview](../showcase/live-preview.md) to confirm how `{% wrapif %}` behaves with your own data and conditional logic.

## Standard Syntax

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

=== "Standard Syntax"

    ```django
    {% wrapif user.is_authenticated %}
        <a href="/dashboard" class="user-link">
            {% contents %}Welcome, {{ user.name }}{% endcontents %}
        </a>
    {% endwrapif %}
    ```

=== "Shorthand Syntax"

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

=== "With Wrapif - Standard Syntax"

    ```django
    {% wrapif show_link %}
        <a href="{{ url }}" class="link">
            {% contents %}Click here for {{ title }}{% endcontents %}
        </a>
    {% endwrapif %}
    ```

=== "With Wrapif - Shorthand Syntax"

    ```django
    {% wrapif show_link then "a" href=url class="link" %}
        Click here for {{ title }}
    {% endwrapif %}
    ```

## Complex Wrappers

For complex wrappers that need more than a single element, use the standard syntax with full templates:

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

=== "Standard Syntax"

    ```django
    {% wrapif user.is_active %}
        <a href="/profile">
            {% contents %}{{ user.name }}{% endcontents %}
        </a>
    {% wrapelse %}
        <span class="disabled">
            {{ contents }}
        </span>
    {% endwrapif %}
    ```

=== "Shorthand Syntax"

    ```django
    {% wrapif user.is_active then "a" href="/profile" %}
        {{ user.name }}
    {% wrapelse "span" class="disabled" %}
    {% endwrapif %}
    ```
    
    Note: In shorthand syntax, the content comes **before** the `wrapelse` tag

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

=== "Standard Syntax"

    ```django
    {% wrapif priority == "high" %}
        <strong class="text-red">
            {% contents %}{{ task.title }}{% endcontents %}
        </strong>
    {% wrapelif priority == "medium" %}
        <em class="text-yellow">
            {{ contents }}
        </em>
    {% wrapelif priority == "low" %}
        <span class="text-gray">
            {{ contents }}
        </span>
    {% wrapelse %}
        <span>
            {{ contents }}
        </span>
    {% endwrapif %}
    ```

=== "Shorthand Syntax"

    ```django
    {% wrapif priority == "high" then "strong" class="text-red" %}
        {{ task.title }}
    {% wrapelif priority == "medium" then "em" class="text-yellow" %}
    {% wrapelif priority == "low" then "span" class="text-gray" %}
    {% wrapelse "span" %}
    {% endwrapif %}
    ```
    
    Note: In shorthand syntax, the content is placed after the first condition and is reused for all conditions

### Complex Conditions

The tag supports all Django template conditional operators:

=== "Standard Syntax"

    ```django
    {% wrapif user.is_authenticated and user.is_staff %}
        <div class="admin-panel">
            {% contents %}Admin controls{% endcontents %}
        </div>
    {% endwrapif %}
    
    {% wrapif price > 100 %}
        <span class="expensive">
            {% contents %}${{ price }}{% endcontents %}
        </span>
    {% endwrapif %}
    ```

=== "Shorthand Syntax"

    ```django
    {% wrapif user.is_authenticated and user.is_staff then "div" class="admin-panel" %}
        Admin controls
    {% endwrapif %}
    
    {% wrapif price > 100 then "span" class="expensive" %}
        ${{ price }}
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

=== "Standard Syntax"

    ```django
    {% wrapif show_section %}
        <section class="main-content">
            {% contents %}
                {% wrapif show_header %}
                    <header class="section-header">
                        {% contents %}<h1>{{ section.title }}</h1>{% endcontents %}
                    </header>
                {% endwrapif %}
                
                <div class="section-body">
                    {{ section.content }}
                </div>
                
                {% wrapif show_footer %}
                    <footer class="section-footer">
                        {% contents %}<p>Updated: {{ section.updated_at|date }}</p>{% endcontents %}
                    </footer>
                {% endwrapif %}
            {% endcontents %}
        </section>
    {% endwrapif %}
    ```

=== "Shorthand Syntax"

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

When using standard syntax, you can have multiple named content blocks:

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

## Example Use Cases

### Conditional Links

=== "Standard Syntax"

    ```django
    {% wrapif article.url %}
        <a href="{{ article.url }}" target="_blank">
            {% contents %}{{ article.title }}{% endcontents %}
        </a>
    {% endwrapif %}
    ```

=== "Shorthand Syntax"

    ```django
    {% wrapif article.url then "a" href=article.url target="_blank" %}
        {{ article.title }}
    {% endwrapif %}
    ```

### Dynamic Headings

=== "Standard Syntax"

    ```django
    {% wrapif level == 1 %}
        <h1>{% contents %}{{ heading_text }}{% endcontents %}</h1>
    {% wrapelif level == 2 %}
        <h2>{{ contents }}</h2>
    {% wrapelif level == 3 %}
        <h3>{{ contents }}</h3>
    {% wrapelse %}
        <p>{{ contents }}</p>
    {% endwrapif %}
    ```

=== "Shorthand Syntax"

    ```django
    {% wrapif level == 1 then "h1" %}
        {{ heading_text }}
    {% wrapelif level == 2 then "h2" %}
    {% wrapelif level == 3 then "h3" %}
    {% wrapelse "p" %}
    {% endwrapif %}
    ```

### Responsive Containers

=== "Standard Syntax"

    ```django
    {% wrapif is_mobile %}
        <div class="mobile-container">
            {% contents %}{{ content }}{% endcontents %}
        </div>
    {% wrapelse %}
        <div class="desktop-container">
            {{ contents }}
        </div>
    {% endwrapif %}
    ```

=== "Shorthand Syntax"

    ```django
    {% wrapif is_mobile then "div" class="mobile-container" %}
        {{ content }}
    {% wrapelse "div" class="desktop-container" %}
    {% endwrapif %}
    ```

### Permission-Based Wrapping

=== "Standard Syntax"

    ```django
    {% wrapif user.can_edit %}
        <div class="editable" data-edit-url="{{ edit_url }}">
            {% contents %}
                {{ content }}
                {% if user.can_edit %}
                    <button class="edit-btn">Edit</button>
                {% endif %}
            {% endcontents %}
        </div>
    {% endwrapif %}
    ```

=== "Shorthand Syntax"

    ```django
    {% wrapif user.can_edit then "div" class="editable" data-edit-url=edit_url %}
        {{ content }}
        {% if user.can_edit %}
            <button class="edit-btn">Edit</button>
        {% endif %}
    {% endwrapif %}
    ```

### Form Field Validation

=== "Standard Syntax"

    ```django
    {% wrapif field.errors %}
        <div class="field-group error">
            {% contents %}
                <label for="{{ field.id_for_label }}">{{ field.label }}</label>
                {{ field }}
                {% if field.errors %}
                    <div class="error-messages">
                        {% for error in field.errors %}
                            <span class="error">{{ error }}</span>
                        {% endfor %}
                    </div>
                {% endif %}
            {% endcontents %}
        </div>
    {% wrapelse %}
        <div class="field-group">
            {{ contents }}
        </div>
    {% endwrapif %}
    ```

=== "Shorthand Syntax"

    ```django
    {% wrapif field.errors then "div" class="field-group error" %}
        <label for="{{ field.id_for_label }}">{{ field.label }}</label>
        {{ field }}
        {% if field.errors %}
            <div class="error-messages">
                {% for error in field.errors %}
                    <span class="error">{{ error }}</span>
                {% endfor %}
            </div>
        {% endif %}
    {% wrapelse "div" class="field-group" %}
    {% endwrapif %}
    ```

## Boolean Attributes

The wrapif tag properly handles boolean HTML attributes:

=== "Standard Syntax"

    ```django
    {% wrapif is_required %}
        <input type="text" required>
            {% contents %}{% endcontents %}
        </input>
    {% endwrapif %}
    ```

=== "Shorthand Syntax"

    ```django
    {% wrapif is_required then "input" type="text" required %}
    {% endwrapif %}
    ```

When `is_required` is `True`, outputs:
```html
<input type="text" required>
```

When `is_required` is `False`, the input element is not rendered at all (for standard syntax) or rendered without the wrapper (for shorthand with content).

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

- Explore [HTML Component Syntax](../using-components/html-syntax.md) for modern component development
- Learn about [Props & Attrs](../using-components/props-and-attrs.md) for component attributes
- Check out [Component Patterns](../building-components/component-patterns.md) for advanced techniques
