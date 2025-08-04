# Basic Concepts

Understanding the core concepts of Django IncludeContents will help you make the most of this powerful component system.

## What are Components?

In Django IncludeContents, **components** are reusable template fragments that can accept content and properties (props). Think of them as custom HTML elements that you can define once and use throughout your templates.

```html
<!-- Instead of repeating this pattern: -->
<div class="card border rounded-lg p-6">
    <h2 class="text-xl font-bold">My Title</h2>
    <p>Some content here...</p>
</div>

<!-- Create a component and use it like this: -->
<include:card title="My Title">
    <p>Some content here...</p>
</include:card>
```

## Two Ways to Use Components

Django IncludeContents offers two syntaxes for the same functionality:

### HTML Syntax (Recommended)

```html
<include:card title="Welcome" class="highlight">
    <p>This looks and feels like HTML!</p>
</include:card>
```

**Benefits:**
- Familiar HTML-like syntax
- Better IDE support and formatting
- Cleaner, more readable templates
- Self-closing tags for simple components

### Template Tag Syntax

```django
{% load includecontents %}
{% includecontents "components/card.html" title="Welcome" class="highlight" %}
    <p>Traditional Django template syntax</p>
{% endincludecontents %}
```

**Benefits:**
- Works with any Django template engine
- Familiar to Django developers
- No setup required

!!! tip "Which Should I Use?"
    We recommend the **HTML syntax** for new projects as it provides a better developer experience. The template tag syntax is perfect for existing projects or when you can't use the custom template engine.

## Component Discovery

Components are automatically discovered from your `templates/components/` directory:

```
templates/
└── components/
    ├── card.html              → <include:card>
    ├── user-profile.html      → <include:user-profile>
    ├── forms/
    │   ├── field.html         → <include:forms:field>
    │   └── button.html        → <include:forms:button>
    └── ui/
        └── modal.html         → <include:ui:modal>
```

**Key Rules:**
- **File paths** map to **component names** using `:` as separators
- **Subdirectories** create **namespaces** (e.g., `forms/field.html` → `forms:field`)
- **Kebab-case filenames** are recommended (e.g., `user-profile.html`)

## Context Isolation

One of the most important concepts in Django IncludeContents is **context isolation**.

### What is Context Isolation?

Unlike Django's standard `{% include %}` tag, components run in an **isolated context**. This means:

- ✅ **Only explicitly passed props are available** in the component
- ❌ **Parent template variables are not automatically inherited**
- ✅ **Django context processors remain available** (like `request`, `user`, `csrf_token`)
- ✅ **Components are predictable and self-contained**

!!! note "Context Processors Exception"
    While parent template variables are isolated, **context processor variables** are automatically available in all components. This includes Django's built-in processors (`request`, `user`, `csrf_token`, etc.) and any custom context processors you've configured.

### Example

**Parent template:**
```django
{% with user_name="John" %}
    <include:greeting name="{{ user_name }}">
        Welcome back!
    </include:greeting>
{% endwith %}
```

**Component (templates/components/greeting.html):**
```html
<div class="greeting">
    <h1>Hello, {{ name }}!</h1>     <!-- ✅ Available: passed as prop -->
    <p>{{ contents }}</p>           <!-- ✅ Available: component content -->
    <p>{{ user_name }}</p>          <!-- ❌ Empty: not passed explicitly -->
    <p>User: {{ user.username }}</p> <!-- ✅ Available: from context processor -->
</div>
```

**Result:**
```html
<div class="greeting">
    <h1>Hello, John!</h1>
    <p>Welcome back!</p>
    <p></p>  <!-- Empty because user_name wasn't passed -->
</div>
```

### Why Context Isolation?

Context isolation provides several benefits:

1. **Predictability**: Components always behave the same way regardless of where they're used
2. **Reusability**: No hidden dependencies on parent template variables
3. **Maintainability**: Clear interface through explicit props
4. **Debugging**: Easier to understand what data a component needs

## Props and Content

Components receive data through two mechanisms:

### Props (Attributes)
Props are named values passed to components:

```html
<include:card title="My Card" size="large" featured>
    Content goes here
</include:card>
```

In the component template, these become variables:
```html
<!-- templates/components/card.html -->
<div class="card {{ size }}">
    <h2>{{ title }}</h2>
    {% if featured %}<span class="badge">Featured</span>{% endif %}
    <div>{{ contents }}</div>
</div>
```

### Content
Content is what goes between the opening and closing component tags:

```html
<include:card>
    This becomes the {{ contents }} variable
</include:card>
```

### Named Content Blocks
For more complex components, you can use named content blocks:

```html
<include:layout-card>
    <content:header>
        <h1>Article Title</h1>
    </content:header>
    
    <p>Main article content...</p>
    
    <content:footer>
        <button>Read More</button>
    </content:footer>
</include:layout-card>
```

## Key Benefits

### 1. **Reusability**
Write once, use everywhere. Components eliminate template duplication.

### 2. **Maintainability**
Change a component's structure in one place, and it updates everywhere it's used.

### 3. **Consistency**
Components ensure consistent styling and behavior across your application.

### 4. **Developer Experience**
HTML-like syntax with IDE support makes template development more enjoyable.

### 5. **Testability**
Components can be tested in isolation, making your templates more reliable.

## Next Steps

Now that you understand the core concepts, you're ready to:

- **[Start using components](../using-components/html-syntax.md)** with the HTML syntax
- **[Learn about props and attributes](../using-components/props-and-attrs.md)** for data passing
- **[Explore component patterns](../building-components/component-patterns.md)** for building reusable components