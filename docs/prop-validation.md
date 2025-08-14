# Component Props Validation

django-includecontents now supports type-safe component props with validation using Django's validators. This provides better developer experience, runtime validation, and IDE support for your components.

## Quick Start

### Template-Based Props (Simple)

Define typed props directly in your component template using the enhanced `{# props #}` syntax:

```django
{# templates/components/user-card.html #}
{# props name:text email:email age:int(min=18) role:choice(admin,user,guest)=user #}

<div class="user-card">
    <h3>{{ name }}</h3>
    <p>Email: {{ email }}</p>
    <p>Age: {{ age }}</p>
    <span class="badge">{{ role }}</span>
</div>
```

### Python-Based Props (Advanced)

For complex components, define props using Python dataclasses with full type hints:

```python
# myapp/component_props.py
from dataclasses import dataclass
from typing import Optional
from includecontents.prop_types import Text, Email, Integer, Choice
from includecontents.props import component

@component('components/user-profile.html')
@dataclass
class UserProfileProps:
    # Required props
    name: Text(max_length=100)
    email: Email
    age: Integer(min=18, max=120)
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

- `Text(max_length=None, min_length=None, pattern=None)` - String with optional validation
- `Integer(min=None, max=None)` - Integer with optional bounds
- `Decimal(max_digits=None, decimal_places=None, min=None, max=None)` - Precise decimal numbers
- `bool` - Boolean values (automatically converts string inputs)

### Pre-configured Types

- `Email` - Validates email addresses
- `Url` - Validates URLs
- `Slug` - Validates slug strings
- `IPAddress` - Validates IPv4 addresses
- `IPv6Address` - Validates IPv6 addresses

### Component-Specific Types

- `Choice['option1', 'option2', ...]` - Restricted string choices (like Literal)
- `CssClass()` - Validates CSS class names
- `Color(format='hex')` - Validates CSS colors (hex, rgb, rgba)
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
{# props name?:type #}                   {# Optional typed prop #}
{# props name:type=default #}            {# Prop with default value #}
```

### Type Parameters

```django
{# props 
   title:text(max_length=100)
   age:int(min=18,max=120)
   role:choice(admin,user,guest)
   email:email
#}
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
from includecontents.prop_types import Text, Email
from includecontents.props import component

@component('components/contact-card.html')
@dataclass
class ContactCardProps:
    name: Text(min_length=2)
    email: Email
    phone: Optional[str] = None
```

### With Custom Validation

```python
@component('components/password-form.html')
@dataclass
class PasswordFormProps:
    password: Text(min_length=8)
    confirm_password: Text(min_length=8)
    
    def clean(self):
        """Cross-field validation."""
        if self.password != self.confirm_password:
            raise ValidationError("Passwords don't match")
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
{# props title:text message:text type:choice(info,warning,error)=info #}
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
{# props title:text variant:choice(primary,secondary,danger) #}
```

### From Plain Attributes

```django
{# Before - no validation #}
{% includecontents "components/card.html" title=title %}

{# After - with validation #}
{# In card.html: #}
{# props title:text(max_length=100) #}
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

### Props class not found

Ensure your props module is imported (e.g., in your app's `__init__.py` or `apps.py`).

### Type coercion failing

Some types require specific string formats. Check the prop type documentation.

## Summary

The prop validation system provides:

- ✅ **Type safety** - Catch errors at render time
- ✅ **Django integration** - Uses familiar Django validators
- ✅ **Progressive enhancement** - Start simple, add validation as needed
- ✅ **Backward compatible** - Existing components continue to work
- ✅ **IDE support** - Full autocomplete and type checking with Python props
- ✅ **Component-focused** - Types designed for UI components, not forms/models