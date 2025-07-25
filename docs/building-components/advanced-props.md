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

### Multiple Enum Values

You can specify multiple enum values separated by spaces:

```html
{# props variant=primary,secondary,accent,icon,large #}
<button {% attrs 
    class="btn" 
    class:btn-primary=variantPrimary 
    class:btn-secondary=variantSecondary 
    class:btn-accent=variantAccent
    class:btn-icon=variantIcon
    class:btn-large=variantLarge
%}>
    {{ contents }}
</button>
```

**Usage:**
```html
<!-- Single value -->
<include:button variant="primary">Save</include:button>

<!-- Multiple values -->
<include:button variant="primary icon">Save</include:button>
<include:button variant="secondary large">Cancel</include:button>
<include:button variant="accent icon large">Featured</include:button>
```

**Context variables created for `variant="primary icon"`:**
- `variant` - The full value (`"primary icon"`)
- `variantPrimary` - Boolean (`True`)
- `variantIcon` - Boolean (`True`)
- `variantSecondary` - Boolean (`False`)
- `variantAccent` - Boolean (`False`)
- `variantLarge` - Boolean (`False`)

This is particularly useful for combining visual modifiers like size, appearance, and behavior flags.

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

## Attribute Spreading

The `...attrs` syntax allows you to forward undefined attributes from a parent component to child components. This is a powerful feature for creating flexible wrapper components that don't need to explicitly define every possible attribute.

### Basic Spreading

```html
{# components/wrapper.html #}
{# props title #}
<div class="wrapper">
    <h2>{{ title }}</h2>
    <!-- Forward all undefined attrs to the child component -->
    <include:card ...attrs>
        {{ contents }}
    </include:card>
</div>
```

**Usage:**
```html
<include:wrapper 
    title="My Wrapper" 
    class="custom-card" 
    id="card-123"
    data-value="456"
>
    Card content
</include:wrapper>
```

In this example, `class`, `id`, and `data-value` are passed through to the `card` component because they're not defined as props in the wrapper.

### How It Works

1. The parent component receives attributes
2. Defined props are extracted and used by the parent
3. Undefined attributes are collected in the `attrs` variable
4. `...attrs` spreads these undefined attributes to the child component
5. The child merges spread attrs with its own attrs

### Spreading with Props

When spreading attrs to a component that defines props, only the undefined attributes are spread:

```html
{# components/filtered-wrapper.html #}
{# props #}
<div class="wrapper">
    <include:user-card name="John" ...attrs>
        Additional info
    </include:user-card>
</div>

{# components/user-card.html #}
{# props name, role="user" #}
<div {{ attrs }} class="user-card">
    <h3>{{ name }}</h3>
    <span class="role">{{ role }}</span>
    {{ contents }}
</div>
```

**Usage:**
```html
<include:filtered-wrapper 
    name="Jane"
    role="admin" 
    data-id="123"
    class="highlight"
>
</include:filtered-wrapper>
```

Here:
- `name` is explicitly set to "John" in the wrapper (overrides "Jane")
- `role="admin"` flows through attrs to the child
- `data-id` and `class` are spread as undefined attributes

### Spreading Attribute Groups

You can spread specific groups of attributes using the dot notation:

```html
{# components/form.html #}
{# props #}
<form {{ attrs }}>
    {{ contents }}
    <include:submit-button ...attrs.button>
        Submit
    </include:submit-button>
</form>
```

**Usage:**
```html
<include:form 
    method="POST" 
    action="/submit"
    button.type="submit"
    button.class="btn btn-primary"
    button.disabled="{{ is_processing }}"
>
    <input name="email" type="email">
</include:form>
```

Only the `button.*` attributes are spread to the submit button component.

### Precedence Rules

Local attributes take precedence over spread attributes:

```html
{# components/precedence-wrapper.html #}
{# props #}
<div>
    <!-- Local class overrides any class from spread attrs -->
    <include:card ...attrs class="local-override">
        {{ contents }}
    </include:card>
</div>
```

### Practical Examples

#### 1. Layout Wrapper
```html
{# components/section.html #}
{# props title #}
<section class="content-section">
    <h2>{{ title }}</h2>
    <include:content-area ...attrs>
        {{ contents }}
    </include:content-area>
</section>
```

#### 2. Conditional Wrapper
```html
{# components/maybe-link.html #}
{# props href=None #}
{% if href %}
    <a href="{{ href }}" ...attrs>{{ contents }}</a>
{% else %}
    <span ...attrs>{{ contents }}</span>
{% endif %}
```

#### 3. Form Field Wrapper
```html
{# components/field-wrapper.html #}
{# props label, name, required=False #}
<div class="field">
    <label for="{{ name }}">
        {{ label }}
        {% if required %}<span class="required">*</span>{% endif %}
    </label>
    <include:input name="{{ name }}" ...attrs />
    {% if contents.error %}
        <div class="error">{{ contents.error }}</div>
    {% endif %}
</div>
```

#### 4. Multi-Level Component Architecture
```html
{# components/card-header.html #}
{# props title #}
<header {{ attrs }}>
    <h3>{{ title }}</h3>
    {{ contents }}
</header>

{# components/card.html #}
{# props #}
<article class="card">
    <include:card-header ...attrs.header title="{{ attrs.title|default:'Untitled' }}">
        {% if contents.actions %}
            {{ contents.actions }}
        {% endif %}
    </include:card-header>
    <div class="card-body" {{ attrs.body }}>
        {{ contents }}
    </div>
</article>

{# Usage #}
<include:card 
    title="User Profile"
    header.class="bg-primary text-white"
    header.id="profile-header"
    body.class="p-4"
>
    <content:actions>
        <button>Edit</button>
    </content:actions>
    Profile content here...
</include:card>
```

### Best Practices

1. **Use for Wrapper Components**: Spreading is most useful for components that wrap other components

2. **Document Expected Attrs**: Even though attrs are undefined, document common ones:
   ```html
   {# 
   Wrapper component that forwards all attrs to inner card.
   Common attrs: class, id, data-*, aria-*
   #}
   {# props title #}
   ```

3. **Be Explicit When Needed**: Sometimes it's clearer to pass specific attrs:
   ```html
   <!-- Less clear -->
   <include:wrapper ...attrs>
   
   <!-- More clear -->
   <include:wrapper class="{{ class }}" id="{{ id }}">
   ```

4. **Consider Performance**: Spreading attrs has minimal overhead, but avoid deeply nested spreading chains

5. **Type Safety**: Remember that spread attrs bypass prop validation - validate critical attributes when needed

### Advanced Patterns

#### Dynamic Spreading
```html
{# props spread_to="card" #}
{% if spread_to == "wrapper" %}
    <div ...attrs>
        <include:card>{{ contents }}</include:card>
    </div>
{% else %}
    <div>
        <include:card ...attrs>{{ contents }}</include:card>
    </div>
{% endif %}
```

#### Component Chain with Spreading
```html
{# components/themed-card.html #}
{# props theme="light" #}
<div class="theme-{{ theme }}">
    <include:styled-card ...attrs>
        {{ contents }}
    </include:styled-card>
</div>

{# components/styled-card.html #}
{# props bordered=True #}
<div class="styled-wrapper">
    <include:base-card bordered="{{ bordered }}" ...attrs>
        {{ contents }}
    </include:base-card>
</div>
```

## Next Steps

- Learn about [CSS Classes](css-and-styling.md) for advanced styling
- Explore [Component Patterns](../building-components/component-patterns.md) for real-world examples
- Check out the [API Reference](../reference/api-reference.md) for complete syntax details