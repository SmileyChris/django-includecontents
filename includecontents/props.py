"""
Component props system for type-safe validation and registration.

This module provides:
- A decorator for registering component prop classes
- Validation logic using type hints and Django validators
- Integration with the template system
"""

import inspect
import logging
import types as _types
from dataclasses import MISSING, dataclass, is_dataclass
from dataclasses import fields as dataclass_fields
from typing import (
    Annotated,
    Any,
    Dict,
    Literal,
    Optional,
    Type,
    Union,
    get_args,
    get_origin,
    get_type_hints,
)

from django.core.exceptions import ValidationError
from django.template import TemplateSyntaxError
from django.utils.safestring import mark_safe

from .errors import enhance_validation_error

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
        Path(normalized_path)

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

        # Special handling for Model, QuerySet, and Html classes used directly
        from .prop_types import (
            Html as HtmlClass,
        )
        from .prop_types import (
            Model as ModelClass,
        )
        from .prop_types import (
            QuerySet as QuerySetClass,
        )

        if type_hint is ModelClass:
            type_hint = ModelClass()
        elif type_hint is QuerySetClass:
            type_hint = QuerySetClass()
        elif type_hint is HtmlClass:
            type_hint = HtmlClass()

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
            if origin is Union:
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
            if origin is Union:
                args = get_args(type_hint)
                non_none_types = [arg for arg in args if arg is not type(None)]
                actual_type = non_none_types[0] if non_none_types else str

            # Get base type from Annotated
            if hasattr(actual_type, "__metadata__"):
                origin = get_origin(actual_type)
                if origin is not None:
                    actual_type = origin

            # Check for type mismatches that should error
            if (
                actual_type is int
                and not isinstance(coerced_value, int)
                and coerced_value == value
            ):
                error_msg = f"{field_name}: Cannot convert '{value}' to integer"
                errors.append(error_msg)
                continue
            elif (
                actual_type is float
                and not isinstance(coerced_value, float)
                and coerced_value == value
            ):
                error_msg = f"{field_name}: Cannot convert '{value}' to float"
                errors.append(error_msg)
                continue
            elif get_origin(actual_type) is list:
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


def is_html_type(type_hint: Any) -> bool:
    """Return True if the type hint is an Html Annotated marker."""
    try:
        # Direct Annotated Html marker
        if hasattr(type_hint, "__metadata__"):
            from .prop_types import _HTML_MARKER

            if _HTML_MARKER in getattr(type_hint, "__metadata__", ()):  # type: ignore[attr-defined]
                return True
        # Bare Html class reference (e.g., nested in containers: list[Html])
        try:
            from .prop_types import Html as HtmlClass

            if type_hint is HtmlClass:
                return True
        except Exception:
            pass
        return False
    except Exception:
        return False


def is_multichoice_type(type_hint: Any) -> bool:
    """Return True if the type hint is a MultiChoice Annotated marker."""
    try:
        # Direct Annotated MultiChoice marker
        if hasattr(type_hint, "__metadata__"):
            from .prop_types import _MULTICHOICE_MARKER

            if _MULTICHOICE_MARKER in getattr(type_hint, "__metadata__", ()):  # type: ignore[attr-defined]
                return True
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
        args[0] if args else Any
        val_type = args[1] if len(args) > 1 else Any
        return {k: mark_html_recursive(v, val_type) for k, v in value.items()}

    return value


def parse_type_spec(type_spec: str, type_map: Dict[str, Any] = None):
    """
    Parse a type specification from template props syntax.

    Examples:
        'text' -> Text
        'int(min=18,max=120)' -> Integer(min=18, max=120)
        'choice[admin,user,guest]' -> Literal['admin', 'user', 'guest']
        'model[auth.User]' -> Model['auth.User']
        'queryset[blog.Article]' -> QuerySet['blog.Article']
        'list[str]' -> List[str]
        'list[int]' -> List[int]
    """
    from .prop_types import TYPE_CLASSES
    from .prop_types import TYPE_MAP as DEFAULT_TYPE_MAP

    type_map = type_map or DEFAULT_TYPE_MAP

    # Handle list type without brackets/parentheses
    if type_spec == "list":
        from typing import List

        return List[str]

    # Check for square bracket syntax (new preferred syntax)
    if "[" in type_spec and type_spec.endswith("]"):
        type_name, params_str = type_spec[:-1].split("[", 1)

        # Handle choice with square brackets
        if type_name == "choice":
            choices = [c.strip().strip("\"'") for c in params_str.split(",")]
            return Literal[tuple(choices)]

        # Handle list with square brackets
        if type_name == "list":
            from typing import List

            if params_str:
                item_type_str = params_str.strip().strip("\"'")
                item_type = parse_type_spec(item_type_str, type_map)
                return List[item_type]
            else:
                return List[str]

        # Handle model with square brackets
        if type_name == "model":
            from .prop_types import Model
            from django.db import models

            if params_str:
                model_path = params_str.strip().strip("\"'")
                return Model[model_path]
            else:
                # Bare model requires subscripting - use models.Model for "any model"
                return Model[models.Model]

        # Handle queryset with square brackets
        if type_name == "queryset":
            from .prop_types import QuerySet
            from django.db import models

            if params_str:
                model_path = params_str.strip().strip("\"'")
                return QuerySet[model_path]
            else:
                # Bare queryset requires subscripting - use models.Model for "any queryset"
                return QuerySet[models.Model]

        # Handle parameterized types like text[max_length=100], int[min=18,max=120]
        if type_name in TYPE_CLASSES:
            # Parse key=value parameters
            params = {}
            if params_str:
                for param in params_str.split(","):
                    param = param.strip()
                    if "=" in param:
                        key, value = param.split("=", 1)
                        key = key.strip()
                        value = value.strip().strip("\"'")
                        # Try to convert to appropriate type
                        try:
                            value = int(value)
                        except ValueError:
                            try:
                                value = float(value)
                            except ValueError:
                                pass  # Keep as string
                        params[key] = value

            type_class = TYPE_CLASSES[type_name]
            # Use the square bracket syntax with params dict
            return type_class[params] if params else type_class()

    # Check for parameterized type with parentheses
    if "(" in type_spec and type_spec.endswith(")"):
        type_name, params_str = type_spec[:-1].split("(", 1)

        # Special handling for choice
        if type_name == "choice":
            # Parse comma-separated choices
            choices = [c.strip().strip("\"'") for c in params_str.split(",")]
            return Literal[tuple(choices)]

        # Special handling for list types
        if type_name == "list":
            # List can have an item type: list(str), list(int), etc.
            from typing import List

            if params_str:
                item_type_str = params_str.strip().strip("\"'")
                # Recursively parse the item type
                item_type = parse_type_spec(item_type_str, type_map)
                return List[item_type]
            else:
                # Default to List[str] if no type specified
                return List[str]

        # Special handling for model and queryset
        if type_name in ("model", "queryset"):
            # These take a model path as a single parameter
            model_path = params_str.strip().strip("\"'")

            if type_name == "model":
                if model_path:
                    # Create validator for specific model
                    def validate_model(value):
                        from django.apps import apps
                        from django.core.exceptions import ValidationError

                        try:
                            app_label, model_name = model_path.split(".")
                            model_class = apps.get_model(app_label, model_name)
                        except (ValueError, LookupError):
                            raise ValidationError(f"Invalid model: {model_path}")

                        if value is not None and not isinstance(value, model_class):
                            raise ValidationError(
                                f"Expected instance of {model_class.__name__}, got {type(value).__name__}"
                            )

                    return Annotated[object, validate_model]
                else:
                    # Bare model requires subscripting - use models.Model for "any model"
                    from .prop_types import Model
                    from django.db import models

                    return Model[models.Model]
            else:
                if model_path:
                    # Create validator for specific queryset
                    def validate_queryset(value):
                        from django.apps import apps
                        from django.core.exceptions import ValidationError
                        from django.db.models import QuerySet as DjangoQuerySet

                        if value is not None and not isinstance(value, DjangoQuerySet):
                            raise ValidationError(
                                f"Expected QuerySet, got {type(value).__name__}"
                            )

                        if value is not None:
                            try:
                                app_label, model_name = model_path.split(".")
                                model_class = apps.get_model(app_label, model_name)
                            except (ValueError, LookupError):
                                raise ValidationError(f"Invalid model: {model_path}")

                            if value.model != model_class:
                                raise ValidationError(
                                    f"Expected QuerySet of {model_class.__name__}, "
                                    f"got QuerySet of {value.model.__name__}"
                                )

                    return Annotated[object, validate_queryset]
                else:
                    # Bare queryset requires subscripting - use models.Model for "any queryset"
                    from .prop_types import QuerySet
                    from django.db import models

                    return QuerySet[models.Model]

        # Parse key=value parameters
        params = {}
        if params_str:
            for param in params_str.split(","):
                param = param.strip()
                if "=" in param:
                    key, value = param.split("=", 1)
                    key = key.strip()
                    value = value.strip().strip("\"'")
                    # Try to convert to appropriate type
                    try:
                        value = int(value)
                    except ValueError:
                        try:
                            value = float(value)
                        except ValueError:
                            pass  # Keep as string
                    params[key] = value

        # Check if we have a builder function that supports parameterization
        if type_name in TYPE_CLASSES:
            builder_func = TYPE_CLASSES[type_name]
            # Call the builder function with params dict
            return builder_func(params) if params else builder_func({})

        # Fall back to the default type map
        type_obj = type_map.get(type_name)
        if type_obj is not None:
            return type_obj

    # Simple type lookup
    return type_map.get(type_spec, str)  # Default to string


def parse_template_props(props_string: str) -> Dict[str, Any]:
    """
    Parse props definition from template comment.

    Supports both old and new syntax:
        {# props title #} - Simple required prop
        {# props title="Default" #} - Prop with default
        {# props title:text email:email age:int(min=18) #} - Typed props
    """
    import re

    from django.template import Variable
    from django.utils.text import smart_split

    from includecontents.templatetags.includecontents import EnumVariable

    props = {}

    for bit in smart_split(props_string.strip()):
        if ":" in bit and not bit.startswith('"') and not bit.startswith("'"):
            # New typed syntax: name:type or name:type(params)
            parts = bit.split(":", 1)
            prop_name = parts[0].strip()
            type_spec = parts[1].strip()

            # Check for optional marker
            required = True
            if prop_name.endswith("?"):
                prop_name = prop_name[:-1]
                required = False

            # Parse the type
            prop_type = parse_type_spec(type_spec)

            # Store as a special marker for the template system
            props[prop_name] = {
                "type": prop_type,
                "required": required,
            }
        else:
            # Original syntax
            if match := re.match(r"^(\w+)(?:=(.+?))?,?$", bit):
                attr, value = match.groups()
                if value is None:
                    props[attr] = None  # Required
                else:
                    # Check for enum values
                    if "," in value and " " not in value:
                        # Strip quotes if present
                        if (value.startswith('"') and value.endswith('"')) or (
                            value.startswith("'") and value.endswith("'")
                        ):
                            value = value[1:-1]
                        # Parse enum values
                        enum_values = value.split(",")
                        required = bool(enum_values[0])
                        props[attr] = EnumVariable(enum_values, required)
                    else:
                        props[attr] = Variable(value)

    return props
