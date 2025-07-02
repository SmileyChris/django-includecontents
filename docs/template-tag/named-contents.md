# Named Contents Blocks

Named contents blocks allow you to pass multiple content sections to a single component, enabling more complex and flexible component designs.

## Basic Syntax

```django
{% load includecontents %}
{% includecontents "template.html" %}
    Default content goes here
    {% contents section_name %}Named content goes here{% endcontents %}
{% endincludecontents %}
```

In the included template, access the content using:
- `{{ contents }}` for the default content
- `{{ contents.section_name }}` for named sections

## Simple Example

**templates/components/card.html**
```html
<div class="card">
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
```django
{% load includecontents %}
{% includecontents "components/card.html" %}
    <p>This is the main card content.</p>
    {% contents footer %}
        <button class="btn">Action</button>
    {% endcontents %}
{% endincludecontents %}
```

**Result:**
```html
<div class="card">
    <div class="card-body">
        <p>This is the main card content.</p>
    </div>
    <div class="card-footer">
        <button class="btn">Action</button>
    </div>
</div>
```

## Multiple Named Sections

You can define multiple named content sections:

**templates/components/article.html**
```html
<article class="article">
    {% if contents.header %}
        <header class="article-header">
            {{ contents.header }}
        </header>
    {% endif %}
    
    <main class="article-body">
        {{ contents }}
    </main>
    
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

**Usage:**
```django
{% includecontents "components/article.html" %}
    {% contents header %}
        <h1>Article Title</h1>
        <p class="meta">Published on {{ article.date }}</p>
    {% endcontents %}
    
    <p>This is the main article content...</p>
    <p>Multiple paragraphs are supported.</p>
    
    {% contents sidebar %}
        <h3>Related Articles</h3>
        <ul>
            <li><a href="#">Article 1</a></li>
            <li><a href="#">Article 2</a></li>
        </ul>
    {% endcontents %}
    
    {% contents footer %}
        <p>Share this article:</p>
        <div class="social-buttons">...</div>
    {% endcontents %}
{% endincludecontents %}
```

## Conditional Content Blocks

Use Django's template conditionals to handle optional content blocks:

**templates/components/modal.html**
```html
<div class="modal">
    {% if contents.header %}
        <div class="modal-header">
            {{ contents.header }}
            <button class="close">&times;</button>
        </div>
    {% endif %}
    
    <div class="modal-body">
        {{ contents }}
    </div>
    
    {% if contents.footer %}
        <div class="modal-footer">
            {{ contents.footer }}
        </div>
    {% else %}
        <div class="modal-footer">
            <button class="btn btn-default">Close</button>
        </div>
    {% endif %}
</div>
```

## HTML Content Syntax Alternative

If you're using the custom template engine, you can use HTML-style syntax for named content blocks:

=== "HTML Content Syntax"

    ```html
    <include:article>
        <content:header>
            <h1>Article Title</h1>
            <p class="meta">Published on {{ article.date }}</p>
        </content:header>
        
        <p>This is the main article content...</p>
        
        <content:sidebar>
            <h3>Related Articles</h3>
            <ul>
                <li><a href="#">Article 1</a></li>
            </ul>
        </content:sidebar>
    </include:article>
    ```

=== "Traditional Syntax"

    ```django
    {% includecontents "components/article.html" %}
        {% contents header %}
            <h1>Article Title</h1>
            <p class="meta">Published on {{ article.date }}</p>
        {% endcontents %}
        
        <p>This is the main article content...</p>
        
        {% contents sidebar %}
            <h3>Related Articles</h3>
            <ul>
                <li><a href="#">Article 1</a></li>
            </ul>
        {% endcontents %}
    {% endincludecontents %}
    ```

Both syntaxes are equivalent and can be mixed within the same project.

## Nested Content Blocks

Content blocks can contain Django template logic and even other components:

```django
{% includecontents "components/dashboard.html" %}
    <h1>Welcome, {{ user.name }}!</h1>
    
    {% contents widgets %}
        {% for widget in user.widgets %}
            {% includecontents "components/widget.html" widget=widget %}
                {{ widget.content }}
            {% endincludecontents %}
        {% endfor %}
    {% endcontents %}
    
    {% contents footer %}
        Last login: {{ user.last_login|date:"M d, Y" }}
    {% endcontents %}
{% endincludecontents %}
```

## Best Practices

### 1. Document Expected Content Blocks

Add comments to your component templates to document expected content blocks:

```html
<!-- 
Component: Article Layout
Expected content blocks:
- header (optional): Article title and meta information
- contents (required): Main article content
- sidebar (optional): Related links or additional info
- footer (optional): Social sharing buttons
-->
<article class="article">
    <!-- ... component template ... -->
</article>
```

### 2. Provide Sensible Defaults

Always provide fallbacks for optional content blocks:

```html
<div class="card">
    <div class="card-header">
        {% if contents.header %}
            {{ contents.header }}
        {% else %}
            <h3>Default Title</h3>
        {% endif %}
    </div>
    <div class="card-body">
        {{ contents }}
    </div>
</div>
```

### 3. Keep Block Names Semantic

Use descriptive names that clearly indicate the purpose:

```django
{% contents header %}...{% endcontents %}          <!-- ✅ Good -->
{% contents sidebar_content %}...{% endcontents %} <!-- ✅ Good -->
{% contents block1 %}...{% endcontents %}         <!-- ❌ Avoid -->
{% contents x %}...{% endcontents %}              <!-- ❌ Avoid -->
```

### 4. Consider Order and Layout

The order of content blocks in your usage doesn't need to match the order in the component template:

```django
{% includecontents "card.html" %}
    {% contents footer %}Footer comes first in the code{% endcontents %}
    
    Main content comes after, but renders first in the card
    
    {% contents header %}Header comes last in code{% endcontents %}
{% endincludecontents %}
```

## Common Patterns

### Layout Components

```html
<!-- templates/components/two-column.html -->
<div class="row">
    <div class="col-md-8">
        {{ contents }}
    </div>
    <div class="col-md-4">
        {{ contents.sidebar }}
    </div>
</div>
```

### Form Components

```html
<!-- templates/components/form-field.html -->
<div class="form-group">
    {% if contents.label %}
        <label>{{ contents.label }}</label>
    {% endif %}
    
    {{ contents }}
    
    {% if contents.help %}
        <small class="form-text">{{ contents.help }}</small>
    {% endif %}
    
    {% if contents.errors %}
        <div class="invalid-feedback">{{ contents.errors }}</div>
    {% endif %}
</div>
```

### Navigation Components

```html
<!-- templates/components/nav-section.html -->
<div class="nav-section">
    <h3 class="nav-title">{{ contents.title }}</h3>
    <ul class="nav-list">
        {{ contents }}
    </ul>
    {% if contents.footer %}
        <div class="nav-footer">{{ contents.footer }}</div>
    {% endif %}
</div>
```

## Next Steps

- Learn about the [Wrapif Tag](wrapif-tag.md) for conditional wrapping
- Explore [HTML Component Syntax](../components/html-syntax.md) for a modern alternative
- Check out [Component Patterns](../advanced/component-patterns.md) for advanced usage