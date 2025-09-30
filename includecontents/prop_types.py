"""
Component prop types for type-safe validation using Django validators.

This module provides prop types specifically designed for component props,
avoiding confusion with Django's form fields, model fields, or serializer fields.
"""

import decimal
from typing import Annotated, TypeVar, Generic  # Literal used in MultiChoice docstrings

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
# Pre-configured common prop types
Email = Annotated[str, EmailValidator()]
Url = Annotated[str, URLValidator()]
Slug = Annotated[str, validate_slug]
UnicodeSlug = Annotated[str, validate_unicode_slug]
IPAddress = Annotated[str, validate_ipv4_address]
IPv6Address = Annotated[str, validate_ipv6_address]


# Unique marker for MultiChoice values to enable camelCase boolean flag generation
T = TypeVar("T")
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

    def __class_getitem__(cls, literal_type):
        """
        Create a MultiChoice type with allowed values.

        Usage: MultiChoice[Literal["primary", "secondary", "large"]]

        Returns an Annotated type with validation and the MultiChoice marker
        for downstream processing.
        """
        # Extract the literal values from the Literal type
        from typing import get_args

        # Get the args from Literal["primary", "secondary", ...]
        items = get_args(literal_type)

        if not items:
            raise TypeError("MultiChoice requires at least one choice value")

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
        # Pass the original Literal type for proper type checking
        return Annotated[literal_type, validate_multichoice, _MULTICHOICE_MARKER, items]


# Django-specific prop types


# Model type with square bracket syntax for model specification
class Model:
    """
    Validates that the value is an instance of a Django model.

    Usage:
        user: Model['auth.User']  # Specific model by string reference
        article: Model[Article]    # Specific model by class (preferred)
    """

    def __class_getitem__(cls, model_spec):
        """Handle Model[...] syntax for specific models."""

        def validate_model(value):
            from django.core.exceptions import ValidationError
            from django.apps import apps

            # Handle string model spec like 'auth.User'
            if isinstance(model_spec, str):
                try:
                    app_label, model_name = model_spec.split(".")
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


# QuerySet type with square bracket syntax for model specification
class QuerySet:
    """
    Validates that the value is a Django QuerySet.

    Usage:
        items: QuerySet['blog.Post']  # QuerySet of specific model (string reference)
        users: QuerySet[User]          # QuerySet of specific model (preferred)
    """

    def __class_getitem__(cls, model_spec):
        """Handle QuerySet[...] syntax for specific model querysets."""

        def validate_queryset(value):
            from django.core.exceptions import ValidationError
            from django.db.models import QuerySet as DjangoQuerySet
            from django.apps import apps

            # Check if it's a QuerySet
            if value is not None and not isinstance(value, DjangoQuerySet):
                raise ValidationError(f"Expected QuerySet, got {type(value).__name__}")

            # Check the model if specified
            if value is not None:
                if isinstance(model_spec, str):
                    try:
                        app_label, model_name = model_spec.split(".")
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
# Pre-configured types with validators
CssClass = Annotated[
    str,
    RegexValidator(
        r"^[a-zA-Z][\w-]*(\s+[a-zA-Z][\w-]*)*$", "Invalid CSS class name"
    ),
]

# Icon name with basic format validation
IconName = Annotated[
    str, RegexValidator(r"^[a-zA-Z0-9][\w:-]*$", "Invalid icon name")
]

# Color validators - pre-configured for common color formats
HexColor = Annotated[
    str,
    RegexValidator(r"^#[0-9A-Fa-f]{3}([0-9A-Fa-f]{3})?$", "Invalid hex color"),
]

RgbColor = Annotated[
    str,
    RegexValidator(
        r"^rgb\(\s*\d{1,3}\s*,\s*\d{1,3}\s*,\s*\d{1,3}\s*\)$", "Invalid RGB color"
    ),
]

RgbaColor = Annotated[
    str,
    RegexValidator(
        r"^rgba\(\s*\d{1,3}\s*,\s*\d{1,3}\s*,\s*\d{1,3}\s*,\s*[01]?\.?\d*\s*\)$",
        "Invalid RGBA color",
    ),
]


# Unique marker object to tag Html-typed values in Annotated metadata
_HTML_MARKER = object()


def _validate_json(value):
    """Validator for JSON strings."""
    import json

    try:
        json.loads(value) if isinstance(value, str) else value
    except (json.JSONDecodeError, TypeError) as e:
        raise ValidationError(f"Invalid JSON: {e}")


# Html and Json as simple Annotated types
Html = Annotated[str, _HTML_MARKER]
"""Marker type for HTML content that should be marked safe in templates."""

Json = Annotated[str, _validate_json]
"""JSON string that will be parsed and validated."""


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
        DecimalValidator(max_digits, decimal_places),
    ]


# Helper functions to build Annotated types for text/integer/decimal with validators
def _build_text_type(params: dict):
    """Build Annotated[str, validators] from params dict."""
    validators = []
    if "max_length" in params:
        validators.append(MaxLengthValidator(params["max_length"]))
    if "min_length" in params:
        validators.append(MinLengthValidator(params["min_length"]))
    if "pattern" in params:
        validators.append(RegexValidator(params["pattern"]))
    return Annotated[str, *validators] if validators else str


def _build_integer_type(params: dict):
    """Build Annotated[int, validators] from params dict."""
    validators = []
    if "min" in params:
        validators.append(MinValueValidator(params["min"]))
    if "max" in params:
        validators.append(MaxValueValidator(params["max"]))
    return Annotated[int, *validators] if validators else int


def _build_decimal_type(params: dict):
    """Build Annotated[Decimal, validators] from params dict."""
    validators = []
    if "min" in params:
        validators.append(MinValueValidator(params["min"]))
    if "max" in params:
        validators.append(MaxValueValidator(params["max"]))
    if "max_digits" in params and "decimal_places" in params:
        validators.append(
            DecimalValidator(params["max_digits"], params["decimal_places"])
        )
    return Annotated[decimal.Decimal, *validators] if validators else decimal.Decimal


def _build_css_class_type(params: dict):
    """Build Annotated[str, RegexValidator] for CSS class with custom pattern."""
    pattern = params.get("pattern", r"^[a-zA-Z][\w-]*(\s+[a-zA-Z][\w-]*)*$")
    return Annotated[str, RegexValidator(pattern, "Invalid CSS class name")]


def _build_color_type(params: dict):
    """Build Annotated[str, RegexValidator] for CSS color with format validation."""
    # If no format specified, return plain str (any color format)
    if not params:
        return str

    fmt = params.get("format", "any")
    patterns = {
        "hex": r"^#[0-9A-Fa-f]{3}([0-9A-Fa-f]{3})?$",
        "rgb": r"^rgb\(\s*\d{1,3}\s*,\s*\d{1,3}\s*,\s*\d{1,3}\s*\)$",
        "rgba": r"^rgba\(\s*\d{1,3}\s*,\s*\d{1,3}\s*,\s*\d{1,3}\s*,\s*[01]?\.?\d*\s*\)$",
        "any": r".*",
    }

    pattern = patterns.get(fmt, patterns["any"])
    if fmt == "any" or pattern == r".*":
        return str  # No validation for "any" format

    return Annotated[str, RegexValidator(pattern, f"Invalid {fmt} color")]


# Type mapping for template parser (bare types without parameters)
TYPE_MAP = {
    "text": str,
    "str": str,
    "string": str,
    "int": int,
    "integer": int,
    "decimal": decimal.Decimal,
    "float": decimal.Decimal,
    "email": Email,
    "url": Url,
    "slug": Slug,
    "unicode_slug": UnicodeSlug,
    "ip": IPAddress,
    "ipv4": IPAddress,
    "ipv6": IPv6Address,
    "css_class": CssClass,
    "icon": IconName,
    "html": Html,
    "json": Json,
    "bool": bool,
    "boolean": bool,
    # Note: bare "model" and "queryset" in templates require subscripting with model type
    # These are handled specially in the template parser (see template_parser.py)
    "user": User,  # Special user type
    "multichoice": MultiChoice,  # MultiChoice type with camelCase boolean flags
}

# Mapping of type names to their builder functions (for parameterized types)
TYPE_BUILDERS = {
    "text": _build_text_type,
    "str": _build_text_type,
    "string": _build_text_type,
    "int": _build_integer_type,
    "integer": _build_integer_type,
    "decimal": _build_decimal_type,
    "float": _build_decimal_type,
    "css_class": lambda params: _build_css_class_type(params),
    "color": lambda params: _build_color_type(params),
    "model": lambda params: Model[params.get("model_path")] if params and "model_path" in params else Model(),
    "queryset": lambda params: QuerySet[params.get("model_path")] if params and "model_path" in params else QuerySet(),
    "multichoice": lambda params: MultiChoice,  # MultiChoice handled separately
}

TYPE_CLASSES = TYPE_BUILDERS
