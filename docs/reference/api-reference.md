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

### `{% icon %}`

Render an icon from the configured icon sprite.

**Syntax:**
```django
{% icon icon_name [attr=value] [use.attr=value] [as variable_name] %}
```

**Parameters:**
- `icon_name`: Name of the icon (string or variable)
- `attr=value`: Attributes for the SVG element
- `use.attr=value`: Attributes for the USE element (prefixed with `use.`)
- `as variable_name`: Store the SVG in a context variable instead of rendering

**Example:**
```django
{% load icons %}
{% icon "home" class="w-6 h-6" %}
{% icon "user" class="avatar" use.role="img" use.aria-label="Profile" %}

{# Store in variable for conditional rendering #}
{% icon "optional-icon" class="w-4 h-4" as my_icon %}
{% if my_icon %}{{ my_icon }}{% endif %}
```

**Generated output:**
```html
<svg class="w-6 h-6"><use href="#home"></use></svg>
<svg class="avatar"><use role="img" aria-label="Profile" href="#user"></use></svg>
```

**Behavior:**
- Invalid/non-existent icons render nothing (empty string)
- With `as variable`: invalid icons store empty string in the variable

### `{% icons_inline %}`

Output the entire SVG sprite sheet inline in the page.

**Syntax:**
```django
{% icons_inline %}
```

**Usage:**
- Use in development mode for immediate icon updates
- Place before closing `</body>` tag for best performance
- Not needed in production when sprites are served as static files

**Example:**
```html
{% load icons %}
<!DOCTYPE html>
<html>
<body>
    <!-- Page content -->
    {% icons_inline %}
</body>
</html>
```


### `{% icon_sprite_url %}`

Get the URL to the generated sprite file.

**Syntax:**
```django
{% icon_sprite_url %}
```

**Usage:**
- Returns the URL in production mode when sprites are on disk
- Returns empty string in development mode
- Useful for preloading or custom sprite loading

**Example:**
```html
{% icon_sprite_url as sprite_url %}
{% if sprite_url %}
    <link rel="preload" href="{{ sprite_url }}" as="image" type="image/svg+xml">
{% endif %}
```

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

### Icon Tags

**Syntax:**
```html
<icon:icon-name [attributes] [use.attributes] />
```

**Parameters:**
- `icon-name`: Name of the configured icon
- `attributes`: Attributes for the SVG element
- `use.attributes`: Attributes for the USE element (prefixed with `use.`)

**Examples:**
```html
<!-- Basic icon -->
<icon:home class="w-6 h-6" />

<!-- With accessibility attributes -->
<icon:user class="avatar" use.role="img" use.aria-label="User profile" />

<!-- With dynamic classes -->
<icon:star class="icon" class:filled="{{ is_favorite }}" />
```

**Generated output:**
```html
<svg class="w-6 h-6"><use href="#mdi-home"></use></svg>
<svg class="avatar"><use role="img" aria-label="User profile" href="#tabler-user"></use></svg>
<svg class="icon filled"><use href="#lucide-star"></use></svg>
```

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
- `icon`, `icons_inline`, `icon_sprite_url` (icon tags)

No need to use `{% load includecontents %}` or `{% load icons %}`.

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

### Icons Configuration

Configure the icons system in your settings:

```python
INCLUDECONTENTS_ICONS = {
    # Required: List of icons to include
    'icons': [
        'mdi:home',                      # Iconify icons
        'tabler:user',
        ('custom-name', 'mdi:house'),    # Custom names with tuples
        'icons/logo.svg',                # Local SVG files from static files
        ('brand', 'logos/company.svg'),
    ],
    
    # Optional: Development mode (default: DEBUG)
    'dev_mode': True,
    
    # Optional: Cache timeout in seconds (default: 3600)
    'cache_timeout': 3600,
    
    # Optional: Iconify API base URL (default: 'https://api.iconify.design')
    'api_base': 'https://api.iconify.design',
}
```

**Icon sources:**
- **Iconify icons**: Use prefix notation like `mdi:home`, `tabler:calendar`
- **Local SVG files**: Place in static directories, reference by path (must end with `.svg`)
- **Custom names**: Use tuples for custom component names

## Context Variables

### Available in Components

Components have access to these automatic context variables:

- `contents` - Main content block
- `contents.block_name` - Named content blocks  
- `attrs` - Undefined attributes object
- Any explicitly passed props/attributes

**Context processor variables are automatically available:**
- `request` - HTTP request object (from `context_processors.request`)
- `user` - Current user (from `context_processors.auth`)
- `csrf_token` - CSRF token (from Django's CSRF middleware)
- Any custom context processor variables

### Context Isolation

Components run in isolated context:
- Parent template variables are NOT inherited
- Only explicitly passed variables are available
- **Exception:** Context processor variables are always available
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
- **Template engines**: Django templates AND Jinja2 templates

### Template Engine Support

| Feature | Django Templates | Jinja2 | Notes |
|---------|-----------------|--------|-------|
| `{% includecontents %}` tag | ✅ Full support | ✅ Full support | Core template tag functionality |
| HTML component syntax (`<include:component>`) | ✅ Full support | ✅ Full support | Via preprocessing in Jinja2 |
| Props system | ✅ Full support | ✅ Full support | Shared props validation system |
| Named content blocks | ✅ Full support | ✅ Full support | `{% contents name %}` syntax |
| Context isolation | ✅ Full support | ✅ Full support | Configurable in Jinja2 |
| Attrs object | ✅ Full support | ✅ Full support | Undefined attribute collection |
| Multi-line tags | ✅ Full support | ✅ Native support | Built into Jinja2 |

!!! success "Dual Template Engine Support"
    Django IncludeContents supports both Django templates and Jinja2 with feature parity! Choose the template engine that best fits your project.

    **Setup guides:**
    - [Django Templates](../getting-started/installation.md#option-1-django-templates-with-custom-engine-recommended)
    - [Jinja2 Templates](../getting-started/jinja2-setup.md)

The custom template engine is fully compatible with Django's standard template features and can be used as a drop-in replacement for `django.template.backends.django.DjangoTemplates`.