# Best Practices

Building maintainable, reusable components requires following established patterns and conventions. This guide covers the essential best practices for Django IncludeContents.

## Naming Conventions

### Component Names

Use clear, semantic names that describe the component's purpose:

```html
<!-- ✅ Good: Clear purpose -->
<include:article-summary article="{{ article }}" />
<include:user-avatar user="{{ user }}" size="small" />
<include:product-image product="{{ product }}" />

<!-- ❌ Avoid: Generic names -->
<include:widget data="{{ data }}" />
<include:component type="user" />
<include:item />
```

### Naming Patterns

Follow consistent naming patterns across your application:

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

### File Organization

Organize components logically using directories:

```
templates/components/
├── forms/                    # Form-related components
│   ├── field.html
│   ├── button.html
│   └── select.html
├── ui/                       # UI components
│   ├── modal.html
│   ├── button.html
│   └── icons/
│       ├── chevron.html
│       └── close.html
├── layout/                   # Layout components
│   ├── header.html
│   ├── footer.html
│   └── sidebar.html
└── content/                  # Content components
    ├── article-card.html
    ├── user-profile.html
    └── comment.html
```

## Component Design Principles

### Single Responsibility

Each component should have one clear purpose:

```html
<!-- ✅ Good: Single responsibility -->
<include:product-image product="{{ product }}" />
<include:product-price product="{{ product }}" />
<include:product-rating product="{{ product }}" />

<!-- ❌ Avoid: Too many responsibilities -->
<include:product-everything product="{{ product }}" />
```

### Composition Over Complexity

Build complex components by combining simpler ones:

```html
<!-- ✅ Good: Composed from simple components -->
<include:article-card article="{{ article }}">
    <content:header>
        <include:user-avatar user="{{ article.author }}" size="small" />
        <include:publish-date date="{{ article.published_at }}" />
    </content:header>
    
    <include:article-excerpt content="{{ article.content }}" />
    
    <content:footer>
        <include:tag-list tags="{{ article.tags }}" />
        <include:social-share url="{{ article.url }}" />
    </content:footer>
</include:article-card>
```

### Predictable Interface

Define clear props interfaces using comments:

```html
{# props 
   user - User object (required)
   size - Avatar size: small, medium, large (default: medium)
   show_status - Show online status indicator (default: false)
   clickable - Make avatar clickable (default: false)
#}

<div {% attrs 
    class="avatar avatar-{{ size }}"
    class:avatar-clickable=clickable
%}>
    <!-- Component implementation -->
</div>
```

## Props and Data Handling

### Explicit Props

Always pass data explicitly rather than relying on context:

```html
<!-- ✅ Good: Explicit props -->
<include:user-card user="{{ user }}" show_email="true" />

<!-- ❌ Avoid: Implicit context dependency -->
<include:user-card />  <!-- Assumes 'user' is in context -->
```

### Default Values

Provide sensible defaults for optional props:

```html
{# props title, size=medium, variant=primary, disabled=false #}

<button {% attrs 
    class="btn btn-{{ size }} btn-{{ variant }}"
    class:btn-disabled=disabled
    disabled|yesno="disabled,"
%}>
    {{ title }}
</button>
```

### Data Validation

Use enum props for controlled values:

```html
{# props 
   size - Button size: small, medium, large
   variant - Button style: primary, secondary, danger
#}

{% if size not in "small,medium,large" %}
    {% error "Invalid size. Must be: small, medium, or large" %}
{% endif %}
```

## Component Patterns

### Container Components

Components that manage layout and structure:

```html
{# Container component: templates/components/modal.html #}
{# props title, size=medium, closable=true #}

<div {% attrs class="modal modal-{{ size }}" %}>
    <div class="modal-content">
        {% if title %}
            <header class="modal-header">
                <h2>{{ title }}</h2>
                {% if closable %}
                    <button class="modal-close">&times;</button>
                {% endif %}
            </header>
        {% endif %}
        
        <div class="modal-body">
            {{ contents }}
        </div>
        
        {% if contents.footer %}
            <footer class="modal-footer">
                {{ contents.footer }}
            </footer>
        {% endif %}
    </div>
</div>
```

### Presentational Components

Pure display components with no side effects:

```html
{# Presentational component: templates/components/price-display.html #}
{# props amount, currency=USD, show_symbol=true #}

<span {% attrs class="price" %}>
    {% if show_symbol %}
        <span class="currency-symbol">
            {% if currency == "USD" %}${% elif currency == "EUR" %}€{% endif %}
        </span>
    {% endif %}
    <span class="amount">{{ amount|floatformat:2 }}</span>
</span>
```

### Conditional Components

Components that adapt based on props or context:

```html
{# Conditional component: templates/components/user-greeting.html #}
{# props user, show_avatar=true, show_status=false #}

<div class="user-greeting">
    {% if show_avatar %}
        <include:user-avatar user="{{ user }}" size="small" />
    {% endif %}
    
    <div class="greeting-text">
        {% if user.is_authenticated %}
            <span>Welcome back, {{ user.first_name }}!</span>
            {% if show_status and user.last_login %}
                <small>Last seen {{ user.last_login|timesince }} ago</small>
            {% endif %}
        {% else %}
            <span>Welcome, Guest!</span>
        {% endif %}
    </div>
</div>
```

## Performance Best Practices

### Template Caching

Components benefit from Django's template caching:

```python
# settings.py
TEMPLATES = [{
    'BACKEND': 'includecontents.django.Engine',
    'OPTIONS': {
        'loaders': [
            ('django.template.loaders.cached.Loader', [
                'django.template.loaders.filesystem.Loader',
                'django.template.loaders.app_directories.Loader',
            ]),
        ],
    },
}]
```

### Props Parsing Cache

Template-defined props (using `{# props ... #}` syntax) are automatically cached for performance:

```html
{# props title:str="Default" count:int=0 active:bool=true #}
<div class="my-component">
    <h2>{{ title }}</h2>
    <span>{{ count }}</span>
</div>
```

**How it works:**
- Props definitions are parsed once and cached on the template instance
- Subsequent renders of the same template reuse the cached props structure
- Cache automatically invalidates when the template file is modified
- Provides significant performance improvements for frequently-rendered components

**Debug logging:**
When `DEBUG=True`, you can see cache operations in logs:

```python
# settings.py
LOGGING = {
    'version': 1,
    'handlers': {
        'console': {'class': 'logging.StreamHandler'},
    },
    'loggers': {
        'includecontents.templatetags.includecontents': {
            'handlers': ['console'],
            'level': 'DEBUG',
        },
    },
}
```

This will show cache hits and storage operations in your development logs.

**Note:** This optimization is completely transparent - your components will work exactly the same, just faster.

### Avoid Heavy Logic

Keep components lightweight by avoiding heavy computation:

```html
<!-- ✅ Good: Simple display logic -->
<div class="product-price">
    <span class="original-price">${{ product.original_price }}</span>
    <span class="sale-price">${{ product.sale_price }}</span>
</div>

<!-- ❌ Avoid: Heavy computation in templates -->
<div class="product-analytics">
    <!-- Don't calculate complex metrics in templates -->
</div>
```

### Lazy Loading Content

Use conditional rendering for expensive content:

```html
{# props user, load_recent_activity=false #}

<div class="user-profile">
    <include:user-avatar user="{{ user }}" />
    <h2>{{ user.get_full_name }}</h2>
    
    {% if load_recent_activity %}
        <include:recent-activity user="{{ user }}" />
    {% endif %}
</div>
```

## Testing Components

### Component Testing

Test components in isolation:

```python
# tests/test_components.py
from django.template.loader import render_to_string
from django.test import TestCase

class ComponentTests(TestCase):
    def test_user_avatar_with_image(self):
        user = User.objects.create(
            username='testuser',
            first_name='John',
            last_name='Doe'
        )
        
        result = render_to_string('components/user-avatar.html', {
            'user': user,
            'size': 'large',
            'show_status': True
        })
        
        self.assertIn('avatar-large', result)
        self.assertIn('John Doe', result)
```

### Integration Testing

Test component usage in real templates:

```python
def test_article_page_with_components(self):
    response = self.client.get('/articles/1/')
    self.assertContains(response, 'class="article-card"')
    self.assertContains(response, 'class="user-avatar"')
```

## Documentation

### Component Documentation

Document your components clearly:

```html
{# templates/components/notification-banner.html

   A banner component for displaying notifications to users.
   
   Props:
   - message (required): The notification message to display
   - type: Notification type (info, success, warning, error) - default: info
   - dismissible: Whether the banner can be dismissed - default: true
   - icon: Show an icon with the message - default: true
   
   Example usage:
   <include:notification-banner 
       message="Your changes have been saved!"
       type="success"
       dismissible="true" />
#}

{# props message, type=info, dismissible=true, icon=true #}

<div {% attrs 
    class="notification-banner notification-{{ type }}"
    class:dismissible=dismissible
%}>
    {% if icon %}
        <include:notification-icon type="{{ type }}" />
    {% endif %}
    
    <span class="message">{{ message }}</span>
    
    {% if dismissible %}
        <button class="dismiss-btn">&times;</button>
    {% endif %}
</div>
```

### Style Guide

Maintain a component style guide:

```markdown
# Component Style Guide

## Button Component

### Variants
- Primary: `<include:button variant="primary">Save</include:button>`
- Secondary: `<include:button variant="secondary">Cancel</include:button>`
- Danger: `<include:button variant="danger">Delete</include:button>`

### Sizes
- Small: `<include:button size="small">OK</include:button>`
- Medium: `<include:button size="medium">Submit</include:button>`
- Large: `<include:button size="large">Get Started</include:button>`
```

## Migration and Refactoring

### Gradual Migration

Migrate to components gradually:

1. **Identify patterns**: Find repeated template code
2. **Extract components**: Create components for common patterns
3. **Replace incrementally**: Update templates one at a time
4. **Test thoroughly**: Ensure behavior remains consistent

### Refactoring Large Components

Break down large components:

```html
<!-- Before: Large monolithic component -->
<include:user-dashboard user="{{ user }}" />

<!-- After: Composed from smaller components -->
<include:dashboard-layout>
    <content:header>
        <include:user-profile user="{{ user }}" />
    </content:header>
    
    <include:activity-feed user="{{ user }}" />
    <include:quick-actions user="{{ user }}" />
    
    <content:sidebar>
        <include:user-stats user="{{ user }}" />
        <include:recent-notifications user="{{ user }}" />
    </content:sidebar>
</include:dashboard-layout>
```

## Common Pitfalls

### Avoid These Mistakes

1. **Over-nesting**: Don't create components that are too deeply nested
2. **God Components**: Avoid components that do too many things
3. **Tight Coupling**: Don't make components depend on specific context
4. **Inconsistent Naming**: Stick to established naming conventions
5. **Missing Documentation**: Always document complex components

### Debug Common Issues

1. **Missing Props**: Use `{# props #}` comments to catch missing attributes
2. **Context Issues**: Remember that components have isolated context
3. **Performance**: Profile template rendering if components are slow

## Next Steps

- **[Learn component patterns](../building-components/component-patterns.md)** for advanced architectures
- **[Explore CSS styling](css-and-styling.md)** for component styling
- **[Check the API reference](../reference/api-reference.md)** for complete documentation