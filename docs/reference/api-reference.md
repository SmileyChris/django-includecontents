# API Reference

Complete reference for all Django IncludeContents template tags, template engine features, and configuration options.

## Template Tags

### `{% includecontents %}`

Include a template with content blocks.

**Syntax:**
```django
{% includecontents template_name [context_vars] %}
    [content]
    [{% contents block_name %}content{% endcontents %}]
{% endincludecontents %}
```

**Parameters:**
- `template_name`: String or variable containing the template path
- `context_vars`: Optional keyword arguments to pass to the template

**Example:**
```django
{% includecontents "components/card.html" title="Hello" count=5 %}
    Main content
    {% contents footer %}Footer content{% endcontents %}
{% endincludecontents %}
```

### `{% contents %}`

Define named content blocks within `{% includecontents %}`.

**Syntax:**
```django
{% contents block_name %}content{% endcontents %}
```

**Parameters:**
- `block_name`: Name of the content block (available as `contents.block_name`)

### `{% wrapif %}`

Conditionally wrap content with HTML elements.

**Syntax:**
```django
{% wrapif condition %}
    <wrapper>
        {% contents %}content{% endcontents %}
    </wrapper>
{% endwrapif %}
```

**Shorthand syntax:**
```django
{% wrapif condition then "tag" attr=value %}
    content
{% endwrapif %}
```

**Parameters:**
- `condition`: Boolean expression to evaluate
- `tag`: HTML tag name (in shorthand syntax)
- `attr=value`: HTML attributes (in shorthand syntax)

**Conditional variants:**
- `{% wrapelif condition %}` - Else-if condition
- `{% wrapelse %}` - Else block

### `{% attrs %}`

Render component attributes with defaults and class handling.

**Syntax:**
```django
{% attrs [attr=default_value] [class="classes"] [class:condition_class=condition] %}
```

**Features:**
- **Default values**: `{% attrs class="default" %}`
- **Class extension**: `{% attrs class="& additional" %}` (append)
- **Class prepending**: `{% attrs class="base &" %}` (prepend)
- **Conditional classes**: `{% attrs class:active=is_active %}`
- **Grouped attributes**: `{% attrs.group attr=value %}`

### Template Filters

#### `|not`

Negate boolean values, useful for conditional classes.

**Syntax:**
```django
{{ value|not }}
```

**Example:**
```html
<include:button class:disabled="{{ enabled|not }}">
    Click me
</include:button>
```

## HTML Component Syntax

### Component Tags

**Syntax:**
```html
<include:component-name [attributes]>
    [content]
    [<content:block-name>content</content:block-name>]
</include:component-name>
```

**Self-closing:**
```html
<include:component-name [attributes] />
```

### Component Discovery

Components are discovered from `templates/components/` directory:

| File Path | Component Tag |
|-----------|---------------|
| `components/card.html` | `<include:card>` |
| `components/forms/field.html` | `<include:forms:field>` |
| `components/ui/button.html` | `<include:ui:button>` |

### Attribute Syntax

**String attributes:**
```html
<include:card title="Hello" class="my-card" />
```

**Variable attributes:**
```html
<include:card title="{{ title }}" user="{{ user }}" />
```

**Shorthand attributes:**
```html
<include:card {title} {user} />
<!-- Equivalent to: title="{{ title }}" user="{{ user }}" -->
```

**Template expressions:**
```html
<include:card 
    title="{% if user %}Welcome {{ user.name }}{% else %}Welcome{% endif %}"
    href="{% url 'profile' user.pk %}"
    class="card {% if featured %}featured{% endif %}"
/>
```

**Conditional classes:**
```html
<include:button class:active="{{ is_active }}" class:disabled="{{ is_disabled }}">
    Click me
</include:button>
```

### Content Blocks

**HTML content syntax:**
```html
<include:card>
    Main content
    <content:header>Header content</content:header>
    <content:footer>Footer content</content:footer>
</include:card>
```

**Mixed syntax:**
```html
<include:card>
    Main content
    <content:header>HTML syntax header</content:header>
    {% contents footer %}Traditional syntax footer{% endcontents %}
</include:card>
```

## Component Props System

### Props Definition

Define component props in template comments:

**Syntax:**
```html
{# props prop1, prop2=default, prop3=value #}
```

**Types of props:**
- **Required**: `title` (no default value)
- **Optional with default**: `visible=True`, `count=0`, `text="default"`
- **Optional without default**: `description=""`, `callback=None`

**Example:**
```html
{# props title, subtitle="", priority="normal", show_meta=True #}
<div class="article priority-{{ priority }}">
    <h1>{{ title }}</h1>
    {% if subtitle %}<h2>{{ subtitle }}</h2>{% endif %}
    <div>{{ contents }}</div>
    {% if show_meta %}
        <footer>Priority: {{ priority }}</footer>
    {% endif %}
</div>
```

### Enum Props

Define props with allowed values:

**Syntax:**
```html
{# props variant=primary,secondary,danger #}
```

**Optional enums (start with empty value):**
```html
{# props size=,small,medium,large #}
```

**Usage:**
```html
<!-- Single value -->
<include:button variant="primary">Click me</include:button>

<!-- Multiple values (space-separated) -->
<include:button variant="primary large">Big Primary Button</include:button>
```

**Generated variables for single value (`variant="primary"`):**
- `variant` - The prop value (`"primary"`)
- `variantPrimary` - Boolean (`True`)
- `variantSecondary` - Boolean (`False`)

**Generated variables for multiple values (`variant="primary large"`):**
- `variant` - The full value (`"primary large"`)
- `variantPrimary` - Boolean (`True`)
- `variantLarge` - Boolean (`True`)
- Other boolean flags remain `False`

### Attrs Variable

Undefined attributes are collected in `attrs`:

**Access methods:**
- `{{ attrs }}` - Render all attributes as HTML
- `{{ attrs.attrName }}` - Access individual attribute (camelCase)
- `{% attrs %}` - Render with defaults and class handling
- `{% attrs.group %}` - Render grouped attributes

**Kebab-case conversion:**
```html
<!-- Usage -->
<include:card data-user-id="123" my-custom-attr="value" />

<!-- In component -->
{# props #}
<div data-id="{{ attrs.dataUserId }}" custom="{{ attrs.myCustomAttr }}">
    {{ contents }}
</div>
```

## Template Engine Features

### Multi-line Template Tags

The custom template engine supports multi-line template tags:

```django
{% if 
    user.is_authenticated 
    and user.is_staff 
    and user.has_perm('myapp.view_admin')
%}
    Admin content
{% endif %}

{% includecontents "complex-component.html"
    title="Long Title Here"
    description="A very long description that spans multiple lines"
    data=complex_data_structure
%}
    Content
{% endincludecontents %}
```

### Auto-loaded Template Tags

When using the custom template engine, these tags are automatically available:
- `includecontents`
- `contents`  
- `wrapif`, `wrapelif`, `wrapelse`
- `attrs`
- `not` filter

No need to use `{% load includecontents %}`.

## Configuration

### Template Engine Settings

Replace Django's default template backend:

```python
TEMPLATES = [
    {
        'BACKEND': 'includecontents.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]
```

### Traditional Setup

Without the custom engine, add to `INSTALLED_APPS`:

```python
INSTALLED_APPS = [
    # ... other apps
    'includecontents',
]
```

Then load tags in templates:
```django
{% load includecontents %}
```

## Context Variables

### Available in Components

Components have access to these automatic context variables:

- `contents` - Main content block
- `contents.block_name` - Named content blocks  
- `attrs` - Undefined attributes object
- `csrf_token` - CSRF token (when available in parent context)
- Any explicitly passed props/attributes

### Context Isolation

Components run in isolated context:
- Parent template variables are NOT inherited
- Only explicitly passed variables are available
- Ensures predictable, reusable components

## Error Handling

### Common Errors

**TemplateDoesNotExist:**
```
Template 'components/nonexistent.html' does not exist
```

**TemplateSyntaxError (missing required prop):**
```
Missing required prop 'title' for component 'card'
```

**TemplateSyntaxError (invalid enum value):**
```
Invalid value 'invalid' for enum prop 'variant'. Must be one of: primary, secondary, danger
```

**TemplateSyntaxError (malformed component):**
```
Invalid component syntax: unclosed tag 'include:card'
```

### Debug Tips

1. **Check component file exists** in `templates/components/`
2. **Verify required props** are provided
3. **Check enum values** match defined options
4. **Validate HTML syntax** in component usage
5. **Use Django's template debugging** for detailed error info

## Performance Notes

- **Template caching**: Components benefit from Django's template caching
- **Context isolation**: Minimal overhead for creating isolated contexts
- **Attribute parsing**: Parsed once during template compilation
- **Content rendering**: Similar performance to standard `{% include %}` tags

## Compatibility

- **Django**: 3.2+ (LTS), 4.0+, 4.1+, 4.2+ (LTS), 5.0+
- **Python**: 3.8+, 3.9+, 3.10+, 3.11+, 3.12+
- **Template engines**: Works with Django's template system

The custom template engine is fully compatible with Django's standard template features and can be used as a drop-in replacement.