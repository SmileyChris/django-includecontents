# Component Patterns

Real-world patterns and best practices for building maintainable, reusable components with Django IncludeContents.

## Component Design Patterns

### Dynamic Templates

Components can dynamically choose which template to render based on props:

```html
{# props template_type=card,list,grid, item #}
{% if template_type == "card" %}
    {% includecontents "components/item-card.html" item=item %}
        {{ contents }}
    {% endincludecontents %}
{% elif template_type == "list" %}
    {% includecontents "components/item-list.html" item=item %}
        {{ contents }}
    {% endincludecontents %}
{% elif template_type == "grid" %}
    {% includecontents "components/item-grid.html" item=item %}
        {{ contents }}
    {% endincludecontents %}
{% endif %}
```

### Conditional Components

Render components only when certain conditions are met:

```html
{# props user, show_admin=False #}
<div class="user-profile">
    <include:user-avatar user="{{ user }}" />
    
    {% if show_admin and user.is_staff %}
        <include:admin-panel user="{{ user }}" />
    {% endif %}
    
    {% if user.is_premium %}
        <include:premium-badge />
    {% endif %}
</div>
```

## Component Design Patterns

### Container Components

Components that provide layout structure and manage child components:

**templates/components/page-layout.html**
```html
{# props title, breadcrumbs=[] #}
<!DOCTYPE html>
<html>
<head>
    <title>{{ title }} - My Site</title>
</head>
<body>
    <header>
        <nav>
            {% if breadcrumbs %}
                <ol class="breadcrumb">
                    {% for crumb in breadcrumbs %}
                        <li><a href="{{ crumb.url }}">{{ crumb.title }}</a></li>
                    {% endfor %}
                </ol>
            {% endif %}
        </nav>
    </header>
    
    <main>
        {% if contents.header %}
            <div class="page-header">
                {{ contents.header }}
            </div>
        {% endif %}
        
        <div class="page-content">
            {{ contents }}
        </div>
        
        {% if contents.sidebar %}
            <aside class="sidebar">
                {{ contents.sidebar }}
            </aside>
        {% endif %}
    </main>
    
    {% if contents.footer %}
        <footer>
            {{ contents.footer }}
        </footer>
    {% endif %}
</body>
</html>
```

**Usage:**
```html
<include:page-layout title="Dashboard" breadcrumbs="{{ breadcrumbs }}">
    <content:header>
        <h1>Welcome to Dashboard</h1>
    </content:header>
    
    <p>Main dashboard content...</p>
    
    <content:sidebar>
        <include:navigation-menu items="{{ menu_items }}" />
    </content:sidebar>
</include:page-layout>
```

### Presentational Components

Pure display components that receive all data via props:

**templates/components/user-avatar.html**
```html
{# props user, size=medium,small,large, show_status=False #}
<div {% attrs 
    class="avatar"
    class:avatar-small=sizeSmall
    class:avatar-medium=sizeMedium
    class:avatar-large=sizeLarge
%}>
    {% if user.avatar %}
        <img src="{{ user.avatar.url }}" alt="{{ user.get_full_name }}">
    {% else %}
        <div class="avatar-placeholder">
            {{ user.first_name.0|upper }}{{ user.last_name.0|upper }}
        </div>
    {% endif %}
    
    {% if show_status and user.is_online %}
        <span class="status-indicator online"></span>
    {% endif %}
</div>
```

### Composite Components

Components that combine multiple smaller components:

**templates/components/article-card.html**
```html
{# props article, show_excerpt=True, show_meta=True, show_actions=False #}
<article {% attrs class="card article-card" %}>
    {% if article.featured_image %}
        <div class="card-image">
            <img src="{{ article.featured_image.url }}" alt="{{ article.title }}">
        </div>
    {% endif %}
    
    <div class="card-content">
        <header class="article-header">
            <h2><a href="{{ article.get_absolute_url }}">{{ article.title }}</a></h2>
            
            {% if show_meta %}
                <div class="article-meta">
                    <include:user-avatar 
                        user="{{ article.author }}" 
                        size="small" 
                    />
                    <span class="author">{{ article.author.get_full_name }}</span>
                    <time datetime="{{ article.published_at|date:'c' }}">
                        {{ article.published_at|date:"M d, Y" }}
                    </time>
                </div>
            {% endif %}
        </header>
        
        {% if show_excerpt and article.excerpt %}
            <div class="article-excerpt">
                {{ article.excerpt|truncatewords:30 }}
            </div>
        {% endif %}
        
        {% if article.tags.exists %}
            <div class="article-tags">
                {% for tag in article.tags.all %}
                    <include:tag name="{{ tag.name }}" url="{{ tag.get_absolute_url }}" />
                {% endfor %}
            </div>
        {% endif %}
    </div>
    
    {% if show_actions %}
        <footer class="card-actions">
            {{ contents.actions }}
        </footer>
    {% endif %}
</article>
```

## Form Components

### Field Components

**templates/components/forms/text-field.html**
```html
{# props 
    name, 
    label="", 
    type=text,email,password,tel,url,
    required=False,
    placeholder="",
    help_text="",
    value="",
    errors=[]
#}
<div {% attrs 
    class="form-group"
    class:has-error=errors
%}>
    {% if label %}
        <label for="{{ name }}" class="form-label">
            {{ label }}
            {% if required %}<span class="required" aria-label="required">*</span>{% endif %}
        </label>
    {% endif %}
    
    <input {% attrs.input
        type=type
        name=name
        id=name
        value=value
        placeholder=placeholder
        required=required
        class="form-control"
        class:is-invalid=errors
        aria-describedby="{{ name }}-help {{ name }}-errors"
    %}>
    
    {% if help_text %}
        <small id="{{ name }}-help" class="form-help">{{ help_text }}</small>
    {% endif %}
    
    {% if errors %}
        <div id="{{ name }}-errors" class="invalid-feedback">
            {% for error in errors %}
                <div>{{ error }}</div>
            {% endfor %}
        </div>
    {% endif %}
</div>
```

### Form Integration

**templates/components/forms/django-field.html**
```html
{# props field, show_label=True, show_help=True #}
<include:forms:text-field
    name="{{ field.name }}"
    label="{% if show_label %}{{ field.label }}{% endif %}"
    type="{{ field.widget.input_type|default:'text' }}"
    required="{{ field.field.required }}"
    value="{{ field.value|default:'' }}"
    help_text="{% if show_help %}{{ field.help_text }}{% endif %}"
    errors="{{ field.errors }}"
    placeholder="{{ field.field.widget.attrs.placeholder|default:'' }}"
    {# Pass through any additional attributes #}
    {% for attr, value in field.field.widget.attrs.items %}
        {% if attr != 'placeholder' %}{{ attr }}="{{ value }}"{% endif %}
    {% endfor %}
/>
```

## Data Display Patterns

### Table Components

**templates/components/data-table.html**
```html
{# props items=[], columns=[], actions=[], empty_message="No data available" #}
<div {% attrs class="table-container" %}>
    {% if items %}
        <table class="table">
            <thead>
                <tr>
                    {% for column in columns %}
                        <th {% if column.sortable %}class="sortable"{% endif %}>
                            {{ column.label }}
                        </th>
                    {% endfor %}
                    {% if actions %}
                        <th class="actions-column">Actions</th>
                    {% endif %}
                </tr>
            </thead>
            <tbody>
                {% for item in items %}
                    <tr>
                        {% for column in columns %}
                            <td>
                                {% if column.template %}
                                    {% include column.template with item=item %}
                                {% else %}
                                    {{ item|lookup:column.field|default:"-" }}
                                {% endif %}
                            </td>
                        {% endfor %}
                        {% if actions %}
                            <td class="actions">
                                {% for action in actions %}
                                    <include:button
                                        variant="{{ action.variant|default:'secondary' }}"
                                        size="small"
                                        href="{{ action.url_pattern|format:item.pk }}"
                                    >
                                        {{ action.label }}
                                    </include:button>
                                {% endfor %}
                            </td>
                        {% endif %}
                    </tr>
                {% endfor %}
            </tbody>
        </table>
    {% else %}
        <div class="empty-state">
            <p>{{ empty_message }}</p>
            {{ contents.empty }}
        </div>
    {% endif %}
</div>
```

### List Components

**templates/components/article-list.html**
```html
{# props articles, show_featured=True, layout=grid,list #}
<div {% attrs 
    class="article-list"
    class:layout-grid=layoutGrid
    class:layout-list=layoutList
%}>
    {% if show_featured %}
        {% with featured_articles=articles|filter_featured|slice:":3" %}
            {% if featured_articles %}
                <section class="featured-articles">
                    <h2>Featured Articles</h2>
                    <div class="featured-grid">
                        {% for article in featured_articles %}
                            <include:article-card 
                                article="{{ article }}"
                                show_excerpt="true"
                                show_meta="true"
                                class="featured-card"
                            />
                        {% endfor %}
                    </div>
                </section>
            {% endif %}
        {% endwith %}
    {% endif %}
    
    {% with regular_articles=articles|exclude_featured %}
        {% if regular_articles %}
            <section class="regular-articles">
                {% if show_featured %}<h2>Latest Articles</h2>{% endif %}
                <div class="article-grid">
                    {% for article in regular_articles %}
                        <include:article-card 
                            article="{{ article }}"
                            show_excerpt="true"
                            show_meta="true"
                        />
                    {% endfor %}
                </div>
            </section>
        {% endif %}
    {% endwith %}
    
    {% if not articles %}
        <div class="empty-state">
            {{ contents.empty }}
        </div>
    {% endif %}
</div>
```

## Navigation Patterns

### Menu Components

**templates/components/navigation/menu.html**
```html
{# props items=[], orientation=horizontal,vertical, current_url="" #}
<nav {% attrs 
    class="menu"
    class:menu-horizontal=orientationHorizontal
    class:menu-vertical=orientationVertical
%}>
    <ul class="menu-list">
        {% for item in items %}
            <li class="menu-item">
                {% if item.children %}
                    <details class="submenu">
                        <summary class="menu-link">
                            {{ item.title }}
                            <span class="menu-indicator">▼</span>
                        </summary>
                        <include:navigation:menu 
                            items="{{ item.children }}"
                            orientation="vertical"
                            current_url="{{ current_url }}"
                            class="submenu-list"
                        />
                    </details>
                {% else %}
                    <a href="{{ item.url }}" 
                       class="menu-link {% if item.url == current_url %}active{% endif %}"
                       {% if item.external %}target="_blank" rel="noopener"{% endif %}>
                        {% if item.icon %}
                            <include:icon name="{{ item.icon }}" size="16" />
                        {% endif %}
                        {{ item.title }}
                    </a>
                {% endif %}
            </li>
        {% endfor %}
    </ul>
</nav>
```

### Breadcrumb Components

**templates/components/navigation/breadcrumbs.html**
```html
{# props items=[], separator="/" #}
{% if items %}
    <nav {% attrs class="breadcrumb" %} aria-label="Breadcrumb">
        <ol class="breadcrumb-list">
            {% for item in items %}
                <li class="breadcrumb-item {% if forloop.last %}current{% endif %}">
                    {% if not forloop.last %}
                        <a href="{{ item.url }}">{{ item.title }}</a>
                        <span class="breadcrumb-separator" aria-hidden="true">{{ separator }}</span>
                    {% else %}
                        <span aria-current="page">{{ item.title }}</span>
                    {% endif %}
                </li>
            {% endfor %}
        </ol>
    </nav>
{% endif %}
```

## Modal and Dialog Patterns

### Modal Components

**templates/components/ui/modal.html**
```html
{# props id, title="", size=medium,small,large,fullscreen, closable=True #}
<div {% attrs 
    class="modal fade"
    class:modal-sm=sizeSmall
    class:modal-lg=sizeLarge
    class:modal-xl=sizeFullscreen
    id=id
    tabindex="-1"
    aria-labelledby="{{ id }}-title"
    aria-hidden="true"
%}>
    <div class="modal-dialog">
        <div class="modal-content">
            {% if title or closable %}
                <header class="modal-header">
                    {% if title %}
                        <h2 id="{{ id }}-title" class="modal-title">{{ title }}</h2>
                    {% endif %}
                    {% if closable %}
                        <button type="button" 
                                class="modal-close" 
                                data-bs-dismiss="modal" 
                                aria-label="Close">
                            <span aria-hidden="true">&times;</span>
                        </button>
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
</div>
```

**Usage:**
```html
<include:ui:modal id="confirm-delete" title="Confirm Deletion" size="small">
    <p>Are you sure you want to delete this item? This action cannot be undone.</p>
    
    <content:footer>
        <include:button variant="secondary" data-bs-dismiss="modal">
            Cancel
        </include:button>
        <include:button variant="danger" id="confirm-delete-btn">
            Delete
        </include:button>
    </content:footer>
</include:ui:modal>
```

## Responsive Patterns

### Responsive Grid

**templates/components/layout/responsive-grid.html**
```html
{# props 
    cols_xs=1, cols_sm=2, cols_md=3, cols_lg=4, cols_xl=6,
    gap=medium,small,large,
    items=[]
#}
<div {% attrs 
    class="responsive-grid"
    class:gap-small=gapSmall
    class:gap-medium=gapMedium
    class:gap-large=gapLarge
    style="--cols-xs: {{ cols_xs }}; --cols-sm: {{ cols_sm }}; --cols-md: {{ cols_md }}; --cols-lg: {{ cols_lg }}; --cols-xl: {{ cols_xl }};"
%}>
    {% if items %}
        {% for item in items %}
            <div class="grid-item">
                {{ contents.item }}
            </div>
        {% endfor %}
    {% else %}
        {{ contents }}
    {% endif %}
</div>
```

**CSS:**
```css
.responsive-grid {
    display: grid;
    grid-template-columns: repeat(var(--cols-xs), 1fr);
}

@media (min-width: 576px) {
    .responsive-grid {
        grid-template-columns: repeat(var(--cols-sm), 1fr);
    }
}

@media (min-width: 768px) {
    .responsive-grid {
        grid-template-columns: repeat(var(--cols-md), 1fr);
    }
}

@media (min-width: 992px) {
    .responsive-grid {
        grid-template-columns: repeat(var(--cols-lg), 1fr);
    }
}

@media (min-width: 1200px) {
    .responsive-grid {
        grid-template-columns: repeat(var(--cols-xl), 1fr);
    }
}
```

## Error Handling Patterns

### Error Boundary Components

**templates/components/ui/error-boundary.html**
```html
{# props title="Something went wrong", show_details=False, error=None #}
<div {% attrs class="error-boundary" %}>
    <div class="error-content">
        <h2 class="error-title">{{ title }}</h2>
        
        {{ contents }}
        
        {% if show_details and error %}
            <details class="error-details">
                <summary>Technical Details</summary>
                <pre><code>{{ error }}</code></pre>
            </details>
        {% endif %}
        
        {% if contents.actions %}
            <div class="error-actions">
                {{ contents.actions }}
            </div>
        {% endif %}
    </div>
</div>
```

### Conditional Components

**templates/components/ui/conditional.html**
```html
{# props condition, fallback="" #}
{% if condition %}
    {{ contents }}
{% else %}
    {% if fallback %}
        {{ fallback }}
    {% elif contents.fallback %}
        {{ contents.fallback }}
    {% endif %}
{% endif %}
```

**Usage:**
```html
<include:ui:conditional condition="{{ user.is_authenticated }}">
    <p>Welcome back, {{ user.name }}!</p>
    
    <content:fallback>
        <p><a href="{% url 'login' %}">Please log in</a></p>
    </content:fallback>
</include:ui:conditional>
```

## Performance Patterns

### Lazy Loading Components

**templates/components/ui/lazy-load.html**
```html
{# props src="", placeholder="Loading...", threshold="0.1" #}
<div {% attrs 
    class="lazy-container"
    data-src=src
    data-threshold=threshold
%}>
    <div class="lazy-placeholder">
        {{ placeholder }}
    </div>
    <div class="lazy-content" style="display: none;">
        {{ contents }}
    </div>
</div>

<script>
document.addEventListener('DOMContentLoaded', function() {
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const container = entry.target;
                const placeholder = container.querySelector('.lazy-placeholder');
                const content = container.querySelector('.lazy-content');
                
                placeholder.style.display = 'none';
                content.style.display = 'block';
                
                observer.unobserve(container);
            }
        });
    }, { threshold: parseFloat(container.dataset.threshold) });
    
    document.querySelectorAll('.lazy-container').forEach(container => {
        observer.observe(container);
    });
});
</script>
```

### Cached Components

Use Django's template fragment caching:

```html
{# props cache_key, cache_timeout=3600 #}
{% load cache %}
{% cache cache_timeout cache_key %}
    {{ contents }}
{% endcache %}
```

## Testing Patterns

### Component Testing

```python
from django.test import TestCase
from django.template import Template, Context

class ComponentTestCase(TestCase):
    def render_component(self, template_string, context=None):
        """Helper to render component templates"""
        template = Template(template_string)
        return template.render(Context(context or {}))
    
    def test_button_component(self):
        html = self.render_component(
            '<include:button variant="primary">Click me</include:button>'
        )
        self.assertIn('btn btn-primary', html)
        self.assertIn('Click me', html)
    
    def test_required_props(self):
        with self.assertRaises(TemplateSyntaxError):
            self.render_component('<include:card>No title</include:card>')
```

## Best Practices Summary

### 1. Component Composition

```html
<!-- ✅ Good: Compose from smaller components -->
<include:article-card article="{{ article }}">
    <content:actions>
        <include:button variant="primary" href="{{ article.edit_url }}">
            Edit
        </include:button>
        <include:button variant="danger" data-confirm="true">
            Delete
        </include:button>
    </content:actions>
</include:article-card>
```

### 2. Props Validation

```html
<!-- ✅ Good: Clear prop requirements -->
{# props article, show_actions=False #}
{% if not article %}
    <div class="error">Article is required</div>
{% else %}
    <!-- Component content -->
{% endif %}
```

### 3. Consistent Naming

```html
<!-- ✅ Good: Consistent naming patterns -->
<include:forms:text-field />
<include:forms:email-field />
<include:forms:select-field />

<!-- ❌ Avoid: Inconsistent naming -->
<include:text-input />
<include:email-field />
<include:dropdown />
```

### 4. Documentation

Document component APIs clearly:

```html
{#
Component: Article Card
Purpose: Display article summary with optional actions
Props:
  - article (required): Article object with title, excerpt, author
  - show_excerpt (optional, default=True): Whether to show article excerpt
  - show_meta (optional, default=True): Whether to show author and date
  - show_actions (optional, default=False): Whether to show action buttons
Content blocks:
  - actions: Action buttons (only shown if show_actions=True)
Example:
  <include:article-card article="{{ article }}" show_actions="true">
    <content:actions>
      <include:button href="/edit/">Edit</include:button>
    </content:actions>
  </include:article-card>
#}
```

## Next Steps

- Review [CSS Classes](../components/css-classes.md) for styling patterns
- Check [Integration Guides](../integration/prettier.md) for development setup
- Explore the [API Reference](../api-reference.md) for complete syntax details