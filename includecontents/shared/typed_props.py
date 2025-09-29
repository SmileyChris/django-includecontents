"""
Shared component props system for type-safe validation and registration.

This module provides the core typed props functionality that can be used
by both Django and potentially Jinja2 template engines.
"""

import logging
import types as _types
from dataclasses import dataclass, is_dataclass
from typing import (
    Annotated,
    Any,
    Dict,
    Optional,
    Type,
    Union,
    get_args,
    get_origin,
)

from django.utils.safestring import mark_safe

# Registry for component props classes
_registry: Dict[str, Type] = {}

# Logger for props system
logger = logging.getLogger(__name__)


def component(template_path: str):
    """
    Decorator to register a props class for a component template.

    Usage:
        @component('components/user-card.html')
        @dataclass
        class UserCardProps:
            name: str
            email: Email
            age: Integer(min=18)
    """

    def decorator(props_class: Type) -> Type:
        # Convert to dataclass if not already
        if not is_dataclass(props_class):
            props_class = dataclass(props_class)

        # Register the props class, warning about collisions
        if template_path in _registry:
            existing_class = _registry[template_path]
            logger.warning(
                "Component already registered for '%s'. "
                "Previous: %s, New: %s (keeping first)",
                template_path,
                existing_class.__name__,
                props_class.__name__,
            )
            # Keep the first registration (don't overwrite)
        else:
            _registry[template_path] = props_class

        # Add a marker attribute
        props_class._is_component_props = True
        props_class._template_path = template_path

        return props_class

    return decorator


def get_props_class(template_path: str) -> Optional[Type]:
    """Get the registered props class for a template path."""
    return _registry.get(template_path)


def list_registered_components() -> list[str]:
    """
    Return list of all registered component template paths.

    This is useful for debugging and introspection, particularly in tests
    and development environments where you need to see what components
    are available.

    Returns:
        List of template paths that have registered props classes
    """
    return list(_registry.keys())


def resolve_props_class_for(path: str) -> Optional[Type]:
    """
    Get props class for a template path with normalization.

    This function tries various path variations to find a matching
    props class, including handling absolute vs relative paths and
    common path prefixes.

    Args:
        path: Template path to look up

    Returns:
        Props class if found, None otherwise
    """
    # Try exact match first
    if path in _registry:
        return _registry[path]

    # Try relative path variations
    from pathlib import Path

    # Try without leading slash
    if path.startswith("/"):
        relative = path.lstrip("/")
        if relative in _registry:
            return _registry[relative]

    # Try with 'templates/' prefix removed (handle both Unix and Windows paths)
    if "templates/" in path or "templates\\" in path:
        # Normalize path separators to forward slashes for consistency
        normalized_path = path.replace("\\", "/")
        if "templates/" in normalized_path:
            parts = normalized_path.split("templates/", 1)
            if len(parts) == 2 and parts[1] in _registry:
                return _registry[parts[1]]

    # Try normalized path variations
    try:
        # Normalize path separators for cross-platform compatibility
        normalized_path = path.replace("\\", "/")
        path_obj = Path(normalized_path)

        # Convert to forward slash notation for consistency
        path_parts = normalized_path.split("/")

        # Look for 'templates' in the path and extract relative part
        if "templates" in path_parts:
            templates_index = path_parts.index("templates")
            if templates_index < len(path_parts) - 1:
                # Get everything after 'templates/'
                relative_parts = path_parts[templates_index + 1 :]
                relative_path = "/".join(relative_parts)
                if relative_path in _registry:
                    return _registry[relative_path]
    except Exception:
        # If path parsing fails, continue with other attempts
        pass

    return None


def clear_registry():
    """
    Clear all registered components.

    This is primarily useful for testing to ensure a clean state
    between test runs. In production, the registry should be populated
    once at startup and remain read-only.

    Note: This modifies global state and should be used carefully.
    """
    _registry.clear()


def coerce_value(value: Any, type_hint: Any) -> Any:
    """
    Coerce a value to match the given type hint.

    Handles:
    - Union/Optional types (strips None, coerces to first non-None type)
    - Annotated types (coerces using origin type)
    - Primitives: int, float, bool, Decimal
    - List types (splits comma-separated strings, coerces items)
    - Returns original value for unknown types
    """
    if value is None:
        return None

    # Handle Union types (including Optional)
    origin = get_origin(type_hint)
    if origin is Union:
        args = get_args(type_hint)
        # Filter out None to get the actual type(s)
        non_none_types = [arg for arg in args if arg is not type(None)]
        if non_none_types:
            # Use the first non-None type for coercion
            return coerce_value(value, non_none_types[0])
        return value

    # Handle Annotated types - coerce using the origin type
    if hasattr(type_hint, "__metadata__"):
        origin = get_origin(type_hint)
        if origin is not None:
            return coerce_value(value, origin)

    # Handle List types
    if origin is list:
        if isinstance(value, str):
            # Split comma-separated string into list
            items = [item.strip() for item in value.split(",") if item.strip()]
        elif not isinstance(value, list):
            # Convert single value to list
            items = [value]
        else:
            items = value

        # Coerce list items if type is specified
        args = get_args(type_hint)
        if args:
            item_type = args[0]
            coerced_items = []
            for item in items:
                coerced_items.append(coerce_value(item, item_type))
            return coerced_items
        return items

    # Handle Decimal type
    if type_hint.__name__ == "Decimal" if hasattr(type_hint, "__name__") else False:
        from decimal import Decimal

        if not isinstance(value, Decimal):
            try:
                return Decimal(str(value))
            except Exception:
                # Let validation handle the error
                return value

    # Handle primitive types
    if type_hint is int and not isinstance(value, int):
        try:
            return int(value)
        except (ValueError, TypeError):
            # Let validation handle the error
            return value
    elif type_hint is float and not isinstance(value, float):
        try:
            return float(value)
        except (ValueError, TypeError):
            # Let validation handle the error
            return value
    elif type_hint is bool and not isinstance(value, bool):
        # Handle string boolean values
        if isinstance(value, str):
            # Any non-empty string that's not explicitly false should be True
            lower_val = value.lower()
            # Check for explicit false values
            if lower_val in ("false", "0", "no", "off", ""):
                return False
            # Check for explicit true values
            elif lower_val in ("true", "1", "yes", "on"):
                return True
            # For Django templates, any non-empty string is truthy
            # But we should be strict here - only accept known values
            return lower_val in ("true", "1", "yes", "on")
        else:
            return bool(value)

    # No coercion needed or unknown type
    return value


def is_html_type(type_hint: Any) -> bool:
    """Return True if the type hint is an Html Annotated marker."""
    try:
        # Direct Annotated Html marker
        if hasattr(type_hint, "__metadata__"):
            # Import here to avoid circular imports
            try:
                from includecontents.django.prop_types import _HTML_MARKER

                if _HTML_MARKER in getattr(type_hint, "__metadata__", ()):
                    return True
            except ImportError:
                pass
        # Bare Html class reference (e.g., nested in containers: list[Html])
        try:
            from includecontents.django.prop_types import Html as HtmlClass

            if type_hint is HtmlClass:
                return True
        except ImportError:
            pass
        return False
    except Exception:
        return False


def is_multichoice_type(type_hint: Any) -> bool:
    """Return True if the type hint is a MultiChoice Annotated marker."""
    try:
        # Direct Annotated MultiChoice marker
        if hasattr(type_hint, "__metadata__"):
            try:
                from includecontents.django.prop_types import _MULTICHOICE_MARKER

                if _MULTICHOICE_MARKER in getattr(type_hint, "__metadata__", ()):
                    return True
            except ImportError:
                pass
        return False
    except Exception:
        return False


def get_multichoice_values(type_hint: Any) -> tuple:
    """Extract the allowed values from a MultiChoice type hint."""
    try:
        if hasattr(type_hint, "__metadata__"):
            metadata = getattr(type_hint, "__metadata__", ())
            # The allowed values are stored as the last item in metadata after the marker
            for item in metadata:
                if isinstance(item, (tuple, list)) and not callable(item):
                    return tuple(item)
        return ()
    except Exception:
        return ()


def generate_multichoice_flags(
    prop_name: str, value: str, allowed_values: tuple
) -> dict:
    """
    Generate camelCase boolean flags for MultiChoice values.

    Args:
        prop_name: The property name (e.g., 'variant')
        value: The space-separated value string (e.g., 'primary large')
        allowed_values: Tuple of allowed values

    Returns:
        Dictionary of camelCase flags (e.g., {'variantPrimary': True, 'variantLarge': True})
    """
    flags = {}

    if not value:
        return flags

    # Split on spaces to get individual values
    selected_values = value.split() if isinstance(value, str) else []

    # Generate camelCase flags for each allowed value
    for allowed_value in allowed_values:
        # Convert hyphens to camelCase (e.g., 'dark-mode' -> 'DarkMode')
        parts = str(allowed_value).split("-")
        camel_value = parts[0] + "".join(p.capitalize() for p in parts[1:])

        # Create the flag name (e.g., 'variant' + 'Primary' -> 'variantPrimary')
        flag_name = prop_name + camel_value[0].upper() + camel_value[1:]

        # Set flag to True if this value is selected, otherwise don't set it
        # (Django templates treat missing variables as False)
        if str(allowed_value) in selected_values:
            flags[flag_name] = True

    return flags


def mark_html_recursive(value: Any, type_hint: Any) -> Any:
    """
    Recursively traverse a value according to the provided type hint and
    mark any Html-typed leaves as safe. Supports Optional/Union, Annotated,
    list/tuple/set/dict container types, and nested combinations thereof.
    """
    if value is None:
        return None

    # If it's directly an Html type, mark safe
    try:
        if is_html_type(type_hint):
            # Only strings should be marked safe; defensive check
            return mark_safe(value) if isinstance(value, str) else value
    except Exception:
        return value

    origin = get_origin(type_hint)
    args = get_args(type_hint)

    # Handle Annotated by recursing into its base type (first arg)
    if origin is Annotated:
        inner = args[0] if args else Any
        return mark_html_recursive(value, inner)

    # Handle Optional/Union by selecting the most appropriate arg
    if origin in (Union, getattr(_types, "UnionType", Union)):
        non_none = [a for a in args if a is not type(None)]  # noqa: E721
        # Try to match container types to value shape first
        for a in non_none:
            a_origin = get_origin(a)
            if a_origin is list and isinstance(value, list):
                return mark_html_recursive(value, a)
            if a_origin is tuple and isinstance(value, tuple):
                return mark_html_recursive(value, a)
            if a_origin is set and isinstance(value, set):
                return mark_html_recursive(value, a)
            if a_origin is dict and isinstance(value, dict):
                return mark_html_recursive(value, a)
            if is_html_type(a) and isinstance(value, str):
                return mark_html_recursive(value, a)
        # Fallback to first non-none arg
        if non_none:
            return mark_html_recursive(value, non_none[0])
        return value

    # Handle containers
    if origin is list and isinstance(value, list):
        item_type = args[0] if args else Any
        return [mark_html_recursive(v, item_type) for v in value]

    if origin is tuple and isinstance(value, tuple):
        if args and args[-1] is Ellipsis:
            # Tuple[T, ...]
            item_type = args[0] if args else Any
            return tuple(mark_html_recursive(v, item_type) for v in value)
        if args and len(args) == len(value):
            return tuple(mark_html_recursive(v, t) for v, t in zip(value, args))
        # Fallback: mark items as Html? Keep unchanged to avoid over-marking
        return value

    if origin is set and isinstance(value, set):
        item_type = args[0] if args else Any
        return {mark_html_recursive(v, item_type) for v in value}

    if origin is dict and isinstance(value, dict):
        # Recurse into values only
        key_type = args[0] if args else Any
        val_type = args[1] if len(args) > 1 else Any
        return {k: mark_html_recursive(v, val_type) for k, v in value.items()}

    return value


def parse_template_props(props_string: str) -> Dict[str, Any]:
    """
    Parse props definition from template comment.
    Supports syntax: name:type, name?:type (optional), name:type=default
    Returns dict with prop info including 'required' and 'type' keys.
    """
    import re
    from django.utils.text import smart_split

    props = {}
    for bit in smart_split(props_string.strip()):
        if ":" in bit and not bit.startswith('"') and not bit.startswith("'"):
            # Handle typed syntax: name:type or name?:type or name:type=default
            if "=" in bit:
                # Has default value: name:type=default
                name_type_part, default_part = bit.split("=", 1)
                required = False  # Has default, so optional
            else:
                # No default: name:type or name?:type
                name_type_part = bit
                required = True  # Default to required

            # Split name and type
            parts = name_type_part.split(":", 1)
            prop_name = parts[0].strip()
            type_spec = parts[1].strip() if len(parts) > 1 else "str"

            # Check for optional marker
            if prop_name.endswith("?"):
                prop_name = prop_name[:-1]
                required = False

            # Parse type spec - simplified version
            prop_type = _parse_simple_type_spec(type_spec)

            props[prop_name] = {
                "type": prop_type,
                "required": required,
            }
        else:
            # Original syntax without type
            if match := re.match(r"^(\w+)(?:=(.+?))?,?$", bit):
                attr, value = match.groups()
                props[attr] = {
                    "type": str,  # Default type
                    "required": value is None,
                }
    return props


def _parse_simple_type_spec(type_spec: str) -> Any:
    """Simple type spec parser for template props testing."""
    from typing import Annotated, List

    # Handle basic types
    if type_spec == "text" or type_spec == "str":
        return str
    elif type_spec == "int":
        return int
    elif type_spec == "email":
        return str  # Simplified - just treat as string for testing
    elif type_spec == "html":
        # Return the Html type (Annotated string with HTML marker)
        return Annotated[str, _HTML_MARKER]
    elif type_spec.startswith("list[") and type_spec.endswith("]"):
        # Handle list[type] syntax
        inner_type = type_spec[5:-1]  # Remove "list[" and "]"
        inner_parsed = _parse_simple_type_spec(inner_type)
        return List[inner_parsed]
    elif type_spec.startswith("choice[") and type_spec.endswith("]"):
        # choice[admin,user,guest] -> just return a marker
        choices_str = type_spec[7:-1]  # Remove "choice[" and "]"
        choices = [c.strip().strip("\"'") for c in choices_str.split(",")]
        return {"type": "choice", "choices": choices}
    else:
        return str  # Default fallback
