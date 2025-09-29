"""
Django-specific component prop types for type-safe validation.

This module provides prop types specifically designed for Django components,
using Django validators and handling Django model instances, QuerySets, etc.
"""

import decimal
from typing import Annotated, Literal, TypeVar, Generic

from django.core.exceptions import ValidationError
from django.core.validators import (
    EmailValidator,
    URLValidator,
    MaxLengthValidator,
    MinLengthValidator,
    MaxValueValidator,
    MinValueValidator,
    RegexValidator,
    DecimalValidator,
    validate_ipv4_address,
    validate_ipv6_address,
    validate_slug,
    validate_unicode_slug,
)


# Basic component prop types
class Text:
    """
    String prop type with optional validation.

    Usage:
        name: Text  # Basic text
        name: Text[max_length=100]  # With max length
        name: Text[min_length=2, max_length=50]  # Multiple validations
        name: Text[pattern=r'^[A-Z]']  # With regex pattern
    """

    def __new__(cls, **kwargs):
        """
        Support both bare and keyword-parameter usage.
        Text() -> str
        Text(max_length=100, min_length=2, pattern=...) -> Annotated[str, validators]
        """
        if not kwargs:
            return str
        validators = []
        if 'max_length' in kwargs:
            validators.append(MaxLengthValidator(kwargs['max_length']))
        if 'min_length' in kwargs:
            validators.append(MinLengthValidator(kwargs['min_length']))
        if 'pattern' in kwargs:
            validators.append(RegexValidator(kwargs['pattern']))
        return Annotated[str, *validators] if validators else str

    def __class_getitem__(cls, params):
        """Handle Text[...] syntax for validation parameters."""
        validators = []

        # Handle dict-like params: Text[max_length=100, min_length=2]
        if isinstance(params, dict):
            if 'max_length' in params:
                validators.append(MaxLengthValidator(params['max_length']))
            if 'min_length' in params:
                validators.append(MinLengthValidator(params['min_length']))
            if 'pattern' in params:
                validators.append(RegexValidator(params['pattern']))

        return Annotated[str, *validators] if validators else str


class Integer:
    """
    Integer prop type with optional bounds validation.

    Usage:
        age: Integer  # Any integer
        age: Integer[min=18]  # Minimum value
        age: Integer[min=18, max=120]  # Min and max bounds
    """

    def __new__(cls, **kwargs):
        """
        Support both bare and keyword-parameter usage.
        Integer() -> int
        Integer(min=..., max=...) -> Annotated[int, validators]
        """
        if not kwargs:
            return int
        validators = []
        if 'min' in kwargs:
            validators.append(MinValueValidator(kwargs['min']))
        if 'max' in kwargs:
            validators.append(MaxValueValidator(kwargs['max']))
        return Annotated[int, *validators] if validators else int

    def __class_getitem__(cls, params):
        """Handle Integer[...] syntax for validation parameters."""
        validators = []

        if isinstance(params, dict):
            if 'min' in params:
                validators.append(MinValueValidator(params['min']))
            if 'max' in params:
                validators.append(MaxValueValidator(params['max']))

        return Annotated[int, *validators] if validators else int


class Decimal:
    """
    Decimal prop type for precise numeric values.

    Usage:
        price: Decimal  # Any decimal
        price: Decimal[max_digits=10, decimal_places=2]  # Precision
        price: Decimal[min=0, max=999.99]  # With bounds
    """

    def __new__(cls, **kwargs):
        """
        Support both bare and keyword-parameter usage.
        Decimal() -> Decimal
        Decimal(min=..., max=..., max_digits=..., decimal_places=...) -> Annotated[Decimal, validators]
        """
        if not kwargs:
            return decimal.Decimal
        validators = []
        if 'min' in kwargs:
            validators.append(MinValueValidator(kwargs['min']))
        if 'max' in kwargs:
            validators.append(MaxValueValidator(kwargs['max']))
        if 'max_digits' in kwargs and 'decimal_places' in kwargs:
            validators.append(DecimalValidator(kwargs['max_digits'], kwargs['decimal_places']))
        return Annotated[decimal.Decimal, *validators] if validators else decimal.Decimal

    def __class_getitem__(cls, params):
        """Handle Decimal[...] syntax for validation parameters."""
        validators = []

        if isinstance(params, dict):
            if 'min' in params:
                validators.append(MinValueValidator(params['min']))
            if 'max' in params:
                validators.append(MaxValueValidator(params['max']))
            if 'max_digits' in params and 'decimal_places' in params:
                validators.append(DecimalValidator(params['max_digits'], params['decimal_places']))

        return Annotated[decimal.Decimal, *validators] if validators else decimal.Decimal


# Pre-configured common prop types
Email = Annotated[str, EmailValidator()]
Url = Annotated[str, URLValidator()]
Slug = Annotated[str, validate_slug]
UnicodeSlug = Annotated[str, validate_unicode_slug]
IPAddress = Annotated[str, validate_ipv4_address]
IPv6Address = Annotated[str, validate_ipv6_address]


# Choice type for restricted values
T = TypeVar('T')


class Choice(Generic[T]):
    """
    Literal-like type for restricted choices.

    Usage:
        role: Choice['admin', 'user', 'guest']
        size: Choice['sm', 'md', 'lg'] = 'md'
    """

    def __class_getitem__(cls, items):
        if isinstance(items, str):
            # Single item: Choice['admin']
            return Literal[items]
        elif isinstance(items, tuple):
            # Multiple items: Choice['admin', 'user', 'guest']
            # Unpack the tuple to create Literal['admin', 'user', 'guest']
            return Literal[items]
        else:
            # Single non-string item: Choice[123]
            return Literal[items]


# Unique marker for MultiChoice values to enable camelCase boolean flag generation
_MULTICHOICE_MARKER = object()


class MultiChoice(Generic[T]):
    """
    Multiple choice type that supports space-separated values and generates camelCase boolean flags.

    This type mimics the behavior of legacy enum props, where multiple values can be provided
    space-separated (e.g., "primary large") and each value generates a camelCase boolean flag
    in the template context (e.g., variantPrimary=True, variantLarge=True).

    Usage:
        variant: MultiChoice['primary', 'secondary', 'large', 'small']
        variant: MultiChoice['primary', 'secondary', 'large', 'small'] = 'primary'

    Example:
        # Component definition:
        {# props variant:multichoice[primary,secondary,large,small] #}

        # Usage:
        <include:button variant="primary large">Click me</include:button>

        # Template context will have:
        # - variant = "primary large"
        # - variantPrimary = True
        # - variantLarge = True
        # - variantSecondary = False (not set)
        # - variantSmall = False (not set)
    """

    def __class_getitem__(cls, items):
        """
        Create a MultiChoice type with allowed values.

        Returns an Annotated type with validation and the MultiChoice marker
        for downstream processing.
        """
        if isinstance(items, str):
            items = (items,)
        elif not isinstance(items, (tuple, list)):
            items = (items,)

        def validate_multichoice(value):
            """Validate that all space-separated values are in allowed choices."""
            from django.core.exceptions import ValidationError

            if value is None:
                return

            # Convert to string and split on spaces
            value_str = str(value).strip()
            if not value_str:
                return

            provided_values = value_str.split()

            # Check each value against allowed choices
            for val in provided_values:
                if val not in items:
                    raise ValidationError(
                        f'Invalid choice "{val}". Allowed choices: {", ".join(repr(x) for x in items)}'
                    )

        # Return annotated type with both validator and MultiChoice marker
        return Annotated[str, validate_multichoice, _MULTICHOICE_MARKER, items]


# Django-specific prop types

# Model type that supports both bare usage and square brackets
class Model:
    """
    Validates that the value is an instance of a Django model.

    Usage:
        user: Model['auth.User']  # Specific model by string
        article: Model[Article]    # Specific model by class
        any_model: Model           # Any Django model instance (returns Annotated type)
    """

    def __class_getitem__(cls, model_spec):
        """Handle Model[...] syntax for specific models."""
        def validate_model(value):
            from django.core.exceptions import ValidationError
            from django.apps import apps

            # Handle string model spec like 'auth.User'
            if isinstance(model_spec, str):
                try:
                    app_label, model_name = model_spec.split('.')
                    model_class = apps.get_model(app_label, model_name)
                except (ValueError, LookupError):
                    raise ValidationError(f"Invalid model: {model_spec}")
            else:
                model_class = model_spec

            # Check if value is an instance of the specific model
            if value is not None and not isinstance(value, model_class):
                raise ValidationError(
                    f"Expected instance of {model_class.__name__}, got {type(value).__name__}"
                )

        return Annotated[object, validate_model]

    def __new__(cls):
        """When used bare (e.g., Model), return an Annotated type for any model."""
        def validate_any_model(value):
            from django.core.exceptions import ValidationError
            from django.db.models import Model as DjangoModel

            if value is not None and not isinstance(value, DjangoModel):
                raise ValidationError(
                    f"Expected a Django model instance, got {type(value).__name__}"
                )

        return Annotated[object, validate_any_model]


# QuerySet type that supports both bare usage and square brackets
class QuerySet:
    """
    Validates that the value is a Django QuerySet.

    Usage:
        items: QuerySet['blog.Post']  # QuerySet of specific model
        users: QuerySet[User]          # QuerySet of model class
        any_qs: QuerySet               # Any QuerySet (returns Annotated type)
    """

    def __class_getitem__(cls, model_spec):
        """Handle QuerySet[...] syntax for specific model querysets."""
        def validate_queryset(value):
            from django.core.exceptions import ValidationError
            from django.db.models import QuerySet as DjangoQuerySet
            from django.apps import apps

            # Check if it's a QuerySet
            if value is not None and not isinstance(value, DjangoQuerySet):
                raise ValidationError(
                    f"Expected QuerySet, got {type(value).__name__}"
                )

            # Check the model if specified
            if value is not None:
                if isinstance(model_spec, str):
                    try:
                        app_label, model_name = model_spec.split('.')
                        model_class = apps.get_model(app_label, model_name)
                    except (ValueError, LookupError):
                        raise ValidationError(f"Invalid model: {model_spec}")
                else:
                    model_class = model_spec

                # Check if QuerySet is of the correct model
                if value.model != model_class:
                    raise ValidationError(
                        f"Expected QuerySet of {model_class.__name__}, "
                        f"got QuerySet of {value.model.__name__}"
                    )

        return Annotated[object, validate_queryset]

    def __new__(cls):
        """When used bare (e.g., QuerySet), return an Annotated type for any queryset."""
        def validate_any_queryset(value):
            from django.core.exceptions import ValidationError
            from django.db.models import QuerySet as DjangoQuerySet

            if value is not None and not isinstance(value, DjangoQuerySet):
                raise ValidationError(
                    f"Expected a QuerySet, got {type(value).__name__}"
                )

        return Annotated[object, validate_any_queryset]


# Special User type that works with any user model
def _validate_user(value):
    """Validator for the project's user model."""
    from django.core.exceptions import ValidationError
    from django.contrib.auth import get_user_model

    UserModel = get_user_model()

    if value is not None and not isinstance(value, UserModel):
        raise ValidationError(
            f"Expected instance of {UserModel.__name__}, got {type(value).__name__}"
        )

# User is just an annotated type
User = Annotated[object, _validate_user]


# Component-specific prop types
class CssClass:
    """
    CSS class name validation.

    Usage:
        css: CssClass  # Default CSS class validation
        css: CssClass[pattern=r'^custom-pattern$']  # Custom pattern
    """

    def __new__(cls):
        """Bare CssClass usage with default pattern."""
        return Annotated[str, RegexValidator(
            r'^[a-zA-Z][\w-]*(\s+[a-zA-Z][\w-]*)*$',
            "Invalid CSS class name"
        )]

    def __class_getitem__(cls, params):
        """Handle CssClass[...] syntax for custom pattern."""
        if isinstance(params, dict) and 'pattern' in params:
            pattern = params['pattern']
        else:
            pattern = r'^[a-zA-Z][\w-]*(\s+[a-zA-Z][\w-]*)*$'

        return Annotated[str, RegexValidator(pattern, "Invalid CSS class name")]


class Color:
    """
    CSS color validation.

    Usage:
        color: Color  # Any color format
        color: Color['hex']  # Hex colors only
        color: Color['rgb']  # RGB format only
        color: Color['rgba']  # RGBA format only
    """

    def __new__(cls, **kwargs):
        """
        Support both bare and keyword-parameter usage.
        Color() -> str (any format)
        Color(format='hex'|'rgb'|'rgba') -> Annotated[str, RegexValidator]
        """
        if not kwargs:
            return str
        fmt = kwargs.get('format')
        patterns = {
            'hex': r'^#[0-9A-Fa-f]{3}([0-9A-Fa-f]{3})?$',
            'rgb': r'^rgb\(\s*\d{1,3}\s*,\s*\d{1,3}\s*,\s*\d{1,3}\s*\)$',
            'rgba': r'^rgba\(\s*\d{1,3}\s*,\s*\d{1,3}\s*,\s*\d{1,3}\s*,\s*[01]?\.?\d*\s*\)$',
        }
        if fmt in patterns:
            return Annotated[str, RegexValidator(patterns[fmt], f"Invalid {fmt} color")]
        return str

    def __class_getitem__(cls, format):
        """Handle Color[...] syntax for specific formats."""
        patterns = {
            'hex': r'^#[0-9A-Fa-f]{3}([0-9A-Fa-f]{3})?$',
            'rgb': r'^rgb\(\s*\d{1,3}\s*,\s*\d{1,3}\s*,\s*\d{1,3}\s*\)$',
            'rgba': r'^rgba\(\s*\d{1,3}\s*,\s*\d{1,3}\s*,\s*\d{1,3}\s*,\s*[01]?\.?\d*\s*\)$',
            'any': r'.*',  # Accept any color format
        }

        if isinstance(format, str):
            pattern = patterns.get(format, patterns['any'])
            return Annotated[str, RegexValidator(pattern, f"Invalid {format} color")]

        return str  # Default to any format


class IconName:
    """
    Icon name validation (validates against registered icons).

    Usage:
        icon: IconName  # Validates icon name format
    """

    def __new__(cls):
        # This will be enhanced to check against registered icons
        # For now, just validate the format
        return Annotated[str, RegexValidator(
            r'^[a-zA-Z0-9][\w:-]*$',
            "Invalid icon name"
        )]


# Unique marker object to tag Html-typed values in Annotated metadata
_HTML_MARKER = object()


class Html:
    """
    Marker type for HTML content that should be marked safe in templates.

    This returns an Annotated[str, _HTML_MARKER] which allows downstream
    validation/templating to detect Html values and mark them safe.
    """

    def __new__(cls):
        return Annotated[str, _HTML_MARKER]


class Json:
    """
    JSON string that will be parsed and validated.

    Usage:
        data: Json  # Validates JSON format
    """

    def __new__(cls):
        def validate_json(value):
            import json
            try:
                json.loads(value) if isinstance(value, str) else value
            except (json.JSONDecodeError, TypeError) as e:
                raise ValidationError(f"Invalid JSON: {e}")

        return Annotated[str, validate_json]


# Utility functions for creating custom prop types
def Pattern(regex, message="Invalid format"):
    """Create a string prop type with regex validation."""
    return Annotated[str, RegexValidator(regex, message)]


def MinMax(min_val, max_val):
    """Create an integer prop type with min/max bounds."""
    return Annotated[int, MinValueValidator(min_val), MaxValueValidator(max_val)]


def MinMaxDecimal(min_val, max_val, max_digits=10, decimal_places=2):
    """Create a decimal prop type with bounds and precision."""
    return Annotated[
        decimal.Decimal,
        MinValueValidator(min_val),
        MaxValueValidator(max_val),
        DecimalValidator(max_digits, decimal_places)
    ]


# Type mapping for template parser
TYPE_MAP = {
    'text': Text(),
    'str': Text(),
    'string': Text(),
    'int': Integer(),
    'integer': Integer(),
    'decimal': Decimal(),
    'float': Decimal(),
    'email': Email,
    'url': Url,
    'slug': Slug,
    'unicode_slug': UnicodeSlug,
    'ip': IPAddress,
    'ipv4': IPAddress,
    'ipv6': IPv6Address,
    'css_class': CssClass(),
    'color': Color(),
    'icon': IconName(),
    'html': Html(),
    'json': Json(),
    'bool': bool,
    'boolean': bool,
    'model': Model(),  # Model instance returns Annotated type for any model
    'queryset': QuerySet(),  # QuerySet instance returns Annotated type for any queryset
    'user': User,  # Special user type
    'multichoice': MultiChoice,  # MultiChoice type with camelCase boolean flags
}

# Mapping of type names to their classes (for parameterized types)
TYPE_CLASSES = {
    'text': Text,
    'str': Text,
    'string': Text,
    'int': Integer,
    'integer': Integer,
    'decimal': Decimal,
    'float': Decimal,
    'css_class': CssClass,
    'color': Color,
    'model': Model,
    'queryset': QuerySet,
    'multichoice': MultiChoice,
}