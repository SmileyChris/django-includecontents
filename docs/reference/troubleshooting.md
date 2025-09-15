# Troubleshooting

Common issues and solutions when working with Django IncludeContents.

## Template Errors

### TemplateDoesNotExist

**Error:**
```
TemplateDoesNotExist: components/my-component.html
```

**Causes and Solutions:**

1. **Component file doesn't exist:**
   ```bash
   # Check if the file exists
   ls templates/components/my-component.html
   ```
   **Solution:** Create the component file in the correct location.

2. **Incorrect file path:**
   ```html
   <!-- ❌ Wrong -->
   <include:my_component>
   
   <!-- ✅ Correct -->
   <include:my-component>
   ```
   **Solution:** Use kebab-case and ensure the filename matches.

3. **Missing components directory:**
   ```bash
   # Create the directory
   mkdir -p templates/components
   ```

4. **Template engine not configured:**
   ```python
   # settings.py - Ensure you have the right backend
   TEMPLATES = [{
       'BACKEND': 'includecontents.django.Engine',  # For HTML syntax
       # OR
       'BACKEND': 'django.template.backends.django.DjangoTemplates',  # For template tags
   }]
   ```

### TemplateSyntaxError

**Error:**
```
TemplateSyntaxError: Invalid block tag: 'includecontents'
```

**Solution:** Load the template tag library:
```django
{% load includecontents %}
{% includecontents "components/card.html" %}
    Content
{% endincludecontents %}
```

**Error:**
```
TemplateSyntaxError: Malformed template tag at token 'includecontents'
```

**Common causes:**

1. **Missing template name:**
   ```django
   <!-- ❌ Wrong -->
   {% includecontents %}
       Content
   {% endincludecontents %}
   
   <!-- ✅ Correct -->
   {% includecontents "components/card.html" %}
       Content
   {% endincludecontents %}
   ```

2. **Incorrect attribute syntax:**
   ```html
   <!-- ❌ Wrong -->
   <include:card title=Hello World>
   
   <!-- ✅ Correct -->
   <include:card title="Hello World">
   ```

## Component Issues

### Empty Component Content

**Problem:** Component renders but shows no content.

**Debug steps:**

1. **Check props are being passed:**
   ```html
   <!-- Debug template: templates/components/debug-card.html -->
   {# props title, content="" #}
   <div>
       <p>Title: "{{ title }}"</p>
       <p>Content: "{{ content }}"</p>
       <p>Contents: "{{ contents }}"</p>
   </div>
   ```

2. **Verify context isolation:**
   ```html
   <!-- Parent template -->
   {% with message="Hello" %}
       <!-- ❌ Wrong: message not passed -->
       <include:greeting>Welcome</include:greeting>
       
       <!-- ✅ Correct: message passed explicitly -->
       <include:greeting message="{{ message }}">Welcome</include:greeting>
   {% endwith %}
   ```

3. **Check for typos in variable names:**
   ```html
   <!-- ❌ Wrong -->
   <include:card titel="Hello">  <!-- typo: titel -->
   
   <!-- ✅ Correct -->
   <include:card title="Hello">
   ```

### Missing Required Attributes

**Error:**
```
TemplateSyntaxError: Missing required attribute "title" in <include:card>
```

**Solution:** Provide all required attributes:
```html
<!-- Component definition -->
{# props title, description="" #}

<!-- ❌ Wrong: missing required title -->
<include:card description="A card">Content</include:card>

<!-- ✅ Correct: title provided -->
<include:card title="My Card" description="A card">Content</include:card>
```

### Variable Not Found in Component

**Problem:** Variables show as empty in component templates.

**Debugging:**

1. **Check context isolation:**
   ```html
   <!-- Parent template -->
   <h1>{{ page_title }}</h1>  <!-- Works in parent -->
   
   <include:card>
       <h2>{{ page_title }}</h2>  <!-- Empty in component! -->
   </include:card>
   ```

2. **Solution - pass variables explicitly:**
   ```html
   <include:card page-title="{{ page_title }}">
       <h2>{{ page_title }}</h2>  <!-- Still empty -->
       <h2>{{ page-title }}</h2>  <!-- Works! -->
   </include:card>
   ```

## HTML Syntax Issues

### HTML Components Not Working

**Problem:** HTML component syntax doesn't work, shows as literal text.

**Check your template engine:**
```python
# settings.py
TEMPLATES = [{
    'BACKEND': 'includecontents.django.Engine',  # Required for HTML syntax
    'DIRS': [BASE_DIR / 'templates'],
    'APP_DIRS': True,
    # ...
}]
```

**Common issues:**

1. **Wrong template engine:**
   ```python
   # ❌ Won't work for HTML syntax
   'BACKEND': 'django.template.backends.django.DjangoTemplates'
   
   # ✅ Required for HTML syntax
   'BACKEND': 'includecontents.django.Engine'
   ```

2. **File not in components directory:**
   ```
   templates/
   ├── my-card.html          # ❌ Won't work
   └── components/
       └── my-card.html      # ✅ Works
   ```

### Self-Closing Tags Not Working

**Problem:**
```html
<include:icon name="star" />  <!-- Doesn't work -->
```

**Solution:** Ensure proper self-closing syntax:
```html
<!-- ✅ Correct -->
<include:icon name="star" />

<!-- ❌ Wrong - missing space before / -->
<include:icon name="star"/>
```

## Performance Issues

### Slow Template Rendering

**Problem:** Templates render slowly with many components.

**Solutions:**

1. **Enable template caching:**
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

2. **Avoid heavy computation in components:**
   ```html
   <!-- ❌ Slow: complex calculations in template -->
   {# props user #}
   {% for post in user.posts.all %}
       {% for comment in post.comments.select_related.all %}
           <!-- Complex nested queries -->
       {% endfor %}
   {% endfor %}
   
   <!-- ✅ Fast: pass computed data -->
   {# props user, user_stats #}
   <div>Posts: {{ user_stats.post_count }}</div>
   <div>Comments: {{ user_stats.comment_count }}</div>
   ```

3. **Use conditional rendering:**
   ```html
   {# props user, load_heavy_content=False #}
   <div class="user-profile">
       <h1>{{ user.name }}</h1>
       
       {% if load_heavy_content %}
           <include:user-activity-feed user="{{ user }}" />
       {% endif %}
   </div>
   ```

## Development Issues

### Component Changes Not Reflected

**Problem:** Component template changes don't appear in browser.

**Solutions:**

1. **Disable template caching during development:**
   ```python
   # settings.py (development only)
   if DEBUG:
       TEMPLATES[0]['OPTIONS']['loaders'] = [
           'django.template.loaders.filesystem.Loader',
           'django.template.loaders.app_directories.Loader',
       ]
   ```

2. **Clear template cache:**
   ```bash
   # Restart development server
   python manage.py runserver
   
   # Or clear cache programmatically
   python manage.py shell
   >>> from django.template.loader import get_template
   >>> get_template.cache_clear()
   ```

3. **Check file paths:**
   ```bash
   # Ensure you're editing the right file
   find . -name "my-component.html" -type f
   ```

### IDE Not Recognizing Components

**Problem:** No syntax highlighting or autocomplete for components.

**Solutions:**

1. **VS Code setup:**
   ```json
   // .vscode/settings.json
   {
       "emmet.includeLanguages": {
           "django-html": "html"
       },
       "files.associations": {
           "*.html": "django-html"
       }
   }
   ```

2. **Configure file associations:**
   - Associate `.html` files with Django HTML language mode
   - Install Django extensions for your IDE

## Error Debugging

### Enhanced Error Messages

Django IncludeContents provides enhanced error messages with additional context to help debug issues faster.

#### Props Validation Errors

Modern validation errors include comprehensive context:

```python
# Example enhanced error output (Python 3.11+):
TemplateSyntaxError: Props validation failed: email: Enter a valid email address
Component: components/user-card.html
Props class: UserCardProps
  • email: Enter a valid email address
  • age: Cannot convert 'abc' to integer

# On older Python versions, context is included in the main error message
```

**Common validation error types:**

1. **Missing required props:**
   ```
   Props validation failed: Missing required prop: title
   Component: components/card.html
   Props class: CardProps
   ```

2. **Type coercion failures:**
   ```
   Props validation failed: age: Cannot convert 'not-a-number' to integer
   Component: components/user-profile.html
   Props class: UserProfileProps
     • Field: age
     • Expected type: int
     • Received value: 'not-a-number' (type: str)
     • Hint: Ensure the value is a valid integer
   ```

3. **Validation errors:**
   ```
   Props validation failed: email: Enter a valid email address
   Component: components/contact-form.html
   Props class: ContactFormProps
     • email: Enter a valid email address
   ```

#### Debug Component Registration

Use registry introspection helpers to debug component lookup issues:

```python
from includecontents.props import list_registered_components, resolve_props_class_for

# Check what components are registered
components = list_registered_components()
print("Available components:", components)

# Debug path resolution
props_class = resolve_props_class_for('components/my-component.html')
if props_class:
    print(f"Found props class: {props_class.__name__}")
else:
    print("No props class found - check registration")
```

#### Debug Logging

Enable debug logging to see detailed component lookup information:

```python
# settings.py
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'includecontents.props': {
            'handlers': ['console'],
            'level': 'DEBUG',
        },
        'includecontents.templatetags.includecontents': {
            'handlers': ['console'],
            'level': 'DEBUG',
        },
    },
}
```

**Debug log output examples:**

```
# Props cache operations
DEBUG: Props cache hit for template components/card.html (key: props title...)
DEBUG: Props cached for template components/button.html (key: props text..., 2 props)

# Registry lookup failures
DEBUG: No props class found for component 'card'. Tried candidates:
['components/card.html', '/app/templates/components/card.html', 'card.html'].
Registered components (first 5): ['components/button.html', 'components/form.html']

# Registry collisions
WARNING: Component already registered for 'components/button.html'.
Previous: ButtonProps, New: DuplicateButtonProps (keeping first)
```

### Enable Debug Mode

**Template debugging:**
```python
# settings.py
DEBUG = True
TEMPLATES[0]['OPTIONS']['debug'] = True
```

**Verbose error output:**
```python
# Add to component template for debugging
{# props title, description="" #}
<div>
    <h1>DEBUG: title="{{ title }}"</h1>
    <p>DEBUG: description="{{ description }}"</p>
    <div>DEBUG: contents="{{ contents }}"</div>
</div>
```

### Common Error Patterns

**1. Context variable naming:**
```html
<!-- ❌ Wrong: underscore vs hyphen confusion -->
<include:user-card user_name="{{ user.name }}">  <!-- prop: user_name -->
<!-- Component expects: {{ user-name }} not {{ user_name }} -->

<!-- ✅ Correct: consistent naming -->
<include:user-card user-name="{{ user.name }}">  <!-- prop: user-name -->
<!-- Component uses: {{ user-name }} -->
```

**2. Quote handling:**
```html
<!-- ❌ Wrong: nested quotes -->
<include:card title="Say "Hello"">

<!-- ✅ Correct: escaped quotes -->
<include:card title="Say &quot;Hello&quot;">

<!-- ✅ Alternative: different quote types -->
<include:card title='Say "Hello"'>
```

## Getting Help

### Before Asking for Help

1. **Check this troubleshooting guide**
2. **Enable debug mode**
3. **Create a minimal reproduction case**
4. **Check recent changes to your templates**

### When Reporting Issues

Include this information:

1. **Django IncludeContents version:**
   ```bash
   pip show django-includecontents
   ```

2. **Django version:**
   ```bash
   python manage.py version
   ```

3. **Template engine configuration:**
   ```python
   # From settings.py
   TEMPLATES = [...]
   ```

4. **Minimal code example:**
   ```html
   <!-- Component template -->
   {# props title #}
   <div>{{ title }}</div>
   
   <!-- Usage -->
   <include:my-component title="Test">
   ```

5. **Full error traceback:**
   ```
   Traceback (most recent call last):
   ...
   ```

### Community Resources

- **[GitHub Issues](https://github.com/SmileyChris/django-includecontents/issues)**: Bug reports and feature requests
- **[Documentation](../index.md)**: Complete feature documentation
- **[Examples](../getting-started/quickstart.md)**: Working code examples

## Prevention Tips

### Best Practices to Avoid Issues

1. **Use consistent naming conventions**
2. **Document component props clearly**
3. **Test components in isolation**
4. **Keep components simple and focused**
5. **Use template debugging during development**

### Regular Maintenance

1. **Update Django IncludeContents regularly**
2. **Run tests after updates**
3. **Review component usage patterns**
4. **Clean up unused components**

## Still Having Issues?

If this guide doesn't solve your problem:

1. **[Search existing issues](https://github.com/SmileyChris/django-includecontents/issues)**
2. **[Create a new issue](https://github.com/SmileyChris/django-includecontents/issues/new)** with:
   - Clear problem description
   - Minimal reproduction steps
   - Environment details
   - Error messages or unexpected behavior