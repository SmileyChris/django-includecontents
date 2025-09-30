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

If you are new to component attributes, revisit the [Props & Attrs](using-components/props-and-attrs.md) guide first. For enum helpers, grouped attributes, and additional spreading patterns, keep [Advanced Props](building-components/advanced-props.md) nearby—you will reuse many of those ideas alongside validation.

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
from typing import Annotated, Literal, Optional
from django.core.validators import MaxLengthValidator, MinValueValidator, MaxValueValidator
from includecontents.prop_types import Email, Url
from includecontents.props import component

@component('components/user-profile.html')
@dataclass
class UserProfileProps:
    # Required props with validators
    name: Annotated[str, MaxLengthValidator(100)]
    email: Email
    age: Annotated[int, MinValueValidator(18), MaxValueValidator(120)]
    role: Literal['admin', 'editor', 'viewer']

    # Optional props
    bio: Optional[str] = None
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

### Quick Reference

| Type | Template Syntax | Python Syntax | Description |
|------|----------------|---------------|-------------|
| **Basic Types** |
| `str`/`text` | `name:text` | `name: str` | Basic string values |
| `int` | `age:int` | `age: int` | Integer values |
| `bool` | `active:bool` | `active: bool` | Boolean values |
| `decimal`/`float` | `price:decimal` | `price: Decimal` | Decimal numbers |
| **Validated Basic Types** |
| String with validation | `name:text[max_length=100]` | `name: Annotated[str, MaxLengthValidator(100)]` | String with max length |
| Integer with bounds | `age:int[min=18,max=120]` | `age: Annotated[int, MinValueValidator(18), MaxValueValidator(120)]` | Integer with min/max |
| Decimal with bounds | `price:decimal[min=0,max=999.99]` | `price: Annotated[Decimal, MinValueValidator(0), MaxValueValidator(Decimal('999.99'))]` | Decimal with bounds |
| **Validated String Types** |
| `Email` | `email:email` | `email: Email` | Email address validation |
| `Url` | `website:url` | `website: Url` | URL validation |
| `Slug` | `permalink:slug` | `permalink: Slug` | URL slug validation |
| `UnicodeSlug` | `name:unicode_slug` | `name: UnicodeSlug` | Unicode slug validation |
| `IPAddress` | `server:ip` | `server: IPAddress` | IPv4 address validation |
| `IPv6Address` | `server:ipv6` | `server: IPv6Address` | IPv6 address validation |
| **Component-Specific Types** |
| `CssClass` | `css:css_class` | `css: CssClass` | CSS class validation |
| `IconName` | `icon:icon` | `icon: IconName` | Icon name validation |
| `HexColor`, `RgbColor`, `RgbaColor` | `color:color[hex]` | `primary: HexColor` | Color validation |
| `Html` | `content:html` | `content: Html` | HTML content (marked safe) |
| `Json` | `data:json` | `data: Json` | JSON string validation |
| **Choice Types** |
| `Literal` | `role:choice[admin,user,guest]` | `role: Literal['admin', 'user', 'guest']` | Restricted choices |
| `MultiChoice` | `variant:multichoice[primary,large]` | `variant: MultiChoice[Literal['primary', 'large']]` | Multiple choices with flags |
| **Django-Specific Types** |
| `Model` | `author:model[auth.User]` | `author: Model[User]` | Django model instance (use actual class) |
| `QuerySet` | `posts:queryset[blog.Post]` | `posts: QuerySet[Article]` | Django QuerySet (use actual class) |
| `User` | `owner:user` | `owner: User` | Project user model |

!!! note "Model and QuerySet Type References"
    For `Model` and `QuerySet` types in Python code, **prefer using actual model classes** (e.g., `Model[User]`) over string references (e.g., `Model['auth.User']`). String references are available for forward references when needed, but actual classes provide better type safety and IDE support.

### Basic Types

#### String with Validation
```python
# Python usage - use Annotated with Django validators
from typing import Annotated
from django.core.validators import MaxLengthValidator, MinLengthValidator, RegexValidator

name: str                                                          # Basic string, no validation
title: Annotated[str, MaxLengthValidator(100)]                    # With max length
username: Annotated[str, MinLengthValidator(3), MaxLengthValidator(20)]  # Min and max length
code: Annotated[str, RegexValidator(r'^[A-Z]{3}-\d{3}$')]        # With regex pattern
```

```django
{# Template usage #}
{# props name:text title:text[max_length=100] username:text[min_length=3,max_length=20] #}
```

#### Integer with Bounds
```python
# Python usage - use Annotated with Django validators
from typing import Annotated
from django.core.validators import MinValueValidator, MaxValueValidator

age: int                                                          # Any integer, no validation
year: Annotated[int, MinValueValidator(1900)]                    # Minimum value
score: Annotated[int, MinValueValidator(0), MaxValueValidator(100)]  # Min and max bounds
```

```django
{# Template usage #}
{# props age:int year:int[min=1900] score:int[min=0,max=100] #}
```

#### Decimal - Precise Decimal Numbers
```python
# Python usage - use Annotated with Django validators
from typing import Annotated
from decimal import Decimal
from django.core.validators import MinValueValidator, MaxValueValidator, DecimalValidator

price: Decimal                                                    # Any decimal, no validation
amount: Annotated[Decimal, MinValueValidator(0), MaxValueValidator(Decimal('999.99'))]  # With bounds
precise: Annotated[Decimal, DecimalValidator(10, 2)]             # With precision (max_digits, decimal_places)
```

```django
{# Template usage #}
{# props price:decimal amount:decimal[min=0,max=999.99] #}
```

### Validated String Types

All of these are pre-configured `Annotated` types with specific Django validators:

```python
# Python usage
email: Email        # EmailValidator
website: Url        # URLValidator
permalink: Slug     # Slug validator (lowercase, hyphens)
name: UnicodeSlug   # Unicode-aware slug
server: IPAddress   # IPv4 address validator
server_v6: IPv6Address  # IPv6 address validator
```

```django
{# Template usage #}
{# props email:email website:url permalink:slug server:ip #}
```

### Component-Specific Types

#### `CssClass` - CSS Class Validation
```python
# Python usage - pre-configured Annotated type
from includecontents.prop_types import CssClass

css: CssClass  # Default pattern: ^[a-zA-Z][\w-]*(\s+[a-zA-Z][\w-]*)*$

# For custom patterns, use Annotated directly
from typing import Annotated
from django.core.validators import RegexValidator

custom: Annotated[str, RegexValidator(r'^btn-\w+$', "Invalid CSS class")]
```

```django
{# Template usage #}
{# props css:css_class #}
```

#### Color Validators - CSS Color Validation
```python
# Python usage - pre-configured color validators
from includecontents.prop_types import HexColor, RgbColor, RgbaColor

primary: HexColor    # Validates hex format (#fff, #ffffff)
accent: RgbColor     # Validates RGB format (rgb(255, 0, 0))
shadow: RgbaColor    # Validates RGBA format (rgba(0, 0, 0, 0.5))

# For custom validation, use Annotated directly
from typing import Annotated
from django.core.validators import RegexValidator

custom: Annotated[str, RegexValidator(r'^custom-pattern$', "Invalid color")]
```

```django
{# Template usage #}
{# props primary:color[hex] accent:color[rgb] shadow:color[rgba] #}
```

#### `IconName` - Icon Name Validation
```python
# Python usage - pre-configured Annotated type
from includecontents.prop_types import IconName

icon: IconName  # Validates icon name format (^[a-zA-Z0-9][\w:-]*$)
```

```django
{# Template usage #}
{# props icon:icon #}
```

#### `Html` - HTML Content Marker
```python
# Python usage
content: Html      # String that will be marked safe in templates
```

```django
{# Template usage #}
{# props content:html #}
```

#### `Json` - JSON String Validation
```python
# Python usage
config: Json       # Validates JSON format
```

```django
{# Template usage #}
{# props config:json #}
```

### Choice Types

#### `Literal` - Restricted String Choices
```python
# Python usage
role: Literal['admin', 'user', 'guest']
size: Literal['sm', 'md', 'lg'] = 'md'
```

```django
{# Template usage #}
{# props role:choice[admin,user,guest] size:choice[sm,md,lg]=md #}
```

**Note:** In Python code, use `Literal` from `typing`. In template comments, use `choice[...]` syntax.

#### `MultiChoice` - Multiple Choices with Boolean Flags
```python
# Python usage
variant: MultiChoice[Literal['primary', 'secondary', 'large', 'small']]
features: MultiChoice[Literal['shadow', 'border', 'hover']] = 'shadow border'
```

```django
{# Template usage #}
{# props variant:multichoice[primary,secondary,large,small] #}

{# Usage generates camelCase boolean flags #}
<include:component variant="primary large">
{# Creates: variantPrimary=True, variantLarge=True, variantSecondary=False, variantSmall=False #}
```

### Django-Specific Types

#### `Model` - Django Model Instance Validation
```python
# Python usage
from django.contrib.auth import get_user_model
from django.db import models

User = get_user_model()

any_model: Model[models.Model]  # Any Django model instance
user: Model[User]               # Specific model by class (preferred)
article: Model[Article]         # Specific model by class
```

```django
{# Template usage #}
{# props user:model[auth.User] #}
```

#### `QuerySet` - Django QuerySet Validation
```python
# Python usage
from django.contrib.auth import get_user_model
from django.db import models

User = get_user_model()

any_queryset: QuerySet[models.Model]  # Any QuerySet
users: QuerySet[User]                 # QuerySet of specific model (preferred)
articles: QuerySet[Article]           # QuerySet of model class
```

```django
{# Template usage #}
{# props posts:queryset[blog.Post] #}
```

#### `User` - Project User Model
```python
# Python usage
owner: User        # Validates against AUTH_USER_MODEL
```

```django
{# Template usage #}
{# props owner:user #}
```

### Helper Functions

For convenience, several helper functions are available to create commonly-used validated types:

#### `Pattern(regex, message)` - Custom Regex Validation
```python
# Python usage
from includecontents.prop_types import Pattern

ProductCode = Pattern(r'^[A-Z]{3}-\d{3}$', 'Invalid product code format')
product_code: ProductCode  # Equivalent to Annotated[str, RegexValidator(...)]
```

#### `MinMax(min_val, max_val)` - Integer Bounds
```python
# Python usage
from includecontents.prop_types import MinMax

Age18Plus = MinMax(18, 120)
age: Age18Plus  # Equivalent to Annotated[int, MinValueValidator(18), MaxValueValidator(120)]
```

#### `MinMaxDecimal(min_val, max_val, max_digits, decimal_places)` - Decimal Bounds
```python
# Python usage
from includecontents.prop_types import MinMaxDecimal

Price = MinMaxDecimal(0, 999.99, max_digits=6, decimal_places=2)
price: Price  # Equivalent to Annotated[Decimal, ...]
```

**Note:** While these helper functions are convenient, you can also use `Annotated` directly with Django validators for more flexibility.

### Type Coercion

The system automatically converts string inputs to appropriate types:

| Input | Type | Result | Notes |
|-------|------|--------|-------|
| `"25"` | `int` | `25` | String to integer |
| `"true"` | `bool` | `True` | String to boolean |
| `"false"` | `bool` | `False` | Recognizes false, 0, no, off, empty |
| `"4.5"` | `Decimal` | `Decimal('4.5')` | String to decimal |
| `"red,blue,green"` | `list[str]` | `['red', 'blue', 'green']` | Comma-separated to list |
| `"primary large"` | `MultiChoice` | `"primary large"` + flags | Space-separated choices |

### Optional Props Syntax

There are several ways to make props optional:

#### Template Props Syntax

```django
{# 1. Use ? marker #}
{# props name?:text email?:email age?:int #}

{# 2. Provide default values #}
{# props name:text="Anonymous" active:bool=true count:int=0 #}

{# 3. Legacy enum with empty first value #}
{# props size=,small,medium,large theme=,light,dark #}
```

#### Python Props Syntax

```python
@dataclass
class Props:
    # Using | None (Python 3.10+)
    name: str | None = None
    email: str | None = None

    # Using Optional (older Python)
    from typing import Optional
    bio: Optional[str] = None

    # Default values (makes them optional)
    active: bool = True
    count: int = 0
    theme: Choice['light', 'dark'] = 'light'
```

**Important:** The `| None` syntax is **only supported in Python dataclasses**, not in template `{# props #}` syntax. Use `?` marker or defaults in templates.

### Legacy Enum Optional Syntax

The original enum syntax supports optional values by starting with an empty choice:

```django
{# Legacy syntax - still supported #}
{# props size=,small,medium,large #}          {# Leading comma = optional #}
{# props validation_state=,valid,invalid #}   {# Empty first = optional #}

{# Modern equivalent #}
{# props size?:choice[small,medium,large] #}  {# ? marker = optional #}
{# props size:choice[small,medium,large]="" #}  {# Empty default = optional #}
```

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

{# MultiChoice defaults - supports multiple space-separated values #}
{# props variant:multichoice[primary,secondary,large,small]=primary size:multichoice[sm,md,lg]=md #}
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

### MultiChoice Type

The `MultiChoice` type supports multiple space-separated values while automatically generating camelCase boolean flags in the template context.

#### Basic Usage

```python
from includecontents.prop_types import MultiChoice

@component('components/button.html')
@dataclass
class ButtonProps:
    variant: MultiChoice[Literal['primary', 'secondary', 'large', 'small']] = 'primary'
```

#### Template Syntax

```django
{# Template definition #}
{# props variant:multichoice[primary,secondary,large,small] #}

{# Usage - single value #}
<include:button variant="primary">Click me</include:button>

{# Usage - multiple values #}
<include:button variant="primary large">Big primary button</include:button>
```

#### Generated camelCase Flags

When a MultiChoice value is set, boolean flags are automatically generated in the template context:

```django
{# For variant="primary large", these flags are available: #}
{% if variantPrimary %}  {# True - primary is selected #}
    <span class="primary-styling"></span>
{% endif %}

{% if variantLarge %}    {# True - large is selected #}
    <span class="large-styling"></span>
{% endif %}

{% if variantSecondary %} {# False - secondary not selected (variable doesn't exist) #}
    <span class="secondary-styling"></span>
{% endif %}
```

#### Hyphen Handling

Hyphenated values are automatically converted to camelCase for flag generation:

```python
variant: MultiChoice[Literal['dark-mode', 'extra-large', 'light-theme']]
```

```django
{# For variant="dark-mode extra-large" #}
{% if variantDarkMode %}     {# True #}
{% if variantExtraLarge %}   {# True #}
{% if variantLightTheme %}   {# False #}
```

#### Practical Examples

**Button Component:**
```python
@component('components/button.html')
@dataclass
class ButtonProps:
    label: str
    variant: MultiChoice[Literal['primary', 'secondary', 'outline']] = 'primary'
    size: MultiChoice[Literal['sm', 'md', 'lg']] = 'md'
    disabled: bool = False
```

```django
{# components/button.html #}
{# props label:str variant:multichoice[primary,secondary,outline]=primary size:multichoice[sm,md,lg]=md disabled:bool=false #}

<button class="btn{% if variantPrimary %} btn-primary{% endif %}{% if variantSecondary %} btn-secondary{% endif %}{% if variantOutline %} btn-outline{% endif %}{% if sizeSm %} btn-sm{% endif %}{% if sizeLg %} btn-lg{% endif %}"
        {% if disabled %}disabled{% endif %}>
    {{ label }}
</button>
```

**Usage:**
```django
{# Single values #}
<include:button label="Save" variant="primary" />
<include:button label="Cancel" variant="secondary" size="sm" />

{# Multiple values (not typical for size, but demonstrates capability) #}
<include:button label="Special" variant="primary outline" />
```

#### Backward Compatibility with Legacy Enums

MultiChoice provides the same functionality as legacy enum props but with modern type safety:

```django
{# Legacy enum syntax (still works) #}
{# def variant=primary,secondary,large #}

{# Modern MultiChoice equivalent #}
{# props variant:multichoice[primary,secondary,large] #}
```

Both generate the same camelCase boolean flags (`variantPrimary`, `variantSecondary`, `variantLarge`).

#### Validation

MultiChoice validates that all space-separated values are in the allowed list:

```python
# ✅ Valid
validate_props(ButtonProps, {'variant': 'primary'})           # Single value
validate_props(ButtonProps, {'variant': 'primary large'})     # Multiple values
validate_props(ButtonProps, {'variant': 'secondary outline'}) # Different combination

# ❌ Invalid - raises ValidationError
validate_props(ButtonProps, {'variant': 'invalid'})           # Unknown value
validate_props(ButtonProps, {'variant': 'primary invalid'})   # Mix of valid/invalid
```

#### Migration from Legacy Enums

To migrate from legacy enum syntax to MultiChoice:

1. **Update the template comment:**
   ```django
   {# Before #}
   {# def variant=primary,secondary,large #}
   
   {# After #}
   {# props variant:multichoice[primary,secondary,large] #}
   ```

2. **Or create a Python props class:**
   ```python
   @component('components/your-component.html')
   @dataclass
   class YourComponentProps:
       variant: MultiChoice[Literal['primary', 'secondary', 'large']]
   ```

3. **Template usage remains the same** - all camelCase flags continue to work identically.

#### Advanced Usage with Defaults

```python
@component('components/card.html')
@dataclass  
class CardProps:
    title: str
    variant: MultiChoice[Literal['primary', 'secondary', 'outline']] = 'primary'
    features: MultiChoice[Literal['shadow', 'border', 'hover-effect']] = 'shadow border'
    size: MultiChoice[Literal['sm', 'md', 'lg']] = 'md'
```

```django
{# All of these work: #}
<include:card title="Default card" />  {# Uses all defaults #}
<include:card title="Big card" size="lg" />
<include:card title="Special card" features="shadow hover-effect" variant="outline" />
```

## Python Props Classes

### Basic Example

```python
from dataclasses import dataclass
from typing import Annotated, Optional
from django.core.validators import MinLengthValidator
from includecontents.prop_types import Email
from includecontents.props import component

@component('components/contact-card.html')
@dataclass
class ContactCardProps:
    name: Annotated[str, MinLengthValidator(2)]
    email: Email
    phone: Optional[str] = None
```

### With Custom Validation

```python
from typing import Annotated
from django.core.validators import MinLengthValidator

@component('components/password-form.html')
@dataclass
class PasswordFormProps:
    password: Annotated[str, MinLengthValidator(8)]
    confirm_password: Annotated[str, MinLengthValidator(8)]

    def clean(self):
        """Cross-field validation."""
        from django.core.exceptions import ValidationError
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
from django.db import models

@component('components/content-list.html')
@dataclass
class ContentListProps:
    items: QuerySet[models.Model]  # Any QuerySet
    owner: Model[models.Model]  # Any Django model instance
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
    type: Literal['info', 'warning', 'error', 'custom']
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
    label: str
    variant: Literal['primary', 'secondary'] = 'primary'
    # Extra attrs will be collected in template's {{ attrs }}
```

### Conditional Props

Use Optional types for conditional rendering:

```python
footer: Optional[str] = None  # Only render footer if provided
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

## Next Steps

- Deepen everyday attribute usage with [Props & Attrs](using-components/props-and-attrs.md)
- Combine validation with enum helpers in [Advanced Props](building-components/advanced-props.md)
- Look up tag and attribute details in the [API Reference](reference/api-reference.md)
- Diagnose common errors with the [Troubleshooting Guide](reference/troubleshooting.md)
