"""
Shared template parser utilities for prop type specifications.

This module provides type parsing functionality that can be used by both
Django and potentially other template engines.
"""

from typing import Any, Dict, List
from typing import Literal


def parse_type_spec(type_spec: str, type_map: Dict[str, Any] = None):
    """
    Parse a type specification from template props syntax.

    Examples:
        'text' -> Text
        'int(min=18,max=120)' -> Integer(min=18, max=120)
        'choice[admin,user,guest]' -> Choice['admin', 'user', 'guest']
        'model[auth.User]' -> Model['auth.User']
        'queryset[blog.Article]' -> QuerySet['blog.Article']
        'list[str]' -> List[str]
        'list[int]' -> List[int]
    """
    # Import Django-specific types here to avoid circular imports
    try:
        from includecontents.django.prop_types import (
            TYPE_CLASSES,
            TYPE_MAP as DEFAULT_TYPE_MAP,
        )
    except ImportError:
        # If Django types aren't available, provide basic fallback
        DEFAULT_TYPE_MAP = {
            "text": str,
            "str": str,
            "string": str,
            "int": int,
            "integer": int,
            "bool": bool,
            "boolean": bool,
        }
        TYPE_CLASSES = {}

    type_map = type_map or DEFAULT_TYPE_MAP

    # Handle list type without brackets/parentheses
    if type_spec == "list":
        return List[str]

    # Check for square bracket syntax (new preferred syntax)
    if "[" in type_spec and type_spec.endswith("]"):
        type_name, params_str = type_spec[:-1].split("[", 1)

        # Handle choice with square brackets
        if type_name == "choice":
            choices = [c.strip().strip("\"'") for c in params_str.split(",")]
            try:
                from includecontents.django.prop_types import Choice

                return Choice[tuple(choices)]
            except ImportError:
                return Literal[tuple(choices)]

        # Handle list with square brackets
        if type_name == "list":
            if params_str:
                item_type_str = params_str.strip().strip("\"'")
                item_type = parse_type_spec(item_type_str, type_map)
                return List[item_type]
            else:
                return List[str]

        # Handle model with square brackets
        if type_name == "model":
            try:
                from includecontents.django.prop_types import Model

                if params_str:
                    model_path = params_str.strip().strip("\"'")
                    return Model[model_path]
                else:
                    return Model()
            except ImportError:
                return object  # Fallback for non-Django environments

        # Handle queryset with square brackets
        if type_name == "queryset":
            try:
                from includecontents.django.prop_types import QuerySet

                if params_str:
                    model_path = params_str.strip().strip("\"'")
                    return QuerySet[model_path]
                else:
                    return QuerySet()
            except ImportError:
                return object  # Fallback for non-Django environments

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

        # Handle Color with format like color[hex]
        if type_name == "color":
            try:
                from includecontents.django.prop_types import Color

                # params_str could be a format like 'hex', 'rgb', 'rgba'
                return Color[params_str.strip().strip("\"'")]
            except ImportError:
                return str

    # Check for parameterized type with parentheses
    if "(" in type_spec and type_spec.endswith(")"):
        type_name, params_str = type_spec[:-1].split("(", 1)

        # Special handling for choice
        if type_name == "choice":
            # Parse comma-separated choices
            choices = [c.strip().strip("\"'") for c in params_str.split(",")]
            try:
                from includecontents.django.prop_types import Choice

                return Choice[tuple(choices)]
            except ImportError:
                return Literal[tuple(choices)]

        # Special handling for list types
        if type_name == "list":
            # List can have an item type: list(str), list(int), etc.
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
                try:
                    from includecontents.django.prop_types import Model

                    if model_path:
                        return Model[model_path]
                    else:
                        return Model()
                except ImportError:
                    return object

            else:  # queryset
                try:
                    from includecontents.django.prop_types import QuerySet

                    if model_path:
                        return QuerySet[model_path]
                    else:
                        return QuerySet()
                except ImportError:
                    return object

        # Handle other parameterized types
        if type_name in TYPE_CLASSES:
            # Parse key=value parameters from parentheses syntax
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
            return type_class(**params) if params else type_class()

    # Simple type lookup
    if type_spec in type_map:
        return type_map[type_spec]

    # Default fallback
    return str
