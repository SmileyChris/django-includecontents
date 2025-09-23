# Multi-line Template Tags

The custom Django template engine supports multi-line template tags, allowing you to break long tags across multiple lines for better readability and maintainability.

!!! info "Template Engine Support"
    Multi-line template tag support:

    - **Django**: Requires the custom template engine (`includecontents.django.DjangoTemplates`)
    - **Jinja2**: Native support built-in (no configuration needed!)

    Standard Django template engine does not support multi-line tags.

## Basic Multi-line Support

### Standard Django Tags

Break any Django template tag across multiple lines:

```django
{% if 
    user.is_authenticated 
    and user.is_staff 
    and user.has_perm('myapp.view_admin')
%}
    Admin content here
{% endif %}
```

### Complex Conditionals

```django
{% if 
    article.is_published 
    and article.publication_date <= today
    and not article.is_archived
    or user.is_superuser
%}
    <article>{{ article.content }}</article>
{% endif %}
```

### For Loops with Complex Conditions

```django
{% for item in items 
    if item.is_active 
    and item.category in allowed_categories
%}
    <div>{{ item.name }}</div>
{% empty %}
    <p>No active items found</p>
{% endfor %}
```

## IncludeContents Multi-line

### Long Component Calls

```django
{% includecontents "components/complex-card.html"
    title="Very Long Title That Would Make This Line Too Long"
    subtitle="An equally long subtitle with lots of descriptive text"
    author=article.author
    publication_date=article.created_at
    category=article.category
    is_featured=article.featured
    show_meta=True
    show_actions=user.can_edit
%}
    <p>Component content goes here</p>
    
    {% contents sidebar %}
        <h3>Related Articles</h3>
        <ul>
            {% for related in article.related_articles.all %}
                <li><a href="{{ related.get_absolute_url }}">{{ related.title }}</a></li>
            {% endfor %}
        </ul>
    {% endcontents %}
{% endincludecontents %}
```

### Multi-line Wrapif

```django
{% wrapif 
    user.is_authenticated 
    and user.profile.is_complete
    and user.has_perm('articles.view_article'
    then "div" 
    class="authenticated-content"
    data-user-id=user.pk
%}
    Welcome back, {{ user.get_full_name }}!
{% endwrapif %}
```

## Formatting Guidelines

### Indentation

Use consistent indentation to show the structure:

```django
{% if complex_condition_one
    and complex_condition_two
    and complex_condition_three
%}
    {% for item in long_queryset_name.filter(
        status='published'
    ).select_related(
        'author', 'category'
    ).prefetch_related(
        'tags'
    ) %}
        <div class="item">
            {{ item.title }}
        </div>
    {% endfor %}
{% endif %}
```

### Line Breaks

Break at logical points:

```django
<!-- ✅ Good: Break at logical operators -->
{% if user.is_authenticated 
    and user.is_active 
    and user.profile.is_complete
%}

<!-- ✅ Good: Break at parameter boundaries -->
{% includecontents "template.html"
    param_one="value_one"
    param_two="value_two"
    param_three="value_three"
%}

<!-- ❌ Avoid: Random line breaks -->
{% if user.is_authenticated and user.
    is_active and user.profile.is_complete
%}
```

## Real-world Examples

### Complex Form Rendering

```django
{% for field in form.visible_fields %}
    {% includecontents "components/form-field.html"
        field=field
        label=field.label
        help_text=field.help_text
        required=field.field.required
        widget_type=field.widget.__class__.__name__
        css_classes=field.css_classes
        show_label=True
        show_help=True
        show_errors=True
    %}
        {% if field.errors %}
            {% contents errors %}
                {% for error in field.errors %}
                    <div class="error">{{ error }}</div>
                {% endfor %}
            {% endcontents %}
        {% endif %}
        
        {% if field.help_text %}
            {% contents help %}
                <small>{{ field.help_text }}</small>
            {% endcontents %}
        {% endif %}
    {% endincludecontents %}
{% endfor %}
```

### Permission-Based Content

```django
{% wrapif 
    user.is_authenticated
    and user.has_perm('articles.change_article'
    and article.author == user
    or user.is_superuser
    then "div"
    class="editable-content"
    data-edit-url="{% url 'edit_article' article.pk %}"
    data-can-delete="{{ user.has_perm('articles.delete_article')|yesno:'true,false' }}"
%}
    <article>
        <h1>{{ article.title }}</h1>
        <div class="content">{{ article.content|safe }}</div>
        
        <div class="edit-controls">
            <a href="{% url 'edit_article' article.pk %}">Edit</a>
            {% if user.has_perm('articles.delete_article') %}
                <a href="{% url 'delete_article' article.pk %}" class="danger">Delete</a>
            {% endif %}
        </div>
    </article>
{% endwrapif %}
```

### Complex Data Processing

```django
{% with processed_items=items|dictsort:"priority"|slice:":10" %}
    {% if processed_items %}
        {% for item in processed_items %}
            {% includecontents "components/priority-item.html"
                item=item
                show_priority=True
                show_date=item.created_date
                show_author=item.author.get_full_name
                css_class="priority-{{ item.priority|default:'normal' }}"
                is_urgent=item.priority|default:0|add:0|divisibleby:1|yesno:"true,false"
            %}
                {{ item.description|truncatewords:20 }}
                
                {% contents metadata %}
                    <span class="priority">Priority: {{ item.priority }}</span>
                    <span class="date">{{ item.created_date|date:"M d, Y" }}</span>
                    <span class="author">{{ item.author.get_full_name }}</span>
                {% endcontents %}
            {% endincludecontents %}
        {% endfor %}
    {% else %}
        <p class="empty-state">No priority items found.</p>
    {% endif %}
{% endwith %}
```

## Integration with Formatters

### Prettier Integration

The multi-line syntax works well with Prettier's Django template formatting:

```django
<!-- Before formatting -->
{% if user.is_authenticated and user.is_staff and user.has_perm('myapp.view_admin') %}Content{% endif %}

<!-- After Prettier formatting -->
{% if
  user.is_authenticated and
  user.is_staff and
  user.has_perm('myapp.view_admin')
%}
  Content
{% endif %}
```

### Custom Formatting Rules

Configure your editor to format multi-line tags consistently:

```json
// .prettierrc for Django templates
{
  "plugins": ["prettier-plugin-jinja-template"],
  "overrides": [
    {
      "files": ["**/{templates,jinja2}/**/*.html"],
      "options": {
        "parser": "jinja-template",
        "printWidth": 100,
        "tabWidth": 2
      }
    }
  ]
}
```

## Benefits

### Readability

```django
<!-- ❌ Hard to read: Single line -->
{% includecontents "components/complex-card.html" title="Long title here" subtitle="Long subtitle here" author=article.author publication_date=article.created_at category=article.category is_featured=article.featured %}

<!-- ✅ Easy to read: Multi-line -->
{% includecontents "components/complex-card.html"
    title="Long title here"
    subtitle="Long subtitle here"
    author=article.author
    publication_date=article.created_at
    category=article.category
    is_featured=article.featured
%}
```

### Maintainability

```django
<!-- Easy to add/remove/modify parameters -->
{% includecontents "components/user-card.html"
    user=user
    show_avatar=True
    show_bio=True
    show_contact=user.profile.show_contact
    show_social=user.profile.show_social
    <!-- Easy to add: show_badges=True -->
%}
```

### Code Reviews

Multi-line tags make it easier to review changes:

```diff
{% includecontents "components/article.html"
    title=article.title
    author=article.author
+   publication_date=article.created_at
    content=article.content
%}
```

## Limitations

### Parser Constraints

Some complex expressions may need parentheses:

```django
<!-- ✅ Works -->
{% if (user.is_authenticated and user.is_staff)
    or user.is_superuser
%}

<!-- ❌ May not parse correctly -->
{% if user.is_authenticated and user.is_staff
    or user.is_superuser
%}
```

### Template Loader Compatibility

Multi-line tags work with:
- ✅ File system loader
- ✅ App directories loader
- ✅ Cached loader
- ✅ Custom loaders (usually)

## Best Practices

### 1. Use Consistent Indentation

```django
<!-- ✅ Good: Consistent 4-space indentation -->
{% includecontents "template.html"
    param_one="value"
    param_two="value"
    param_three="value"
%}

<!-- ❌ Inconsistent indentation -->
{% includecontents "template.html"
  param_one="value"
    param_two="value"
      param_three="value"
%}
```

### 2. Group Related Parameters

```django
<!-- ✅ Good: Logical grouping -->
{% includecontents "components/user-profile.html"
    user=user
    
    show_avatar=True
    show_bio=True
    show_contact=True
    
    avatar_size="large"
    theme="dark"
%}
```

### 3. Break Long Conditions Logically

```django
<!-- ✅ Good: Break at logical operators -->
{% if user.is_authenticated 
    and user.profile.is_verified
    and user.has_perm('content.view')
%}

<!-- ✅ Good: Group related conditions -->
{% if (user.is_authenticated and user.profile.is_verified)
    and (article.is_published or user.is_author)
%}
```

### 4. Align Similar Elements

```django
<!-- ✅ Good: Aligned parameters -->
{% includecontents "template.html"
    title      = "Article Title"
    author     = article.author
    date       = article.created_at
    category   = article.category
%}
```

## Next Steps

- Learn about [Custom Engine](custom-engine.md) features
- Explore [Component Patterns](../building-components/component-patterns.md) for advanced usage
- Check out [Integration Guides](../tooling-integration/prettier-formatting.md) for formatting setup