"""
Shared validation utilities for typed props system.

This module provides validation logic that can be used by both Django and
potentially other template engines.
"""

import inspect
from dataclasses import MISSING, is_dataclass
from dataclasses import fields as dataclass_fields
import types
from typing import Any, Dict, Type, Union, get_args, get_origin, get_type_hints

from django.core.exceptions import ValidationError
from django.template import TemplateSyntaxError

from .typed_props import (
    coerce_value,
    is_multichoice_type,
    get_multichoice_values,
    generate_multichoice_flags,
    mark_html_recursive,
)


def _check_coercion_failure(value, coerced_value, actual_type, field_name):
    """
    Check if type coercion failed and return appropriate error message.

    Returns error message if coercion failed, None otherwise.
    """
    # Only check if coercion didn't change the value
    if coerced_value != value:
        return None

    # Check for common type coercion failures
    if actual_type is int and not isinstance(coerced_value, int):
        return f"{field_name}: Cannot convert '{value}' to integer"
    elif actual_type is float and not isinstance(coerced_value, float):
        return f"{field_name}: Cannot convert '{value}' to float"
    elif hasattr(actual_type, "__name__") and actual_type.__name__ == "Decimal":
        if isinstance(value, str) and not isinstance(coerced_value, actual_type):
            return f"{field_name}: Cannot convert '{value}' to decimal"

    return None


def validate_props(props_class: Type, values: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate values against a props class definition.

    Args:
        props_class: The dataclass defining the props
        values: Dictionary of prop values to validate

    Returns:
        Dictionary of cleaned/validated values

    Raises:
        TemplateSyntaxError: If validation fails
    """
    from includecontents.django.errors import enhance_validation_error

    errors = []
    cleaned = {}

    # Get type hints including Annotated metadata
    hints = get_type_hints(props_class, include_extras=True)

    # Get dataclass fields for defaults
    if is_dataclass(props_class):
        dc_fields = {f.name: f for f in dataclass_fields(props_class)}
    else:
        dc_fields = {}

    # Process each field
    for field_name, type_hint in hints.items():
        # Skip private/protected fields
        if field_name.startswith("_"):
            continue

        # Get the value or use default
        if field_name in values:
            value = values[field_name]
        elif field_name in dc_fields:
            field = dc_fields[field_name]
            if field.default is not MISSING:
                value = field.default
            elif field.default_factory is not MISSING:
                value = field.default_factory()
            else:
                # Required field is missing
                errors.append(f"Missing required prop: {field_name}")
                continue
        else:
            # Check if it's Optional
            origin = get_origin(type_hint)
            # Handle both typing.Union and types.UnionType (Python 3.10+ | syntax)
            if origin is Union or (
                hasattr(types, "UnionType") and origin is types.UnionType
            ):
                # Check if None is in the union (making it Optional)
                args = get_args(type_hint)
                if type(None) in args:
                    value = None
                else:
                    errors.append(f"Missing required prop: {field_name}")
                    continue
            else:
                errors.append(f"Missing required prop: {field_name}")
                continue

        # Type coercion using the shared coerce_value function
        coerced_value = coerce_value(value, type_hint)

        # Check for conversion errors after coercion
        if value is not None:
            # Coercion didn't change the value - check if it's a type mismatch we should error on
            actual_type = type_hint

            # Unwrap Optional/Union to get actual type
            origin = get_origin(type_hint)
            # Handle both typing.Union and types.UnionType (Python 3.10+ | syntax)
            if origin is Union or (
                hasattr(types, "UnionType") and origin is types.UnionType
            ):
                args = get_args(type_hint)
                non_none_types = [arg for arg in args if arg is not type(None)]
                actual_type = non_none_types[0] if non_none_types else str

            # Get base type from Annotated
            if hasattr(actual_type, "__metadata__"):
                args = get_args(actual_type)
                if args:
                    # First arg is the actual type
                    actual_type = args[0]

            # Check for type coercion failures
            error_msg = _check_coercion_failure(
                value, coerced_value, actual_type, field_name
            )
            if error_msg:
                errors.append(error_msg)
                continue

            # Check for list item coercion failures
            if get_origin(actual_type) is list:
                # Check if coerced list has unconverted items when expecting int/float
                if isinstance(coerced_value, list):
                    list_args = get_args(actual_type)
                    if list_args:
                        item_type = list_args[0]
                        if item_type is int:
                            for item in coerced_value:
                                if not isinstance(item, int):
                                    # Coercion failed for this item
                                    errors.append(
                                        f"{field_name}: Cannot convert '{item}' to integer"
                                    )
                                    break
                        elif item_type is float:
                            for item in coerced_value:
                                if not isinstance(item, (int, float)):
                                    # Coercion failed for this item
                                    errors.append(
                                        f"{field_name}: Cannot convert '{item}' to float"
                                    )
                                    break

        value = coerced_value

        # Run validators from Annotated types
        if hasattr(type_hint, "__metadata__"):
            for validator in type_hint.__metadata__:
                if callable(validator):
                    try:
                        validator(value)
                    except ValidationError as e:
                        # Get the error message
                        if hasattr(e, "messages"):
                            msg = "; ".join(e.messages)
                        elif hasattr(e, "message"):
                            msg = str(e.message)
                        else:
                            msg = str(e)
                        errors.append(f"{field_name}: {msg}")

        # Check Literal types (including Choice)
        from typing import Literal

        origin = get_origin(type_hint)
        if origin is Literal:
            allowed = get_args(type_hint)
            if value not in allowed:
                errors.append(
                    f"{field_name}: Must be one of {', '.join(repr(a) for a in allowed)}"
                )

        # Recursively mark Html-typed values safe according to type hints
        value = mark_html_recursive(value, type_hint)

        # Generate camelCase boolean flags for MultiChoice types
        if is_multichoice_type(type_hint):
            allowed_values = get_multichoice_values(type_hint)
            flags = generate_multichoice_flags(field_name, value, allowed_values)
            # Add flags to cleaned data (they will be added to template context)
            cleaned.update(flags)

        cleaned[field_name] = value

    # Check for unexpected props
    unexpected = set(values.keys()) - set(hints.keys())
    if unexpected:
        # These will go into attrs if the component uses it
        # But we should track them for the template
        cleaned["_extra_attrs"] = {k: values[k] for k in unexpected}

    # Raise errors if any
    if errors:
        exc = TemplateSyntaxError(f"Props validation failed: {'; '.join(errors)}")

        # Enhance with contextual information
        component_name = getattr(props_class, "_template_path", None)
        props_class_name = getattr(props_class, "__name__", "Unknown")

        enhance_validation_error(
            exc,
            component_name=component_name,
            props_class_name=props_class_name,
            field_errors=errors,
        )

        raise exc

    # Run custom clean method if it exists
    if hasattr(props_class, "clean"):
        try:
            # Create an instance with cleaned values
            instance = props_class(
                **{k: v for k, v in cleaned.items() if not k.startswith("_")}
            )
            instance.clean()
        except ValidationError as e:
            if hasattr(e, "messages"):
                msg = "; ".join(e.messages)
            elif hasattr(e, "message"):
                msg = str(e.message)
            else:
                msg = str(e)

            exc = TemplateSyntaxError(f"Props validation failed: {msg}")

            # Enhance with contextual information
            component_name = getattr(props_class, "_template_path", None)
            props_class_name = getattr(props_class, "__name__", "Unknown")

            enhance_validation_error(
                exc,
                component_name=component_name,
                props_class_name=props_class_name,
                field_errors=[msg],
            )

            raise exc
        except TypeError:
            # Handle cases where the class can't be instantiated
            # Fall back to calling clean as a class method
            if inspect.ismethod(props_class.clean):
                props_class.clean(cleaned)

    return cleaned
