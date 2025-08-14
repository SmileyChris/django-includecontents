"""
Component props system for type-safe validation and registration.

This module provides:
- A decorator for registering component prop classes
- Validation logic using type hints and Django validators
- Integration with the template system
"""

import dataclasses
from dataclasses import dataclass, is_dataclass, fields as dataclass_fields, MISSING
from typing import Any, Dict, Type, get_type_hints, get_origin, get_args, Optional, Union, Literal, Annotated
import inspect

from django.core.exceptions import ValidationError
from django.template import TemplateSyntaxError


# Registry for component props classes
_registry: Dict[str, Type] = {}


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
        
        # Register the props class
        _registry[template_path] = props_class
        
        # Add a marker attribute
        props_class._is_component_props = True
        props_class._template_path = template_path
        
        return props_class
    
    return decorator


def get_props_class(template_path: str) -> Optional[Type]:
    """Get the registered props class for a template path."""
    return _registry.get(template_path)


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
        if field_name.startswith('_'):
            continue
        
        # Special handling for Model and QuerySet classes used directly
        from .prop_types import Model as ModelClass, QuerySet as QuerySetClass
        if type_hint is ModelClass:
            type_hint = ModelClass()
        elif type_hint is QuerySetClass:
            type_hint = QuerySetClass()
            
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
        
        # Type conversion for common types
        if value is not None:
            actual_type = type_hint
            
            # Unwrap Optional (Union with None)
            origin = get_origin(type_hint)
            if origin is Union:
                args = get_args(type_hint)
                # Filter out None to get the actual type
                non_none_types = [arg for arg in args if arg is not type(None)]
                actual_type = non_none_types[0] if non_none_types else str
            
            # Get the base type from Annotated
            if hasattr(actual_type, '__metadata__'):
                origin = get_origin(actual_type)
                if origin is not None:
                    actual_type = origin
            
            # Type coercion
            if actual_type is int and not isinstance(value, int):
                try:
                    value = int(value)
                except (ValueError, TypeError):
                    errors.append(f"{field_name}: Cannot convert '{value}' to integer")
                    continue
            elif actual_type is float and not isinstance(value, float):
                try:
                    value = float(value)
                except (ValueError, TypeError):
                    errors.append(f"{field_name}: Cannot convert '{value}' to float")
                    continue
            elif actual_type is bool and not isinstance(value, bool):
                # Handle string boolean values
                if isinstance(value, str):
                    value = value.lower() in ('true', '1', 'yes', 'on')
                else:
                    value = bool(value)
            
            # Handle List types - convert comma-separated strings
            if get_origin(actual_type) is list:
                if isinstance(value, str):
                    # Split comma-separated string into list
                    value = [item.strip() for item in value.split(',') if item.strip()]
                    # Try to coerce list items to the right type
                    list_args = get_args(actual_type)
                    if list_args:
                        item_type = list_args[0]
                        coerced_items = []
                        for item in value:
                            if item_type is int:
                                try:
                                    coerced_items.append(int(item))
                                except (ValueError, TypeError):
                                    errors.append(f"{field_name}: Cannot convert '{item}' to integer")
                                    break
                            elif item_type is float:
                                try:
                                    coerced_items.append(float(item))
                                except (ValueError, TypeError):
                                    errors.append(f"{field_name}: Cannot convert '{item}' to float")
                                    break
                            elif item_type is bool:
                                coerced_items.append(item.lower() in ('true', '1', 'yes', 'on'))
                            else:
                                # Keep as string
                                coerced_items.append(item)
                        else:
                            # No errors in coercion
                            value = coerced_items
                elif not isinstance(value, list):
                    # Try to convert to list if it's not already
                    value = [value]
        
        # Run validators from Annotated types
        if hasattr(type_hint, '__metadata__'):
            for validator in type_hint.__metadata__:
                if callable(validator):
                    try:
                        validator(value)
                    except ValidationError as e:
                        # Get the error message
                        if hasattr(e, 'messages'):
                            msg = '; '.join(e.messages)
                        elif hasattr(e, 'message'):
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
        
        cleaned[field_name] = value
    
    # Check for unexpected props
    unexpected = set(values.keys()) - set(hints.keys())
    if unexpected:
        # These will go into attrs if the component uses it
        # But we should track them for the template
        cleaned['_extra_attrs'] = {k: values[k] for k in unexpected}
    
    # Raise errors if any
    if errors:
        raise TemplateSyntaxError(
            f"Props validation failed: {'; '.join(errors)}"
        )
    
    # Run custom clean method if it exists
    if hasattr(props_class, 'clean'):
        try:
            # Create an instance with cleaned values
            instance = props_class(**{
                k: v for k, v in cleaned.items() 
                if not k.startswith('_')
            })
            instance.clean()
        except ValidationError as e:
            if hasattr(e, 'messages'):
                msg = '; '.join(e.messages)
            elif hasattr(e, 'message'):
                msg = str(e.message)
            else:
                msg = str(e)
            raise TemplateSyntaxError(f"Props validation failed: {msg}")
        except TypeError as e:
            # Handle cases where the class can't be instantiated
            # Fall back to calling clean as a class method
            if inspect.ismethod(props_class.clean):
                props_class.clean(cleaned)
    
    return cleaned


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
    from .prop_types import TYPE_MAP as DEFAULT_TYPE_MAP, TYPE_CLASSES
    
    type_map = type_map or DEFAULT_TYPE_MAP
    
    # Handle list type without brackets/parentheses
    if type_spec == 'list':
        from typing import List
        return List[str]
    
    # Check for square bracket syntax (new preferred syntax)
    if '[' in type_spec and type_spec.endswith(']'):
        type_name, params_str = type_spec[:-1].split('[', 1)
        
        # Handle choice with square brackets
        if type_name == 'choice':
            choices = [c.strip().strip('\"\'') for c in params_str.split(',')]
            from .prop_types import Choice
            return Choice[tuple(choices)]
        
        # Handle list with square brackets
        if type_name == 'list':
            from typing import List
            if params_str:
                item_type_str = params_str.strip().strip('\"\'')
                item_type = parse_type_spec(item_type_str, type_map)
                return List[item_type]
            else:
                return List[str]
        
        # Handle model with square brackets
        if type_name == 'model':
            from .prop_types import Model
            if params_str:
                model_path = params_str.strip().strip('\"\'')
                return Model[model_path]
            else:
                return Model()
        
        # Handle queryset with square brackets
        if type_name == 'queryset':
            from .prop_types import QuerySet
            if params_str:
                model_path = params_str.strip().strip('\"\'')
                return QuerySet[model_path]
            else:
                return QuerySet()
        
        # Handle parameterized types like text[max_length=100], int[min=18,max=120]
        if type_name in TYPE_CLASSES:
            # Parse key=value parameters
            params = {}
            if params_str:
                for param in params_str.split(','):
                    param = param.strip()
                    if '=' in param:
                        key, value = param.split('=', 1)
                        key = key.strip()
                        value = value.strip().strip('\"\'')
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
        if type_name == 'color':
            from .prop_types import Color
            # params_str could be a format like 'hex', 'rgb', 'rgba'
            return Color[params_str.strip().strip('\"\'')]
    
    # Check for parameterized type with parentheses
    if '(' in type_spec and type_spec.endswith(')'):
        type_name, params_str = type_spec[:-1].split('(', 1)
        
        # Special handling for choice
        if type_name == 'choice':
            # Parse comma-separated choices
            choices = [c.strip().strip('\"\'') for c in params_str.split(',')]
            from .prop_types import Choice
            return Choice[tuple(choices)]
        
        # Special handling for list types
        if type_name == 'list':
            # List can have an item type: list(str), list(int), etc.
            from typing import List
            if params_str:
                item_type_str = params_str.strip().strip('\"\'')
                # Recursively parse the item type
                item_type = parse_type_spec(item_type_str, type_map)
                return List[item_type]
            else:
                # Default to List[str] if no type specified
                return List[str]
        
        # Special handling for model and queryset
        if type_name in ('model', 'queryset'):
            # These take a model path as a single parameter
            model_path = params_str.strip().strip('\"\'')
            
            if type_name == 'model':
                if model_path:
                    # Create validator for specific model
                    def validate_model(value):
                        from django.core.exceptions import ValidationError
                        from django.apps import apps
                        
                        try:
                            app_label, model_name = model_path.split('.')
                            model_class = apps.get_model(app_label, model_name)
                        except (ValueError, LookupError):
                            raise ValidationError(f"Invalid model: {model_path}")
                        
                        if value is not None and not isinstance(value, model_class):
                            raise ValidationError(
                                f"Expected instance of {model_class.__name__}, got {type(value).__name__}"
                            )
                    
                    return Annotated[object, validate_model]
                else:
                    # Return the annotated type for bare Model
                    from .prop_types import Model
                    return Model()
            else:
                if model_path:
                    # Create validator for specific queryset
                    def validate_queryset(value):
                        from django.core.exceptions import ValidationError
                        from django.db.models import QuerySet as DjangoQuerySet
                        from django.apps import apps
                        
                        if value is not None and not isinstance(value, DjangoQuerySet):
                            raise ValidationError(
                                f"Expected QuerySet, got {type(value).__name__}"
                            )
                        
                        if value is not None:
                            try:
                                app_label, model_name = model_path.split('.')
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
                    # Return the annotated type for bare QuerySet
                    from .prop_types import QuerySet
                    return QuerySet()
        
        # Parse key=value parameters
        params = {}
        if params_str:
            for param in params_str.split(','):
                param = param.strip()
                if '=' in param:
                    key, value = param.split('=', 1)
                    key = key.strip()
                    value = value.strip().strip('\"\'')
                    # Try to convert to appropriate type
                    try:
                        value = int(value)
                    except ValueError:
                        try:
                            value = float(value)
                        except ValueError:
                            pass  # Keep as string
                    params[key] = value
        
        # Check if we have a class that supports parameterization
        if type_name in TYPE_CLASSES:
            type_class = TYPE_CLASSES[type_name]
            # Use the square bracket syntax with params dict
            return type_class[params] if params else type_class()
        
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
    from django.template import Variable
    from includecontents.templatetags.includecontents import EnumVariable
    from django.utils.text import smart_split
    import re
    
    props = {}
    
    for bit in smart_split(props_string.strip()):
        if ':' in bit and not bit.startswith('"') and not bit.startswith("'"):
            # New typed syntax: name:type or name:type(params)
            parts = bit.split(':', 1)
            prop_name = parts[0].strip()
            type_spec = parts[1].strip()
            
            # Check for optional marker
            required = True
            if prop_name.endswith('?'):
                prop_name = prop_name[:-1]
                required = False
            
            # Parse the type
            prop_type = parse_type_spec(type_spec)
            
            # Store as a special marker for the template system
            props[prop_name] = {
                'type': prop_type,
                'required': required,
            }
        else:
            # Original syntax
            if match := re.match(r'^(\w+)(?:=(.+?))?,?$', bit):
                attr, value = match.groups()
                if value is None:
                    props[attr] = None  # Required
                else:
                    # Check for enum values
                    if ',' in value and ' ' not in value:
                        # Strip quotes if present
                        if (value.startswith('"') and value.endswith('"')) or \
                           (value.startswith("'") and value.endswith("'")):
                            value = value[1:-1]
                        # Parse enum values
                        enum_values = value.split(',')
                        required = bool(enum_values[0])
                        props[attr] = EnumVariable(enum_values, required)
                    else:
                        props[attr] = Variable(value)
    
    return props