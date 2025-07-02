# CSS Classes

Advanced CSS class management features including conditional classes, class extension, and utilities for building flexible, styled components.

## Basic Class Handling

### Default Classes

Set default classes that can be overridden:

```html
{# props #}
<div {% attrs class="card border rounded p-4" %}>
    {{ contents }}
</div>
```

**Usage:**
```html
<include:card>Default styling</include:card>
<!-- Output: <div class="card border rounded p-4"> -->

<include:card class="my-custom-card">Custom styling</include:card>
<!-- Output: <div class="my-custom-card"> -->
```

## Class Extension

### Appending Classes

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
<!-- Output: <button class="my-button btn btn-default"> -->
```

### Prepending Classes

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
<!-- Output: <div class="container my-content"> -->
```

### Combining Extension Methods

```html
{# props #}
<article {% attrs class="prose &" class="& max-w-none" %}>
    {{ contents }}
</article>
```

**Usage:**
```html
<include:article class="dark:prose-invert">Article content</include:article>
<!-- Output: <article class="prose dark:prose-invert max-w-none"> -->
```

## Conditional Classes

### Basic Conditional Classes

Use the `class:` prefix for conditional classes based on component props:

```html
{# props active=False, disabled=False #}
<button {% attrs 
    class="btn"
    class:btn-active=active
    class:btn-disabled=disabled
%}>
    {{ contents }}
</button>
```

**Usage:**
```html
<include:button active="true">Active Button</include:button>
<!-- Output: <button class="btn btn-active"> -->
```

### Always-Applied Classes

Omit the condition to always apply a class:

```html
{# props #}
<div {% attrs class="base-class" class:always-applied %}>
    {{ contents }}
</div>
```

### Complex Conditionals

Use component attributes directly for conditional classes:

```html
<include:card 
    title="Hello" 
    class:featured="{{ article.is_featured }}"
    class:urgent="{{ priority == 'high' }}"
>
    Content
</include:card>
```

## Tailwind CSS Integration

### Utility-First Approach

Perfect for Tailwind CSS utility classes:

```html
{# props variant=primary,secondary,danger, size=sm,md,lg #}
<button {% attrs
    class="inline-flex items-center justify-center rounded-md font-medium transition-colors"
    class:bg-blue-600=variantPrimary
    class:bg-gray-600=variantSecondary  
    class:bg-red-600=variantDanger
    class:px-3=sizeSm
    class:py-1.5=sizeSm
    class:text-sm=sizeSm
    class:px-4=sizeMd
    class:py-2=sizeMd
    class:text-base=sizeMd
    class:px-6=sizeLg
    class:py-3=sizeLg
    class:text-lg=sizeLg
%}>
    {{ contents }}
</button>
```

### Responsive Classes

```html
{# props mobile_hidden=False #}
<div {% attrs 
    class="block"
    class:hidden=mobile_hidden
    class:sm:block=mobile_hidden
%}>
    {{ contents }}
</div>
```

### Dark Mode Support

```html
{# props #}
<div {% attrs 
    class="bg-white text-gray-900"
    class="dark:bg-gray-900 dark:text-gray-100"
%}>
    {{ contents }}
</div>
```

## Advanced Patterns

### State-Based Styling

```html
{# props state=loading,success,error,idle #}
<div {% attrs
    class="status-indicator p-4 rounded-lg"
    class:bg-blue-100=stateLoading
    class:text-blue-800=stateLoading
    class:bg-green-100=stateSuccess
    class:text-green-800=stateSuccess
    class:bg-red-100=stateError
    class:text-red-800=stateError
    class:bg-gray-100=stateIdle
    class:text-gray-800=stateIdle
%}>
    {% if stateLoading %}
        <span class="spinner"></span> Loading...
    {% elif stateSuccess %}
        ✅ Success!
    {% elif stateError %}
        ❌ Error occurred
    {% else %}
        ⏸️ Ready
    {% endif %}
</div>
```

### Layout Variants

```html
{# props layout=horizontal,vertical,grid #}
<div {% attrs
    class="container"
    class:flex=layoutHorizontal
    class:space-x-4=layoutHorizontal
    class:flex-col=layoutVertical
    class:space-y-4=layoutVertical
    class:grid=layoutGrid
    class:grid-cols-2=layoutGrid
    class:gap-4=layoutGrid
%}>
    {{ contents }}
</div>
```

### Interactive States

```html
{# props interactive=True, disabled=False #}
<div {% attrs
    class="card p-6 rounded-lg border"
    class:cursor-pointer=interactive
    class:hover:shadow-lg=interactive
    class:hover:border-blue-300=interactive
    class:focus:outline-none=interactive
    class:focus:ring-2=interactive
    class:focus:ring-blue-500=interactive
    class:opacity-50=disabled
    class:cursor-not-allowed=disabled
    tabindex=interactive|yesno:"0,"
%}>
    {{ contents }}
</div>
```

## Component-Specific Patterns

### Form Components

```html
{# props validation_state=,valid,invalid,warning #}
<div {% attrs
    class="form-group mb-4"
    class:has-success=validationStateValid
    class:has-error=validationStateInvalid
    class:has-warning=validationStateWarning
%}>
    <input {% attrs.input
        class="form-control w-full px-3 py-2 border rounded-md"
        class:border-green-500=validationStateValid
        class:border-red-500=validationStateInvalid
        class:border-yellow-500=validationStateWarning
        class:focus:ring-green-500=validationStateValid
        class:focus:ring-red-500=validationStateInvalid
        class:focus:ring-yellow-500=validationStateWarning
    %}>
</div>
```

### Navigation Components

```html
{# props active=False, disabled=False #}
<a {% attrs
    class="nav-link px-3 py-2 rounded-md text-sm font-medium transition-colors"
    class:bg-blue-100=active
    class:text-blue-700=active
    class:text-gray-600=active|not
    class:hover:text-gray-900=active|not
    class:hover:bg-gray-50=active|not
    class:opacity-50=disabled
    class:cursor-not-allowed=disabled
    class:pointer-events-none=disabled
%}>
    {{ contents }}
</a>
```

### Alert Components

```html
{# props 
    variant=info,success,warning,error,
    dismissible=False,
    icon=True 
#}
<div {% attrs
    class="alert p-4 rounded-lg flex items-start space-x-3"
    class:bg-blue-50=variantInfo
    class:border-blue-200=variantInfo
    class:text-blue-800=variantInfo
    class:bg-green-50=variantSuccess
    class:border-green-200=variantSuccess
    class:text-green-800=variantSuccess
    class:bg-yellow-50=variantWarning
    class:border-yellow-200=variantWarning
    class:text-yellow-800=variantWarning
    class:bg-red-50=variantError
    class:border-red-200=variantError
    class:text-red-800=variantError
    class:pr-10=dismissible
%}>
    {% if icon %}
        <span class="flex-shrink-0">
            {% if variantInfo %}ℹ️{% elif variantSuccess %}✅{% elif variantWarning %}⚠️{% elif variantError %}❌{% endif %}
        </span>
    {% endif %}
    
    <div class="flex-1">{{ contents }}</div>
    
    {% if dismissible %}
        <button class="absolute top-2 right-2 text-gray-400 hover:text-gray-600">
            ×
        </button>
    {% endif %}
</div>
```

## Debugging Classes

### Development Helper

Add a debug mode to visualize applied classes:

```html
{# props debug=False #}
<div {% attrs
    class="component"
    class:debug-border=debug
    class:debug-bg=debug
%}>
    {% if debug %}
        <div class="debug-info text-xs text-gray-500 mb-2">
            Classes: {{ attrs.class|default:"none" }}
        </div>
    {% endif %}
    {{ contents }}
</div>
```

### Class Validation

```html
{# props variant=primary,secondary #}
{% if not variantPrimary and not variantSecondary %}
    <div class="error">Invalid variant specified</div>
{% else %}
    <button {% attrs class="btn" class:btn-primary=variantPrimary class:btn-secondary=variantSecondary %}>
        {{ contents }}
    </button>
{% endif %}
```

## Performance Considerations

### Efficient Class Building

```html
<!-- ✅ Good: Conditional classes only when needed -->
{# props large=False, success=False #}
<div {% attrs 
    class="base-class"
    class:large-variant=large
    class:success-variant=success
%}>

<!-- ❌ Avoid: Always evaluating all conditions -->
<div class="base-class {% if large %}large-variant{% endif %} {% if success %}success-variant{% endif %}">
```

### Minimize Class Duplication

```html
<!-- ✅ Good: Shared base classes -->
{# props variant=primary,secondary #}
<button {% attrs
    class="btn px-4 py-2 rounded transition-colors"
    class:bg-blue-600=variantPrimary
    class:bg-gray-600=variantSecondary
%}>

<!-- ❌ Avoid: Repeating common classes -->
<button {% attrs
    class:btn-primary=variantPrimary
    class:btn-secondary=variantSecondary
%}>
<!-- Where btn-primary includes all the base styles repeatedly -->
```

## CSS Framework Integration

### Bootstrap Integration

```html
{# props variant=primary,secondary,success,danger, size=sm,lg #}
<button {% attrs
    class="btn"
    class:btn-primary=variantPrimary
    class:btn-secondary=variantSecondary
    class:btn-success=variantSuccess
    class:btn-danger=variantDanger
    class:btn-sm=sizeSm
    class:btn-lg=sizeLg
%}>
    {{ contents }}
</button>
```

### Bulma Integration

```html
{# props color=primary,info,success,warning,danger, size=small,normal,medium,large #}
<button {% attrs
    class="button"
    class:is-primary=colorPrimary
    class:is-info=colorInfo
    class:is-success=colorSuccess
    class:is-warning=colorWarning
    class:is-danger=colorDanger
    class:is-small=sizeSmall
    class:is-medium=sizeMedium
    class:is-large=sizeLarge
%}>
    {{ contents }}
</button>
```

## Best Practices

### 1. Use Semantic Class Names

```html
<!-- ✅ Good: Semantic naming -->
class:is-featured=featured
class:is-urgent=urgent
class:is-completed=completed

<!-- ❌ Avoid: Generic naming -->
class:red=urgent
class:big=featured
```

### 2. Group Related Classes

```html
<!-- ✅ Good: Logical grouping -->
<div {% attrs
    class="card"
    class:card-elevated=elevated
    class:card-bordered=bordered
    class:card-compact=compact
%}>
```

### 3. Provide Fallbacks

```html
{# props variant=primary,secondary,danger #}
<button {% attrs
    class="btn"
    class:btn-primary=variantPrimary
    class:btn-secondary=variantSecondary
    class:btn-danger=variantDanger
    class:btn-default=variant|default:"primary"
%}>
```

### 4. Document Class Behavior

```html
{#
Component: Button
Classes:
- Base: btn (always applied)
- Variants: btn-primary, btn-secondary, btn-danger
- Sizes: btn-sm, btn-lg (optional)
- States: btn-loading, btn-disabled (conditional)
#}
```

## Next Steps

- Explore [Component Patterns](../advanced/component-patterns.md) for real-world examples
- Check out [Integration Guides](../integration/tailwind.md) for framework-specific setup
- Review the [API Reference](../api-reference.md) for complete class syntax