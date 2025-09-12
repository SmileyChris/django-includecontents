# Component Props Validation

django-includecontents now supports type-safe component props with validation using Django's validators. This provides better developer experience, runtime validation, and IDE support for your components.

## Quick Start

### Template-Based Props (Simple)

Define typed props directly in your component template using the enhanced `{# props #}` syntax:

```django
{# templates/components/user-card.html #}
{# props name:text email:email age:int[min=18] role:choice[admin,user,guest]=user #}

<div class="user-card">
    <h3>{{ name }}</h3>
    <p>Email: {{ email }}</p>
    <p>Age: {{ age }}</p>
    <span class="badge">{{ role }}</span>
</div>
```

### Python-Based Props (Advanced)

For complex components, define props using Python dataclasses with full type hints.

#### Where to Put Props Classes

Props classes should be placed where they'll be automatically imported when Django starts:

1. **In your app's `props.py` file** (recommended):
   ```python
   # myapp/props.py
   ```
   Then import it in your app's `apps.py`:
   ```python
   # myapp/apps.py
   from django.apps import AppConfig
   
   class MyAppConfig(AppConfig):
       default_auto_field = 'django.db.models.BigAutoField'
       name = 'myapp'
       
       def ready(self):
           # Import props to register them
           from . import props
   ```

2. **In your app's `__init__.py`**:
   ```python
   # myapp/__init__.py
   from .props import *  # Register all props classes
   ```

3. **In any module that's imported at startup** (e.g., models.py, views.py)

#### Example Props Class

```python
# myapp/props.py
from dataclasses import dataclass
from typing import Optional
from includecontents.prop_types import Text, Email, Integer, Choice
from includecontents.props import component

@component('components/user-profile.html')
@dataclass
class UserProfileProps:
    # Required props
    name: Text[{'max_length': 100}]
    email: Email
    age: Integer[{'min': 18, 'max': 120}]
    role: Choice['admin', 'editor', 'viewer']
    
    # Optional props
    bio: Optional[Text] = None
    website: Optional[Url] = None
    verified: bool = False
    
    def clean(self):
        """Custom validation logic."""
        from django.core.exceptions import ValidationError
        if self.role == 'admin' and self.age < 21:
            raise ValidationError("Admins must be 21 or older")
```

## Available Prop Types

The `includecontents.prop_types` module provides component-focused types that leverage Django validators:

### Basic Types

- `Text[{'max_length': 100, 'min_length': 2, 'pattern': r'^[A-Z]'}]` - String with optional validation
- `Integer[{'min': 18, 'max': 120}]` - Integer with optional bounds  
- `Decimal[{'max_digits': 10, 'decimal_places': 2, 'min': 0, 'max': 999.99}]` - Precise decimal numbers
- `bool` - Boolean values (automatically converts string inputs)

### Pre-configured Types

- `Email` - Validates email addresses
- `Url` - Validates URLs
- `Slug` - Validates slug strings
- `IPAddress` - Validates IPv4 addresses
- `IPv6Address` - Validates IPv6 addresses

### Django-Specific Types

- `Model['app.ModelName']` - Validates specific Django model instances
- `Model[ModelClass]` - Validates instances of a model class
- `Model` - Validates any Django model instance
- `QuerySet['app.ModelName']` - Validates QuerySets of a specific model
- `QuerySet[ModelClass]` - Validates QuerySets of a model class
- `QuerySet` - Validates any Django QuerySet
- `User` - Validates instances of the project's user model (AUTH_USER_MODEL)

### Component-Specific Types

- `Choice['option1', 'option2', ...]` - Restricted string choices (like Literal)
- `CssClass[{'pattern': r'^custom-pattern$'}]` - Validates CSS class names (with optional custom pattern)
- `Color['hex']` or `Color['rgb']` or `Color['rgba']` - Validates CSS colors with specific format
- `IconName()` - Validates icon names
- `Html` - Marker for HTML content (will be marked safe)
- `Json` - Validates JSON strings

### Helper Functions

- `MinMax(min, max)` - Integer with min/max bounds
- `Pattern(regex, message)` - String with regex validation

## Template Props Syntax

### Basic Syntax

```django
{# props name:type #}                    {# Required typed prop #}
{# props name?:type #}                   {# Optional typed prop - can be missing or None #}
{# props name:type=default #}            {# Prop with default value (also optional) #}
```

### Default Values

Props with default values are automatically optional. When the prop isn't provided, the default value is used:

#### Literal Defaults

```django
{# String defaults #}
{# props title:str="Welcome" greeting:str=Hello #}

{# Numeric defaults #}
{# props count:int=10 price:float=99.99 percentage:int=-5 #}

{# Boolean defaults #}
{# props active:bool=true enabled:bool=false #}

{# List defaults #}
{# props tags:list[str]=[] categories:list[str]=[news,updates] numbers:list[int]=[1,2,3] #}

{# Choice defaults #}
{# props role:choice[admin,user,guest]=user status:choice[active,inactive]=active #}
```

#### Variable Expression Defaults

For simple variable access, use unquoted syntax:

```django
{# props name:str=user.name theme:str=settings.theme count:int=items.count #}
```

For complex expressions with filters or spaces, use quoted syntax:

```django
{# props title:str="{{ page.title|default:'Untitled' }}" greeting:str="{{ 'Hello ' + user.name }}" #}
```

#### Examples in Context

```django
{# templates/components/notification.html #}
{# props 
   message:str 
   type:choice[info,warning,error,success]=info 
   title:str="{{ message|title }}"
   dismissible:bool=true 
   timeout:int=5000
#}

<div class="notification notification-{{ type }}" 
     {% if dismissible %}data-dismissible="true"{% endif %}
     {% if timeout > 0 %}data-timeout="{{ timeout }}"{% endif %}>
    {% if title %}
        <h4 class="notification-title">{{ title }}</h4>
    {% endif %}
    <p class="notification-message">{{ message }}</p>
</div>
```

Usage examples:

```django
{# Uses all defaults except message #}
{% includecontents "components/notification.html" message="Task completed!" %}{% endincludecontents %}

{# Override some defaults #}
{% includecontents "components/notification.html" 
   message="Error occurred" 
   type="error" 
   dismissible=false %}{% endincludecontents %}

{# Complex default with context variable #}
{% includecontents "components/notification.html" 
   message="Welcome back!" 
   title="{{ user.first_name|default:'User' }}" %}{% endincludecontents %}
```

#### Optional Props

The `?` marker makes a prop optional, allowing it to be:
- Missing from the component call
- Explicitly set to `None`
- Set to any falsey value (empty string, 0, false, etc.)

```django
{# props 
   title:text                      {# Required - must be provided #}
   subtitle?:text                  {# Optional - can be missing #}
   role?:choice[admin,user,guest]  {# Optional choice #}
   tags?:list[str]                 {# Optional list #}
#}
```

### Type Parameters

Use square brackets for type parameters (consistent with Python's typing syntax):

```django
{# props 
   title:text[max_length=100]        {# Text with max length #}
   age:int[min=18,max=120]          {# Integer with bounds #}
   role:choice[admin,user,guest]     {# Choice from options #}
   email:email                        {# Pre-configured email type #}
   author:model[auth.User]           {# Django model instance #}
   articles:queryset[blog.Article]   {# Django QuerySet #}
   tags:list[str]                    {# List of strings #}
#}
```

For simple types without parameters, just use the type name:
```django
{# props name:text email:email age:int active:bool #}
```

### Backward Compatibility

The original props syntax still works:

```django
{# props title #}                        {# Required prop #}
{# props title="Default" #}              {# Prop with default #}
{# props variant=primary,secondary #}     {# Enum prop #}
```

## Python Props Classes

### Basic Example

```python
from dataclasses import dataclass
from typing import Optional
from includecontents.prop_types import Text, Email
from includecontents.props import component

@component('components/contact-card.html')
@dataclass
class ContactCardProps:
    name: Text[{'min_length': 2}]
    email: Email
    phone: Optional[str] = None
```

### With Custom Validation

```python
@component('components/password-form.html')
@dataclass
class PasswordFormProps:
    password: Text[{'min_length': 8}]
    confirm_password: Text[{'min_length': 8}]
    
    def clean(self):
        """Cross-field validation."""
        if self.password != self.confirm_password:
            raise ValidationError("Passwords don't match")
```

### With Django Models and QuerySets

```python
from blog.models import Article

@component('components/author-articles.html')
@dataclass
class AuthorArticlesProps:
    author: User  # Automatically uses the project's user model
    articles: QuerySet[Article]  # or QuerySet['blog.Article']
    show_drafts: bool = False
    
    def clean(self):
        """Ensure articles belong to the author."""
        if self.articles.exclude(author=self.author).exists():
            raise ValidationError("All articles must belong to the author")
```

Or with more flexibility:

```python
@component('components/content-list.html')
@dataclass
class ContentListProps:
    items: QuerySet  # Any QuerySet
    owner: Model  # Any Django model instance
    featured: Model['blog.Article']  # Specific model type
```

In templates:
```django
{# props author:model[auth.User] articles:queryset[blog.Article] #}
<div class="author-section">
    <h2>{{ author.get_full_name }}</h2>
    <ul>
    {% for article in articles %}
        <li>{{ article.title }}</li>
    {% endfor %}
    </ul>
</div>
```

### Using Django Validators Directly

```python
from typing import Annotated
from django.core.validators import RegexValidator, MinLengthValidator

@component('components/custom-input.html')
@dataclass
class CustomInputProps:
    # Use Annotated to attach validators
    username: Annotated[str, RegexValidator(r'^[a-zA-Z0-9_]+$')]
    bio: Annotated[str, MinLengthValidator(10)]
```

### Advanced Validation Patterns

#### Requiring Exactly One of Two Props

Sometimes you need exactly one of two optional props to be provided:

```python
from typing import Optional

@component('components/media-display.html')
@dataclass
class MediaDisplayProps:
    # Either image_url OR video_url must be provided, but not both
    image_url: Optional[str] = None
    video_url: Optional[str] = None
    caption: Optional[str] = None
    
    def clean(self):
        """Ensure exactly one media source is provided."""
        has_image = self.image_url is not None
        has_video = self.video_url is not None
        
        if has_image and has_video:
            raise ValidationError(
                "Provide either image_url or video_url, not both"
            )
        if not has_image and not has_video:
            raise ValidationError(
                "Either image_url or video_url is required"
            )
```

#### Conditional Requirements

Make certain props required based on the value of other props:

```python
@component('components/notification.html')
@dataclass
class NotificationProps:
    type: Choice['info', 'warning', 'error', 'custom']
    message: str
    custom_icon: Optional[str] = None
    custom_color: Optional[str] = None
    
    def clean(self):
        """Custom notifications require icon and color."""
        if self.type == 'custom':
            if not self.custom_icon:
                raise ValidationError(
                    "custom_icon is required when type is 'custom'"
                )
            if not self.custom_color:
                raise ValidationError(
                    "custom_color is required when type is 'custom'"
                )
        elif self.custom_icon or self.custom_color:
            raise ValidationError(
                "custom_icon and custom_color are only allowed when type is 'custom'"
            )
```

## Usage in Templates

Both template-defined and Python-defined props work the same way when using components:

```django
{# Using HTML component syntax #}
<include:user-profile 
    name="Jane Doe"
    email="jane@example.com"
    age="25"
    role="editor" />

{# Using traditional includecontents tag #}
{% includecontents "components/user-profile.html" 
   name="Jane Doe"
   email="jane@example.com"
   age=25
   role="editor" %}
{% endincludecontents %}
```

## Validation Behavior

### When Validation Occurs

Props are validated at template render time, providing immediate feedback during development.

### Error Messages

Validation errors are raised as `TemplateSyntaxError` with clear messages:

- `"Missing required prop: name"`
- `"Invalid value for email: Enter a valid email address"`
- `"age: Ensure this value is greater than or equal to 18"`
- `"role: Must be one of 'admin', 'user', 'guest'"`

### Type Coercion

The system automatically converts string inputs to the appropriate type:

- `"25"` → `25` (for Integer props)
- `"true"` → `True` (for bool props)
- `"4.5"` → `4.5` (for float/Decimal props)

## Best Practices

### When to Use Template Props

Use template-defined props for simple components with basic validation:

```django
{# props title:text message:text type:choice[info,warning,error]=info #}
<div class="alert alert-{{ type }}">
    <h4>{{ title }}</h4>
    <p>{{ message }}</p>
</div>
```

### When to Use Python Props

Use Python props classes for:

1. **Complex validation logic**
2. **Reusable component libraries**
3. **Components needing IDE support**
4. **Cross-field validation**

### Progressive Enhancement

Start simple with template props, then migrate to Python props as needed:

```django
{# Start with this #}
{# props name email #}

{# Enhance to this #}
{# props name:text email:email #}

{# Or migrate to Python for complex cases #}
```

## Migration Guide

### From Original Props

```django
{# Before #}
{# props title variant=primary,secondary,danger #}

{# After - with validation #}
{# props title:text variant:choice[primary,secondary,danger] #}
```

### From Plain Attributes

```django
{# Before - no validation #}
{% includecontents "components/card.html" title=title %}

{# After - with validation #}
{# In card.html: #}
{# props title:text[max_length=100] #}
```

## Advanced Features

### Spread Attributes

Props classes work with the spread syntax:

```python
@component('components/button.html')
@dataclass
class ButtonProps:
    label: Text
    variant: Choice['primary', 'secondary'] = 'primary'
    # Extra attrs will be collected in template's {{ attrs }}
```

### Conditional Props

Use Optional types for conditional rendering:

```python
footer: Optional[Text] = None  # Only render footer if provided
```

### Complex Types

```python
from typing import List, Dict

@dataclass
class AdvancedProps:
    tags: List[str]
    metadata: Dict[str, str]
    items: List[int]
```

#### List Type Coercion

When props are passed from templates, lists often come as comma-separated strings. The validation system automatically handles this:

```python
@dataclass
class TaggedProps:
    tags: List[str]
    ids: List[int]

# All of these work:
# From template: tags="python, django, web"
# From template: ids="1, 2, 3"
# From code: tags=['python', 'django', 'web']
# Single value: tags="single-tag" -> ['single-tag']
```

This makes it easy to use list props in templates:

```django
{% includecontents "components/tagged-item.html" 
   tags="python, django, web"
   ids="1, 2, 3" %}
   Content here
{% endincludecontents %}
```

## Testing Props

### Unit Testing Props Classes

```python
def test_user_props_validation():
    from myapp.component_props import UserProps
    from includecontents.props import validate_props
    
    # Test valid data
    result = validate_props(UserProps, {
        'name': 'John',
        'email': 'john@example.com',
        'age': 25
    })
    assert result['name'] == 'John'
    
    # Test validation error
    with pytest.raises(TemplateSyntaxError):
        validate_props(UserProps, {
            'name': 'John',
            'email': 'invalid-email',
            'age': 25
        })
```

### Testing Components

```python
def test_component_rendering():
    result = render_to_string('test-component.html', {
        'components': [{
            'name': 'John',
            'email': 'john@example.com',
            'age': 25
        }]
    })
    assert 'john@example.com' in result
```

## IDE Support

When using Python props classes, you get:

- **Autocomplete** for prop names
- **Type checking** with mypy/pyright
- **Go to definition** for props classes
- **Refactoring support** for renaming props

## Performance Considerations

- Props validation occurs once per component render
- Validation is lightweight (Django validators are efficient)
- Props classes are cached after first import
- No performance penalty for unused props classes

## Troubleshooting

### "Missing required prop"

Ensure all required props are provided when using the component.

### "Invalid value for prop"

Check that the value matches the expected type and validation rules.

### Props class not found / not being used

If your Python props class isn't being picked up:

1. **Check that the module is imported at startup:**
   ```python
   # In myapp/apps.py
   class MyAppConfig(AppConfig):
       def ready(self):
           from . import props  # Force import
   ```

2. **Verify the template path matches exactly:**
   ```python
   @component('components/user-card.html')  # Must match template path
   ```
   The path should be relative to your template directories.

3. **Check Django's template loading order:**
   If you have multiple apps with the same template path, Django might be loading a different template than expected.

4. **Debug by checking the registry:**
   ```python
   from includecontents.props import _registry
   print(_registry)  # See what's registered
   ```

### Type coercion failing

Some types require specific string formats. Check the prop type documentation.

### Import errors on startup

If you get circular import errors:
- Move props to a separate `props.py` file
- Import props in `AppConfig.ready()` instead of at module level
- Avoid importing views or models in your props file

## Summary

The prop validation system provides:

- ✅ **Type safety** - Catch errors at render time
- ✅ **Django integration** - Uses familiar Django validators
- ✅ **Progressive enhancement** - Start simple, add validation as needed
- ✅ **Backward compatible** - Existing components continue to work
- ✅ **IDE support** - Full autocomplete and type checking with Python props
- ✅ **Component-focused** - Types designed for UI components, not forms/models