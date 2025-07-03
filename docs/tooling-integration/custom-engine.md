# Custom Template Engine

Django IncludeContents provides a custom template engine that extends Django's standard template functionality with additional features while maintaining full compatibility.

## Engine Features

The custom template engine (`includecontents.django.DjangoTemplates`) provides:

1. **HTML Component Syntax**: `<include:component>` tags
2. **Multi-line Template Tags**: Break long tags across lines
3. **Auto-loaded Template Tags**: No need for `{% load includecontents %}`
4. **All Standard Django Features**: 100% compatibility with existing templates

## Installation

Replace Django's default template backend in your `settings.py`:

```python
TEMPLATES = [
    {
        'BACKEND': 'includecontents.django.DjangoTemplates',
        'DIRS': [
            BASE_DIR / 'templates',
        ],
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

## Architecture

### Template Processing Pipeline

1. **Template Loading**: Standard Django template loading
2. **Preprocessing**: Convert HTML component syntax to Django tags
3. **Multi-line Processing**: Handle multi-line template tags
4. **Standard Compilation**: Use Django's standard template compiler
5. **Rendering**: Standard Django template rendering

### Component Discovery

The engine automatically discovers components from:

```
templates/
└── components/
    ├── button.html          → <include:button>
    ├── forms/
    │   └── field.html       → <include:forms:field>
    └── ui/
        ├── card.html        → <include:ui:card>
        └── icons/
            └── star.html    → <include:ui:icons:star>
```

### Template Tag Auto-loading

These template tags are automatically available without `{% load %}`:

- `includecontents` / `endincludecontents`
- `contents` / `endcontents`
- `wrapif` / `wrapelif` / `wrapelse` / `endwrapif`
- `attrs`
- `not` filter

## HTML Component Syntax Processing

### Syntax Transformation

The engine transforms HTML component syntax to standard Django tags:

```html
<!-- Input: HTML component syntax -->
<include:card title="Hello" class="my-card">
    <p>Content</p>
    <content:footer>Footer content</content:footer>
</include:card>

<!-- Transformed to: Django template tags -->
{% includecontents "components/card.html" title="Hello" class="my-card" %}
    <p>Content</p>
    {% contents footer %}Footer content{% endcontents %}
{% endincludecontents %}
```

### Attribute Processing

Complex attribute processing handles:

- **String literals**: `title="Hello"`
- **Template variables**: `title="{{ title }}"`
- **Template expressions**: `href="{% url 'home' %}"`
- **Shorthand syntax**: `{title}` → `title="{{ title }}"`
- **Conditional classes**: `class:active="{{ is_active }}"`
- **Boolean attributes**: `disabled` → `disabled="True"`

### Self-closing Components

```html
<!-- Self-closing syntax -->
<include:icon name="star" size="24" />

<!-- Transformed to -->
{% includecontents "components/icon.html" name="star" size="24" %}{% endincludecontents %}
```

## Multi-line Tag Processing

### Line Continuation

The engine handles multi-line template tags by:

1. **Detecting unclosed tags**: Tags that span multiple lines
2. **Concatenating lines**: Join lines until tag is complete
3. **Preserving whitespace**: Maintain proper spacing in output
4. **Error reporting**: Accurate line numbers in error messages

### Example Processing

```django
<!-- Input -->
{% if user.is_authenticated 
    and user.is_staff 
    and user.has_perm('admin')
%}
    Content
{% endif %}

<!-- Processed as -->
{% if user.is_authenticated and user.is_staff and user.has_perm('admin') %}
    Content
{% endif %}
```

## Advanced Features

### Context Processors

The engine supports all standard Django context processors and custom ones:

```python
# settings.py
TEMPLATES = [
    {
        'BACKEND': 'includecontents.django.DjangoTemplates',
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'myapp.context_processors.custom_processor',
            ],
        },
    },
]
```

### Template Loaders

Works with all Django template loaders:

```python
# Custom loader configuration
TEMPLATES = [
    {
        'BACKEND': 'includecontents.django.DjangoTemplates',
        'OPTIONS': {
            'loaders': [
                'django.template.loaders.filesystem.Loader',
                'django.template.loaders.app_directories.Loader',
                ('django.template.loaders.cached.Loader', [
                    'django.template.loaders.filesystem.Loader',
                    'django.template.loaders.app_directories.Loader',
                ]),
            ],
        },
    },
]
```

### Custom Template Tags Integration

Custom template tags work seamlessly:

```python
# myapp/templatetags/custom_tags.py
from django import template

register = template.Library()

@register.simple_tag
def custom_component(**kwargs):
    return render_to_string('components/custom.html', kwargs)
```

```django
<!-- In templates -->
{% load custom_tags %}
<include:card>
    {% custom_component data=my_data %}
</include:card>
```

## Performance Considerations

### Template Caching

- **Preprocessing is cached**: HTML component syntax transformation is cached
- **Standard Django caching**: All Django template caching mechanisms work
- **Development vs Production**: Use cached loader in production

### Memory Usage

- **Minimal overhead**: Engine adds minimal memory overhead
- **Template parsing**: Slightly more parsing for HTML components
- **Context isolation**: Each component gets isolated context (small overhead)

### Optimization Tips

```python
# Production settings
TEMPLATES = [
    {
        'BACKEND': 'includecontents.django.DjangoTemplates',
        'OPTIONS': {
            'loaders': [
                ('django.template.loaders.cached.Loader', [
                    'django.template.loaders.filesystem.Loader',
                    'django.template.loaders.app_directories.Loader',
                ]),
            ],
        },
    },
]
```

## Debugging

### Debug Information

Enable template debugging for detailed error information:

```python
# settings.py
DEBUG = True
TEMPLATES = [
    {
        'BACKEND': 'includecontents.django.DjangoTemplates',
        'OPTIONS': {
            'debug': True,
        },
    },
]
```

### Error Messages

The engine provides enhanced error messages:

```
TemplateSyntaxError: Invalid component syntax in template 'home.html' at line 15:
<include:card title="Hello>
              ^
Expected closing quote for attribute 'title'
```

### Template Source Maps

Line numbers in errors map to original template source:

```
TemplateSyntaxError at /
Missing required prop 'title' for component 'card'
Template: home.html
Line: 23 (original: 23)
Component: components/card.html
```

## Compatibility

### Django Versions

- ✅ Django 3.2 LTS
- ✅ Django 4.0
- ✅ Django 4.1  
- ✅ Django 4.2 LTS
- ✅ Django 5.0

### Third-party Packages

The engine works with popular Django packages:

- **Django REST Framework**: API serialization with component templates
- **Django Crispy Forms**: Form rendering in components
- **Django Compressor**: Asset compression with component assets
- **Django Debug Toolbar**: Full debugging support
- **Django Extensions**: Template debugging tools

### Migration from Standard Engine

Migrating is seamless - all existing templates work unchanged:

```python
# Before
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        # ... rest of config
    },
]

# After
TEMPLATES = [
    {
        'BACKEND': 'includecontents.django.DjangoTemplates',
        # ... same config - everything else unchanged
    },
]
```

## Customization

### Engine Subclassing

Extend the engine for custom behavior:

```python
# myapp/engine.py
from includecontents.django import DjangoTemplates

class CustomEngine(DjangoTemplates):
    def __init__(self, params):
        super().__init__(params)
        # Custom initialization
    
    def get_template(self, template_name):
        # Custom template loading logic
        return super().get_template(template_name)
```

```python
# settings.py
TEMPLATES = [
    {
        'BACKEND': 'myapp.engine.CustomEngine',
        # ... config
    },
]
```

### Custom Component Discovery

Override component path resolution:

```python
class CustomEngine(DjangoTemplates):
    def resolve_component_template(self, component_name):
        # Custom component resolution logic
        if component_name.startswith('admin:'):
            return f'admin/components/{component_name[6:]}.html'
        return super().resolve_component_template(component_name)
```

## Testing

### Unit Testing Templates

Test templates using Django's test client:

```python
from django.test import TestCase
from django.template import Template, Context

class TemplateTest(TestCase):
    def test_component_rendering(self):
        template = Template('<include:card title="Test">Content</include:card>')
        html = template.render(Context({}))
        self.assertIn('Test', html)
        self.assertIn('Content', html)
```

### Integration Testing

Test full template rendering:

```python
from django.test import TestCase, Client

class ComponentIntegrationTest(TestCase):
    def setUp(self):
        self.client = Client()
    
    def test_page_with_components(self):
        response = self.client.get('/page-with-components/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'expected-component-output')
```

## Best Practices

### 1. Gradual Migration

Start using HTML components in new templates:

```html
<!-- New templates: Use HTML component syntax -->
<include:card title="New Feature">
    Modern component syntax
</include:card>

<!-- Existing templates: Keep working as-is -->
{% load includecontents %}
{% includecontents "components/card.html" title="Existing" %}
    Legacy syntax still works
{% endincludecontents %}
```

### 2. Component Organization

Organize components logically:

```
templates/components/
├── ui/              # UI components
│   ├── button.html
│   ├── card.html
│   └── modal.html
├── forms/           # Form components
│   ├── field.html
│   └── fieldset.html
├── layout/          # Layout components
│   ├── header.html
│   ├── footer.html
│   └── sidebar.html
└── content/         # Content components
    ├── article.html
    └── summary.html
```

### 3. Development Workflow

```python
# Development settings
TEMPLATES = [
    {
        'BACKEND': 'includecontents.django.DjangoTemplates',
        'OPTIONS': {
            'debug': True,
            'string_if_invalid': 'INVALID_VARIABLE_%s',
        },
    },
]
```

### 4. Production Configuration

```python
# Production settings
TEMPLATES = [
    {
        'BACKEND': 'includecontents.django.DjangoTemplates',
        'OPTIONS': {
            'debug': False,
            'loaders': [
                ('django.template.loaders.cached.Loader', [
                    'django.template.loaders.filesystem.Loader',
                    'django.template.loaders.app_directories.Loader',
                ]),
            ],
        },
    },
]
```

## Troubleshooting

### Common Issues

**Issue**: Components not found
```
TemplateSyntaxError: Template 'components/button.html' does not exist
```
**Solution**: Ensure component files are in `templates/components/` directory.

**Issue**: Multi-line tags not parsing
```
TemplateSyntaxError: Unclosed tag 'if'
```
**Solution**: Check for missing closing tags or unbalanced parentheses.

**Issue**: HTML syntax not working
```
TemplateSyntaxError: Invalid block tag 'include:card'
```
**Solution**: Verify you're using the custom engine, not standard Django engine.

### Performance Issues

Monitor template rendering performance:

```python
# Add to middleware for debugging
import time
from django.template.response import TemplateResponse

class TemplateTimingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        start_time = time.time()
        response = self.get_response(request)
        
        if isinstance(response, TemplateResponse):
            render_time = time.time() - start_time
            print(f"Template render time: {render_time:.3f}s")
        
        return response
```

## Next Steps

- Learn [Component Patterns](../building-components/component-patterns.md) for advanced usage
- Explore [Integration Guides](../tooling-integration/prettier-formatting.md) for tooling setup
- Check the [API Reference](../reference/api-reference.md) for complete engine details