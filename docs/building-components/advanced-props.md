# Advanced Props

Advanced prop features including enum validation, complex prop types, and sophisticated validation patterns.

## Enum Props

Define props with a limited set of allowed values for better validation and developer experience.

### Basic Enum Syntax

```html
{# props variant=primary,secondary,danger #}
<button {% attrs class="btn btn-{{ variant }}" %}>
    {{ contents }}
</button>
```

**Usage:**
```html
<include:button variant="primary">Save</include:button>
<include:button variant="danger">Delete</include:button>
```

### Generated Boolean Variables

When an enum prop is set, the component receives both the value and boolean flags:

```html
{# props variant=primary,secondary,danger #}
<button {% attrs 
    class="btn" 
    class:btn-primary=variantPrimary 
    class:btn-secondary=variantSecondary 
    class:btn-danger=variantDanger 
%}>
    {{ contents }}
</button>
```

**Context variables created:**
- `variant` - The prop value (`"primary"`)
- `variantPrimary` - Boolean (`True` when variant="primary")
- `variantSecondary` - Boolean (`False` when variant="primary")
- `variantDanger` - Boolean (`False` when variant="primary")

### Optional Enums

Start with an empty value to make the enum optional:

```html
{# props size=,small,medium,large #}
<div {% attrs class="box" class:box-small=sizeSmall class:box-medium=sizeMedium class:box-large=sizeLarge %}>
    {{ contents }}
</div>
```

**Usage:**
```html
<!-- No size specified - uses empty default -->
<include:box>Default size content</include:box>

<!-- Explicit size -->
<include:box size="large">Large content</include:box>
```

### Kebab-Case Enum Values

Enum values with hyphens are converted to camelCase for boolean variables:

```html
{# props theme=light-mode,dark-mode,high-contrast #}
<div {% attrs 
    class="container" 
    class:light-theme=themeLightMode 
    class:dark-theme=themeDarkMode 
    class:high-contrast=themeHighContrast 
%}>
    {{ contents }}
</div>
```

## Complex Props

### Default Value Types

Props support various default value types:

```html
{# props 
    title="",
    count=0,
    rating=4.5,
    enabled=True,
    disabled=False,
    callback=None,
    items=[]
#}
```

### Dynamic Defaults

Use template expressions for dynamic defaults:

```html
{# props user, show_avatar=True, avatar_size="medium" #}
{% if user.is_premium %}
    {% with default_size="large" %}
        <!-- Use premium default -->
    {% endwith %}
{% endif %}
```

## Validation Patterns

### Required Prop Validation

Components automatically validate required props:

```html
{# props title, author, content #}
<!-- Will raise TemplateSyntaxError if any required prop is missing -->
```

### Custom Validation

Add validation logic in your component:

```html
{# props count=0 #}
{% if count < 0 %}
    <div class="error">Count cannot be negative</div>
{% elif count > 100 %}
    <div class="error">Count too large (max 100)</div>
{% else %}
    <div class="counter">{{ count }}</div>
{% endif %}
```

### Type Checking

While Django templates don't enforce strict typing, you can add checks:

```html
{# props items=[] #}
{% if items|length_is:"0" %}
    <p class="empty">No items to display</p>
{% else %}
    <ul>
        {% for item in items %}
            <li>{{ item }}</li>
        {% endfor %}
    </ul>
{% endif %}
```

## Advanced Examples

### Multi-Variant Component

```html
{# props 
    variant=primary,secondary,success,warning,danger,
    size=,small,medium,large,
    outline=False,
    disabled=False 
#}
<button {% attrs 
    class="btn"
    class:btn-primary=variantPrimary
    class:btn-secondary=variantSecondary
    class:btn-success=variantSuccess
    class:btn-warning=variantWarning
    class:btn-danger=variantDanger
    class:btn-outline=outline
    class:btn-sm=sizeSmall
    class:btn-lg=sizeLarge
    disabled=disabled
%}>
    {{ contents }}
</button>
```

### Complex Form Component

```html
{# props 
    name,
    label="",
    type=text,email,password,number,tel,url,
    required=False,
    placeholder="",
    help_text="",
    validation_state=,valid,invalid,warning
#}
<div {% attrs 
    class="form-group" 
    class:has-error=validationStateInvalid
    class:has-warning=validationStateWarning
    class:has-success=validationStateValid
%}>
    {% if label %}
        <label for="{{ name }}" class="form-label">
            {{ label }}
            {% if required %}<span class="required">*</span>{% endif %}
        </label>
    {% endif %}
    
    <input {% attrs.input
        type=type
        name=name
        id=name
        placeholder=placeholder
        required=required
        class="form-control"
        class:is-valid=validationStateValid
        class:is-invalid=validationStateInvalid
    %}>
    
    {% if help_text %}
        <small class="form-text">{{ help_text }}</small>
    {% endif %}
    
    {% if contents.errors %}
        <div class="invalid-feedback">{{ contents.errors }}</div>
    {% endif %}
</div>
```

### Theme-Aware Component

```html
{# props 
    theme=auto,light,dark,
    color=blue,red,green,yellow,purple,
    intensity=50,100,200,300,400,500,600,700,800,900
#}
<div {% attrs 
    class="alert"
    class:alert-light=themeLight
    class:alert-dark=themeDark
    class:alert-auto=themeAuto
    class:text-{{ color }}-{{ intensity }}=True
    data-theme=theme
%}>
    {% if themeAuto %}
        <script>
            // Auto theme detection logic
            if (window.matchMedia('(prefers-color-scheme: dark)').matches) {
                this.classList.add('alert-dark');
            } else {
                this.classList.add('alert-light');
            }
        </script>
    {% endif %}
    {{ contents }}
</div>
```

## Error Handling

### Invalid Enum Values

```html
{# props variant=primary,secondary,danger #}
```

**Usage that causes error:**
```html
<include:button variant="invalid">Button</include:button>
```

**Error message:**
```
TemplateSyntaxError: Invalid value 'invalid' for enum prop 'variant'. 
Must be one of: primary, secondary, danger
```

### Missing Required Props

```html
{# props title, content #}
```

**Usage that causes error:**
```html
<include:card title="Hello">Content</include:card>  <!-- Missing 'content' prop -->
```

**Error message:**
```
TemplateSyntaxError: Missing required prop 'content' for component 'card'
```

## Best Practices

### 1. Use Semantic Enum Values

```html
<!-- ✅ Good: Clear meaning -->
{# props status=draft,published,archived #}

<!-- ❌ Avoid: Unclear abbreviations -->
{# props status=d,p,a #}
```

### 2. Provide Sensible Defaults

```html
<!-- ✅ Good: Reasonable defaults -->
{# props variant=primary,secondary, size=medium,small,large, disabled=False #}

<!-- ❌ Avoid: No defaults for optional props -->
{# props variant=primary,secondary, size=medium,small,large #}
```

### 3. Document Complex Props

```html
{# 
props:
  variant (enum): Button style - primary, secondary, danger
  size (enum, optional): Button size - small, medium (default), large  
  loading (bool): Show loading spinner
  href (string, optional): Make button a link
#}
```

### 4. Group Related Enums

```html
{# props 
    text_size=xs,sm,base,lg,xl,2xl,3xl,
    text_weight=thin,light,normal,medium,semibold,bold,black,
    text_color=gray,red,blue,green,yellow,purple
#}
```

### 5. Use Validation for Critical Props

```html
{# props percentage=50 #}
{% if percentage < 0 or percentage > 100 %}
    <div class="error">Percentage must be between 0 and 100</div>
{% else %}
    <div class="progress-bar" style="width: {{ percentage }}%"></div>
{% endif %}
```

## Migration from Simple Props

### Before (Simple Props)

```html
{# props variant="primary", size="medium" #}
<button class="btn btn-{{ variant }} btn-{{ size }}">
    {{ contents }}
</button>
```

### After (Enum Props)

```html
{# props variant=primary,secondary,danger, size=small,medium,large #}
<button {% attrs 
    class="btn"
    class:btn-primary=variantPrimary
    class:btn-secondary=variantSecondary  
    class:btn-danger=variantDanger
    class:btn-small=sizeSmall
    class:btn-medium=sizeMedium
    class:btn-large=sizeLarge
%}>
    {{ contents }}
</button>
```

**Benefits of enum props:**
- **Validation**: Invalid values are caught at render time
- **IDE support**: Better autocomplete and error detection
- **Documentation**: Clear list of allowed values
- **Type safety**: Boolean flags prevent typos in conditionals

## Next Steps

- Learn about [CSS Classes](css-and-styling.md) for advanced styling
- Explore [Component Patterns](../building-components/component-patterns.md) for real-world examples
- Check out the [API Reference](../reference/api-reference.md) for complete syntax details