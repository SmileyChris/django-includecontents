"""
Component prop types for type-safe validation using Django validators.

This module provides prop types specifically designed for component props,
avoiding confusion with Django's form fields, model fields, or serializer fields.
"""

import decimal
from typing import Annotated, Literal, TypeVar, Generic, get_args

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
    """String prop type with optional validation."""
    
    def __new__(cls, max_length=None, min_length=None, pattern=None):
        validators = []
        if max_length is not None:
            validators.append(MaxLengthValidator(max_length))
        if min_length is not None:
            validators.append(MinLengthValidator(min_length))
        if pattern is not None:
            validators.append(RegexValidator(pattern))
        return Annotated[str, *validators] if validators else str


class Integer:
    """Integer prop type with optional bounds validation."""
    
    def __new__(cls, min=None, max=None):
        validators = []
        if min is not None:
            validators.append(MinValueValidator(min))
        if max is not None:
            validators.append(MaxValueValidator(max))
        return Annotated[int, *validators] if validators else int


class Decimal:
    """Decimal prop type for precise numeric values."""
    
    def __new__(cls, max_digits=None, decimal_places=None, min=None, max=None):
        validators = []
        if min is not None:
            validators.append(MinValueValidator(min))
        if max is not None:
            validators.append(MaxValueValidator(max))
        if max_digits is not None and decimal_places is not None:
            validators.append(DecimalValidator(max_digits, decimal_places))
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
            items = (items,)
        return Literal[items]


# Django-specific prop types
class ModelInstance:
    """
    Validates that the value is an instance of a specific Django model.
    
    Usage:
        user: ModelInstance('auth.User')
        article: ModelInstance(Article)  # Can pass model class directly
    """
    
    def __new__(cls, model):
        def validate_model_instance(value):
            from django.core.exceptions import ValidationError
            from django.apps import apps
            
            # Get the model class
            if isinstance(model, str):
                try:
                    app_label, model_name = model.split('.')
                    model_class = apps.get_model(app_label, model_name)
                except (ValueError, LookupError):
                    raise ValidationError(f"Invalid model: {model}")
            else:
                model_class = model
            
            # Check if value is an instance of the model
            if value is not None and not isinstance(value, model_class):
                raise ValidationError(
                    f"Expected instance of {model_class.__name__}, got {type(value).__name__}"
                )
        
        return Annotated[object, validate_model_instance]


class QuerySet:
    """
    Validates that the value is a Django QuerySet.
    
    Usage:
        items: QuerySet()  # Any QuerySet
        users: QuerySet('auth.User')  # QuerySet of specific model
    """
    
    def __new__(cls, model=None):
        def validate_queryset(value):
            from django.core.exceptions import ValidationError
            from django.db.models import QuerySet as DjangoQuerySet
            from django.apps import apps
            
            # Check if it's a QuerySet
            if value is not None and not isinstance(value, DjangoQuerySet):
                raise ValidationError(
                    f"Expected QuerySet, got {type(value).__name__}"
                )
            
            # Optionally check the model
            if model and value is not None:
                if isinstance(model, str):
                    try:
                        app_label, model_name = model.split('.')
                        model_class = apps.get_model(app_label, model_name)
                    except (ValueError, LookupError):
                        raise ValidationError(f"Invalid model: {model}")
                else:
                    model_class = model
                
                # Check if QuerySet is of the correct model
                if value.model != model_class:
                    raise ValidationError(
                        f"Expected QuerySet of {model_class.__name__}, "
                        f"got QuerySet of {value.model.__name__}"
                    )
        
        return Annotated[object, validate_queryset]


# Component-specific prop types
class CssClass:
    """CSS class name validation."""
    
    def __new__(cls, pattern=r'^[a-zA-Z][\w-]*(\s+[a-zA-Z][\w-]*)*$'):
        return Annotated[str, RegexValidator(pattern, "Invalid CSS class name")]


class Color:
    """CSS color validation."""
    
    def __new__(cls, format='any'):
        patterns = {
            'hex': r'^#[0-9A-Fa-f]{3}([0-9A-Fa-f]{3})?$',
            'rgb': r'^rgb\(\s*\d{1,3}\s*,\s*\d{1,3}\s*,\s*\d{1,3}\s*\)$',
            'rgba': r'^rgba\(\s*\d{1,3}\s*,\s*\d{1,3}\s*,\s*\d{1,3}\s*,\s*[01]?\.?\d*\s*\)$',
            'any': r'.*',  # Accept any color format
        }
        pattern = patterns.get(format, patterns['any'])
        return Annotated[str, RegexValidator(pattern, f"Invalid {format} color")]


class IconName:
    """Icon name validation (validates against registered icons)."""
    
    def __new__(cls):
        # This will be enhanced to check against registered icons
        # For now, just validate the format
        return Annotated[str, RegexValidator(
            r'^[a-zA-Z0-9][\w:-]*$',
            "Invalid icon name"
        )]


class Html:
    """
    Marker type for HTML content that should be marked safe in templates.
    
    This is a marker type that indicates the content should be treated
    as safe HTML and not escaped when rendered.
    """
    pass


class Json:
    """JSON string that will be parsed and validated."""
    
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
    'text': Text,
    'str': Text,
    'string': Text,
    'int': Integer,
    'integer': Integer,
    'decimal': Decimal,
    'float': Decimal,
    'email': Email,
    'url': Url,
    'slug': Slug,
    'unicode_slug': UnicodeSlug,
    'ip': IPAddress,
    'ipv4': IPAddress,
    'ipv6': IPv6Address,
    'css_class': CssClass,
    'color': Color,
    'icon': IconName,
    'html': Html,
    'json': Json,
    'bool': bool,
    'boolean': bool,
    'model': ModelInstance,
    'queryset': QuerySet,
}