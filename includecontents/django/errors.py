"""
Error enhancement utilities for better debugging and development experience.

This module provides utilities for enhancing exceptions with additional context,
supporting both Python 3.11+ Exception.add_note() and fallback behavior for
older Python versions.
"""


def enhance_error(exc: Exception, note: str) -> Exception:
    """
    Add contextual note to exception.

    Uses Exception.add_note() when available (Python 3.11+) for most exceptions,
    but falls back to args modification for Django's TemplateDoesNotExist
    which doesn't display notes in its __str__ method.

    Args:
        exc: The exception to enhance
        note: The contextual note to add

    Returns:
        The enhanced exception (same instance)
    """
    # Check if this is Django's TemplateDoesNotExist which doesn't display notes
    from django.template import TemplateDoesNotExist

    if isinstance(exc, TemplateDoesNotExist) or not hasattr(exc, 'add_note'):
        # Use args modification for Django compatibility or older Python
        if exc.args:
            # Append note to the first argument (usually the message)
            exc.args = (f"{exc.args[0]}\n\n{note}",) + exc.args[1:]
        else:
            # No existing args, make the note the primary message
            exc.args = (note,)
    else:
        # Use add_note for Python 3.11+ non-Django exceptions
        exc.add_note(note)

    return exc


def enhance_validation_error(exc: Exception, component_name: str = None,
                           props_class_name: str = None, field_errors: list = None) -> Exception:
    """
    Add comprehensive validation context to an exception.

    Args:
        exc: The exception to enhance
        component_name: Name/path of the component template
        props_class_name: Name of the props class
        field_errors: List of individual field error messages

    Returns:
        The enhanced exception (same instance)
    """
    if component_name:
        enhance_error(exc, f"Component: {component_name}")

    if props_class_name:
        enhance_error(exc, f"Props class: {props_class_name}")

    if field_errors:
        # Show first few errors as individual notes for clarity
        for error in field_errors[:3]:  # Limit to avoid overwhelming output
            enhance_error(exc, f"  • {error}")

        if len(field_errors) > 3:
            enhance_error(exc, f"  ... and {len(field_errors) - 3} more error(s)")

    return exc


def enhance_coercion_error(exc: Exception, field_name: str, value, expected_type,
                          hint: str = None) -> Exception:
    """
    Add type coercion context to an exception.

    Args:
        exc: The exception to enhance
        field_name: Name of the field being coerced
        value: The value that failed coercion
        expected_type: The type we were trying to coerce to
        hint: Optional hint message for the user

    Returns:
        The enhanced exception (same instance)
    """
    enhance_error(exc, f"Field: {field_name}")
    enhance_error(exc, f"Expected type: {getattr(expected_type, '__name__', str(expected_type))}")
    enhance_error(exc, f"Received value: {value!r} (type: {type(value).__name__})")

    if hint:
        enhance_error(exc, f"Hint: {hint}")
    elif expected_type is int:
        enhance_error(exc, "Hint: Ensure the value is a valid integer")
    elif expected_type is float:
        enhance_error(exc, "Hint: Ensure the value is a valid number")
    elif expected_type is bool:
        enhance_error(exc, "Hint: Valid boolean values are: true, false, 1, 0, yes, no, on, off")

    return exc