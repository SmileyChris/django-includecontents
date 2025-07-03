# Props & Attrs

Components can define props (properties) to specify which attributes they expect and how to handle undefined attributes. This system provides validation, defaults, and flexible attribute handling.

## Defining Props

Define props in a comment at the top of your component template:

```html
{# props title, description="", show_icon=True #}
<div class="card">
    <h2>{{ title }}</h2>
    {% if description %}
        <p>{{ description }}</p>
    {% endif %}
    {% if show_icon %}
        <span class="icon">★</span>
    {% endif %}
    <div class="content">
        {{ contents }}
    </div>
</div>
```

## Props Syntax

### Required Props

Props without default values are required:

```html
{# props title, author #}
```

If you use the component without required props, a `TemplateSyntaxError` is raised:

```html
<!-- ❌ Error: Missing required props -->
<include:article>Content</include:article>
```

```html
<!-- ✅ Correct: All required props provided -->
<include:article title="My Article" author="John Doe">Content</include:article>
```

### Optional Props with Defaults

Props with default values are optional:

```html
{# props title, show_date=True, priority="normal" #}
```

**Default value types:**
- **String**: `description="Default text"`
- **Boolean**: `visible=True`, `hidden=False`
- **Number**: `count=0`, `rating=5.0`
- **None**: `optional_value=None`

### Usage Example

```html
{# props title, subtitle="", priority="normal", show_meta=True #}
<article class="article priority-{{ priority }}">
    <header>
        <h1>{{ title }}</h1>
        {% if subtitle %}
            <h2>{{ subtitle }}</h2>
        {% endif %}
    </header>
    
    <div class="content">
        {{ contents }}
    </div>
    
    {% if show_meta %}
        <footer class="meta">
            Priority: {{ priority }}
        </footer>
    {% endif %}
</article>
```

**Usage:**
```html
<!-- Using defaults -->
<include:article title="Hello World">
    <p>Article content...</p>
</include:article>

<!-- Overriding defaults -->
<include:article 
    title="Important News" 
    subtitle="Breaking Story"
    priority="high"
    show-meta="false"
>
    <p>Important content...</p>
</include:article>
```

## The `attrs` Variable

Attributes not defined in props are collected in the `attrs` variable, which can be rendered as HTML attributes.

### Basic Usage

```html
{# props title #}
<div {{ attrs }}>
    <h2>{{ title }}</h2>
    <div class="content">{{ contents }}</div> 
</div>
```

**Usage:**
```html
<include:card title="Hello" class="my-card" data-id="123">
    Content
</include:card>
```

**Output:**
```html
<div class="my-card" data-id="123">
    <h2>Hello</h2>
    <div class="content">Content</div>
</div>
```

### Accessing Individual Attributes

You can access individual undefined attributes:

```html
{# props title #}
<div class="card">
    <h2>{{ title }}</h2>
    {% if attrs.class %}
        <p>Custom class: {{ attrs.class }}</p>
    {% endif %}
    {% if attrs.dataId %}
        <p>Data ID: {{ attrs.dataId }}</p>
    {% endif %}
    <div {{ attrs }}>{{ contents }}</div>
</div>
```

!!! note "Attribute Name Conversion"
    Kebab-case attributes are converted to camelCase for access:
    - `data-id` becomes `attrs.dataId`
    - `my-custom-attr` becomes `attrs.myCustomAttr`

## The `{% attrs %}` Tag

The `{% attrs %}` tag provides more control over attribute rendering with fallback values and class handling.

### Basic Syntax

```html
{% attrs attribute="fallback_value" %}
```

### Providing Defaults

```html
{# props title #}
<div {% attrs class="card" id="default-card" %}>
    <h2>{{ title }}</h2>
    <div class="content">{{ contents }}</div>
</div>
```

**Usage:**
```html
<!-- Uses defaults -->
<include:card title="Hello">Content</include:card>
<!-- Output: <div class="card" id="default-card"> -->

<!-- Overrides defaults -->
<include:card title="Hello" class="custom-card" id="my-card">Content</include:card>
<!-- Output: <div class="custom-card" id="my-card"> -->
```

### Class Handling

The `{% attrs %}` tag provides special handling for CSS classes:

#### Extending Classes

Use `"& "` prefix to append classes after user-provided classes:

```html
{# props #}
<button {% attrs class="& btn btn-default" %}>
    {{ contents }}
</button>
```

**Usage:**
```html
<include:button class="my-button">Click me</include:button>
```

**Output:**
```html
<button class="my-button btn btn-default">Click me</button>
```

#### Prepending Classes

Use `" &"` suffix to prepend classes before user-provided classes:

```html
{# props #}
<div {% attrs class="container &" %}>
    {{ contents }}
</div>
```

**Usage:**
```html
<include:wrapper class="my-content">Content</include:wrapper>
```

**Output:**
```html
<div class="container my-content">Content</div>
```

#### Conditional Classes

Use the `class:` prefix for conditional classes:

```html
{# props active=False, disabled=False #}
<button {% attrs class="btn" class:active=active class:disabled=disabled %}>
    {{ contents }}
</button>
```

**Usage:**
```html
<include:button active="true" disabled="false">Active Button</include:button>
```

**Output:**
```html
<button class="btn active">Active Button</button>
```

## Grouped Attributes

For complex components, you can group attributes by prefix:

### Defining Groups

```html
{# props label, value #}
<div {% attrs class="field" %}>
    <label>{{ label }}</label>
    <input {% attrs.input type="text" value=value %}>
</div>
```

### Using Groups

```html
<include:form-field 
    label="Username" 
    value="john"
    class="form-group"
    input.class="form-control"
    input.placeholder="Enter username"
    input.required="true"
>
</include:form-field>
```

**Output:**
```html
<div class="field form-group">
    <label>Username</label>
    <input type="text" value="john" class="form-control" placeholder="Enter username" required>
</div>
```

## Boolean Attributes

HTML boolean attributes are handled correctly:

```html
{# props #}
<input {% attrs type="text" %}>
```

**Usage:**
```html
<include:input required disabled readonly>
```

**Output:**
```html
<input type="text" required disabled readonly>
```

## Advanced Examples

### Card Component with Full Props System

```html
{# props title, subtitle="", variant="default", collapsible=False #}
<div {% attrs class="card card-{{ variant }}" class:collapsible=collapsible %}>
    <div class="card-header">
        <h3>{{ title }}</h3>
        {% if subtitle %}
            <p class="subtitle">{{ subtitle }}</p>
        {% endif %}
        {% if collapsible %}
            <button class="collapse-toggle">Toggle</button>
        {% endif %}
    </div>
    <div class="card-body">
        {{ contents }}
    </div>
    {% if contents.footer %}
        <div class="card-footer">
            {{ contents.footer }}
        </div>
    {% endif %}
</div>
```

**Usage:**
```html
<include:card 
    title="User Profile" 
    subtitle="Manage your account"
    variant="primary"
    collapsible="true"
    data-user-id="{{ user.pk }}"
    class="my-custom-card"
>
    <p>Profile content here...</p>
    <content:footer>
        <button>Save Changes</button>
    </content:footer>
</include:card>
```

### Form Field Component

```html
{# props name, label="", type="text", required=False #}
<div {% attrs class="form-field" class:required=required %}>
    {% if label %}
        <label for="{{ name }}">
            {{ label }}
            {% if required %}<span class="required">*</span>{% endif %}
        </label>
    {% endif %}
    <input {% attrs.input 
        type=type 
        name=name 
        id=name
        required=required
    %}>
    {% if contents.help %}
        <small class="help-text">{{ contents.help }}</small>
    {% endif %}
    {% if contents.errors %}
        <div class="error-messages">{{ contents.errors }}</div>
    {% endif %}
</div>
```

**Usage:**
```html
<include:form-field 
    name="email" 
    label="Email Address"
    type="email"
    required="true"
    class="mb-3"
    input.class="form-control"
    input.placeholder="Enter your email"
>
    <content:help>We'll never share your email with anyone.</content:help>
</include:form-field>
```

## Validation and Error Handling

### Missing Required Props

```html
{# props title, author #}
<!-- Component definition -->

<!-- ❌ This will raise TemplateSyntaxError -->
<include:article author="John">
    Content without required title
</include:article>
```

**Error message:**
```
TemplateSyntaxError: Missing required prop 'title' for component 'article'
```

### Type Validation

While Django templates don't enforce strict typing, you can add validation in your component:

```html
{# props count=0 #}
{% if count|add:0 != count %}
    <div class="error">Count must be a number</div>
{% else %}
    <div class="counter">Count: {{ count }}</div>
{% endif %}
```

## Best Practices

### 1. Document Your Props

```html
{# 
props:
  title (required): The main heading text
  subtitle (optional): Secondary heading text  
  variant (optional): Style variant - "default", "primary", "success", "danger"
  collapsible (optional): Whether the card can be collapsed
#}
<div class="card">
    <!-- component template -->
</div>
```

### 2. Provide Sensible Defaults

```html
{# props title, size="medium", color="blue", rounded=True #}
```

### 3. Use Descriptive Prop Names

```html
<!-- ✅ Good: Clear and descriptive -->
{# props user_name, show_avatar=True, avatar_size="medium" #}

<!-- ❌ Avoid: Vague or abbreviated -->
{# props name, show=True, size="med" #}
```

### 4. Group Related Attributes

```html
{# props label, value, help_text="" #}
<div class="form-group">
    <label>{{ label }}</label>
    <input {% attrs.input type="text" value=value %}>
    <button {% attrs.button type="button" %}>Helper</button>
    {% if help_text %}
        <small>{{ help_text }}</small>
    {% endif %}
</div>
```

### 5. Handle Edge Cases

```html
{# props items=[] #}
{% if items %}
    <ul {{ attrs }}>
        {% for item in items %}
            <li>{{ item }}</li>
        {% endfor %}
    </ul>
{% else %}
    <p class="empty-message">No items to display</p>
{% endif %}
```

## Common Patterns

### Wrapper Components

```html
{# props tag="div" #}
<{{ tag }} {% attrs class="wrapper" %}>
    {{ contents }}
</{{ tag }}>
```

### Conditional Rendering

```html
{# props visible=True, title="" #}
{% if visible %}
    <div {{ attrs }}>
        {% if title %}<h3>{{ title }}</h3>{% endif %}
        {{ contents }}
    </div>
{% endif %}
```

### Multi-Variant Components

```html
{# props variant="default" #}
<div {% attrs class="alert alert-{{ variant }}" %}>
    {% if variant == "success" %}
        <span class="icon">✓</span>
    {% elif variant == "error" %}
        <span class="icon">✗</span>
    {% endif %}
    {{ contents }}
</div>
```

## Next Steps

- Learn about [Advanced Props](../building-components/advanced-props.md) for enum validation and complex prop handling
- Explore [CSS Classes](../building-components/css-and-styling.md) for advanced class management
- Check out [Component Patterns](../building-components/component-patterns.md) for real-world examples