# HTML Component Syntax

The HTML component syntax provides a modern, HTML-like way to use components in your Django templates. This feature requires the [custom template engine](../getting-started/installation.md#option-1-with-custom-template-engine-recommended).

## Basic Syntax

```html
<include:component-name attribute="value">
    Content goes here
</include:component-name>
```

Components use HTML-like tags that feel natural and familiar. The component name maps directly to a template file in your `components/` directory.

## Component Discovery

Components are automatically discovered from your `templates/components/` directory:

| Component File | HTML Syntax |
|----------------|-------------|
| `components/card.html` | `<include:card>` |
| `components/user-profile.html` | `<include:user-profile>` |
| `components/forms/field.html` | `<include:forms:field>` |
| `components/ui/buttons/primary.html` | `<include:ui:buttons:primary>` |

### Directory Structure Example

```
templates/
└── components/
    ├── card.html
    ├── user-profile.html
    ├── forms/
    │   ├── field.html
    │   └── select.html
    └── ui/
        ├── button.html
        └── icons/
            └── chevron.html
```

**Usage:**
```html
<include:card title="Welcome">
    <p>Main content</p>
</include:card>

<include:user-profile user="{{ user }}">
    <p>Additional info</p>
</include:user-profile>

<include:forms:field label="Email" type="email" />

<include:ui:button variant="primary">Submit</include:ui:button>

<include:ui:icons:chevron direction="right" />
```

## Self-Closing Components

Components without content can use self-closing syntax:

```html
<include:icon name="star" size="24" />
<include:divider />
<include:loading-spinner color="blue" />
```

## Attribute Handling

### String Attributes

```html
<include:button type="submit" class="btn-primary">Save</include:button>
```

### Variable Attributes

```html
<include:button type="{{ form_type }}" class="{{ css_class }}">
    {{ button_text }}
</include:button>
```

### Template Expressions

All Django template syntax is supported in attributes:

```html
<include:user-card 
    name="{{ user.get_full_name }}"
    avatar="{% if user.avatar %}{{ user.avatar.url }}{% endif %}"
    is-online="{{ user.is_active|yesno:'true,false' }}"
    href="{% url 'user_profile' user.pk %}"
/>
```

### Shorthand Attribute Syntax

When the attribute name matches a variable name, use shorthand:

```html
<!-- Instead of: -->
<include:card title="{{ title }}" author="{{ author }}">

<!-- Use shorthand: -->
<include:card {title} {author}>
```

This is equivalent to:
```html
<include:card title="{{ title }}" author="{{ author }}">
```

## Named Content Blocks

Use HTML-style content tags for named content blocks:

```html
<include:article>
    <content:header>
        <h1>{{ article.title }}</h1>
        <p>By {{ article.author }}</p>
    </content:header>
    
    <p>This is the main article content...</p>
    
    <content:sidebar>
        <h3>Related Articles</h3>
        <ul>
            {% for related in article.related_articles %}
                <li><a href="{{ related.url }}">{{ related.title }}</a></li>
            {% endfor %}
        </ul>
    </content:sidebar>
    
    <content:footer>
        <div class="social-sharing">...</div>
    </content:footer>
</include:article>
```

**Component template (templates/components/article.html):**
```html
<article class="article">
    {% if contents.header %}
        <header class="article-header">
            {{ contents.header }}
        </header>
    {% endif %}
    
    <div class="article-body">
        {{ contents }}
    </div>
    
    {% if contents.sidebar %}
        <aside class="article-sidebar">
            {{ contents.sidebar }}
        </aside>
    {% endif %}
    
    {% if contents.footer %}
        <footer class="article-footer">
            {{ contents.footer }}
        </footer>
    {% endif %}
</article>
```

## Mixing Syntaxes

You can mix HTML content syntax with traditional `{% contents %}` blocks:

```html
<include:card>
    <content:header>
        <h2>Mixed Syntax Example</h2>
    </content:header>
    
    <p>Main content here</p>
    
    {% contents footer %}
        <button>Traditional syntax footer</button>
    {% endcontents %}
</include:card>
```

## Template Syntax in Attributes

Component attributes now support the full Django template language, including variables, filters, and template tags:

```html
<include:ui-button 
    variant="primary"
    href="{% url 'user_settings' %}"
    class="btn {% if user.is_premium %}btn-premium{% endif %}"
    data-user-id="{{ user.pk }}"
>
    {% if user.is_premium %}
        Premium Settings
    {% else %}
        Basic Settings
    {% endif %}
</include:ui-button>
```

### Template Variables and Filters

Use Django template variables and filters in any attribute:

```html
<include:card 
    title="{{ product.name }}"
    price="{{ product.price|floatformat:2 }}"
    url="{{ product.get_absolute_url }}"
    active="{{ user.is_premium|yesno:'true,false' }}"
    count="{{ items|length|add:1 }}"
/>
```

### Mixed Content

Combine static text with template variables for dynamic attributes:

```html
<include:button 
    class="btn btn-{{ variant }} {{ 'active' if is_active }}"
    href="/products/{{ product.id }}/details/"
    data-info="Count: {{ total }} of {{ maximum }}"
    title="{{ product.name }} - ${{ product.price }}"
/>
```

### Template Tags

Use any Django template tag including `{% if %}`, `{% for %}`, and `{% url %}`:

```html
<!-- Conditional classes -->
<include:card 
    class="card {% if featured %}featured{% endif %} {% if new %}new{% endif %}"
>

<!-- Dynamic lists -->
<include:select
    data-options="{% for opt in options %}{{ opt.value }}:{{ opt.label }}{% if not forloop.last %},{% endif %}{% endfor %}"
>

<!-- URL generation -->
<include:link 
    href="{% url 'product_detail' pk=product.pk %}"
    class="link {% if product.on_sale %}sale{% endif %}"
>
    View Product
</include:link>
```

### Complex Example

Here's a real-world example combining multiple template features:

```html
<include:product-card 
    title="{{ product.name }}"
    price="{{ product.price|floatformat:2 }}"
    href="{% url 'product_detail' product.slug %}"
    class="product-card {% if product.on_sale %}on-sale{% endif %}"
    data-category="{{ product.category.slug }}"
    stock-status="{{ product.stock|yesno:'in-stock,out-of-stock' }}"
>
    {% if product.is_featured %}
        <content:badge>Featured</content:badge>
    {% endif %}
    
    {{ product.description|truncatewords:20 }}
    
    <content:footer>
        <p class="reviews">{{ product.review_count }} review{{ product.review_count|pluralize }}</p>
    </content:footer>
</include:product-card>
```

## Component Naming Conventions

### Valid Component Names

Components must follow HTML custom element naming rules:

- ✅ `card`, `user-profile`, `my-component`
- ✅ `forms:field`, `ui:button`
- ❌ `Card` (uppercase not allowed)
- ❌ `123-component` (can't start with number)
- ❌ `div` (conflicts with HTML elements)

### Recommended Patterns

```html
<!-- ✅ Good: Descriptive and specific -->
<include:user-avatar size="large" />
<include:product-price value="{{ product.price }}" />
<include:forms:text-field label="Username" />

<!-- ❌ Avoid: Too generic -->
<include:component />
<include:item />
<include:thing />
```

## Error Handling

### Component Not Found

```html
<include:nonexistent-component>
    Content
</include:nonexistent-component>
```

Raises `TemplateDoesNotExist: components/nonexistent-component.html`

### Invalid Syntax

```html
<include:my-component attribute=>  <!-- Missing value -->
    Content
</include:my-component>
```

Raises `TemplateSyntaxError` with details about the syntax error.

## Performance Considerations

- **Template Resolution**: Component templates are cached by Django's template system
- **Attribute Parsing**: Attributes are parsed once per template compilation
- **Content Rendering**: Similar performance to equivalent `{% includecontents %}` tags

## Comparison with Template Tags

| Feature | Template Tag Syntax | HTML Syntax |
|---------|-------------------|-------------|
| **Readability** | Django-specific | HTML-like, familiar |
| **IDE Support** | Limited | Better (HTML tooling) |
| **Formatting** | Manual | Prettier/formatter support |
| **Nesting** | Verbose | Clean and intuitive |
| **Learning Curve** | Django knowledge needed | HTML knowledge sufficient |

### Template Tag Syntax
```django
{% load includecontents %}
{% includecontents "components/card.html" title="Hello" %}
    {% includecontents "components/button.html" variant="primary" %}
        Click me
    {% endincludecontents %}
{% endincludecontents %}
```

### HTML Syntax
```html
<include:card title="Hello">
    <include:button variant="primary">
        Click me
    </include:button>
</include:card>
```

## IDE and Tooling Support

### VS Code

The HTML syntax works well with VS Code's HTML language features:

- **Syntax highlighting**: Components appear as HTML elements
- **Auto-completion**: Attribute completion works
- **Folding**: Component blocks can be collapsed
- **Formatting**: Works with Prettier and other HTML formatters

### Prettier Integration

HTML components format beautifully with Prettier:

```html
<!-- Before formatting -->
<include:card title="Hello" class="my-card"><p>Content</p><content:footer>Footer</content:footer></include:card>

<!-- After prettier -->
<include:card title="Hello" class="my-card">
  <p>Content</p>
  <content:footer>Footer</content:footer>
</include:card>
```

## Migration from Template Tags

Converting existing `{% includecontents %}` usage to HTML syntax:

=== "Before (Template Tags)"

    ```django
    {% load includecontents %}
    {% includecontents "components/user-card.html" user=user show_email=True %}
        <p>Welcome back!</p>
        {% contents actions %}
            <a href="{% url 'profile' %}">Edit Profile</a>
        {% endcontents %}
    {% endincludecontents %}
    ```

=== "After (HTML Syntax)"

    ```html
    <include:user-card user="{{ user }}" show-email="true">
        <p>Welcome back!</p>
        <content:actions>
            <a href="{% url 'profile' %}">Edit Profile</a>
        </content:actions>
    </include:user-card>
    ```

## Best Practices

### 1. Use Semantic Component Names

```html
<!-- ✅ Good: Clear purpose -->
<include:article-summary article="{{ article }}" />
<include:user-avatar user="{{ user }}" size="small" />

<!-- ❌ Avoid: Generic names -->
<include:widget data="{{ data }}" />
<include:component type="user" />
```

### 2. Keep Components Focused

```html
<!-- ✅ Good: Single responsibility -->
<include:product-image product="{{ product }}" />
<include:product-price product="{{ product }}" />
<include:product-rating product="{{ product }}" />

<!-- ❌ Avoid: Too many responsibilities -->
<include:product-everything product="{{ product }}" />
```

### 3. Use Consistent Naming

```html
<!-- ✅ Good: Consistent pattern -->
<include:forms:text-field />
<include:forms:email-field />
<include:forms:password-field />

<!-- ❌ Inconsistent -->
<include:forms:text-field />
<include:email-input />
<include:password-form />
```

## Next Steps

- Learn about [Props & Attrs](props-and-attrs.md) for component attribute handling
- Explore [Advanced Props](../building-components/advanced-props.md) for validation and enum props
- Check out [CSS Classes](../building-components/css-and-styling.md) for advanced styling features