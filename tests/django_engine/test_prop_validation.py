"""
Tests for the prop_types validation system.
"""

import pytest
from dataclasses import dataclass
from typing import Optional, Literal
from django.template import TemplateSyntaxError
from django.template.loader import render_to_string
from django.core.exceptions import ValidationError

from includecontents.django.prop_types import (
    Text, Integer, Email, Url, Choice, CssClass, MinMax, Decimal, Color
)
from includecontents.shared.typed_props import component
from includecontents.shared.validation import validate_props
from includecontents.shared.template_parser import parse_type_spec


class TestPropTypes:
    """Test the prop_types module."""
    
    def test_text_type(self):
        """Test Text prop type with validation."""
        # Basic text
        text_type = Text()
        assert text_type is str
        
        # Text with max length using square brackets
        text_type = Text[{'max_length': 10}]
        assert hasattr(text_type, '__metadata__')
        assert len(text_type.__metadata__) == 1
        
        # Text with multiple validators using square brackets
        text_type = Text[{'max_length': 10, 'min_length': 2, 'pattern': r'^[A-Z]'}]
        assert len(text_type.__metadata__) == 3
    
    def test_integer_type(self):
        """Test Integer prop type with bounds."""
        # Basic integer
        int_type = Integer()
        assert int_type is int
        
        # Integer with min using square brackets
        int_type = Integer[{'min': 18}]
        assert hasattr(int_type, '__metadata__')
        assert len(int_type.__metadata__) == 1
        
        # Integer with min and max using square brackets
        int_type = Integer[{'min': 18, 'max': 120}]
        assert len(int_type.__metadata__) == 2
    
    def test_decimal_type(self):
        """Test Decimal prop type with validation."""
        import decimal
        
        # Basic decimal
        decimal_type = Decimal()
        assert decimal_type is decimal.Decimal
        
        # Decimal with bounds using square brackets
        decimal_type = Decimal[{'min': 0, 'max': 999.99}]
        assert hasattr(decimal_type, '__metadata__')
        assert len(decimal_type.__metadata__) == 2
        
        # Decimal with precision using square brackets
        decimal_type = Decimal[{'max_digits': 10, 'decimal_places': 2}]
        assert hasattr(decimal_type, '__metadata__')
        assert len(decimal_type.__metadata__) == 1
    
    def test_choice_type(self):
        """Test Choice prop type."""
        # Single choice
        choice_type = Choice['admin']
        assert choice_type == Literal['admin']
        
        # Multiple choices
        choice_type = Choice['admin', 'user', 'guest']
        assert choice_type == Literal['admin', 'user', 'guest']
    
    def test_color_type(self):
        """Test Color prop type with format validation."""
        # Basic color (any format)
        color_type = Color()
        assert color_type is str
        
        # Color with hex format using square brackets
        color_type = Color['hex']
        assert hasattr(color_type, '__metadata__')
        
        # Color with rgb format using square brackets
        color_type = Color['rgb']
        assert hasattr(color_type, '__metadata__')
        
        # Color with rgba format using square brackets
        color_type = Color['rgba']
        assert hasattr(color_type, '__metadata__')
    
    def test_predefined_types(self):
        """Test predefined prop types."""
        assert hasattr(Email, '__metadata__')
        assert hasattr(Url, '__metadata__')
        
        # CssClass with default pattern
        css_type = CssClass()
        assert hasattr(css_type, '__metadata__')
        
        # CssClass with custom pattern using square brackets
        css_type = CssClass[{'pattern': r'^custom-pattern$'}]
        assert hasattr(css_type, '__metadata__')
        
        # MinMax helper
        age_type = MinMax(0, 100)
        assert hasattr(age_type, '__metadata__')
        assert len(age_type.__metadata__) == 2


class TestPropsValidation:
    """Test the props validation system."""
    
    def test_simple_props_class(self):
        """Test a simple props class validation."""
        @dataclass
        class SimpleProps:
            name: str
            age: int = 25
        
        # Valid data
        result = validate_props(SimpleProps, {'name': 'John', 'age': 30})
        assert result['name'] == 'John'
        assert result['age'] == 30
        
        # Using default
        result = validate_props(SimpleProps, {'name': 'Jane'})
        assert result['name'] == 'Jane'
        assert result['age'] == 25
        
        # Missing required field
        with pytest.raises(TemplateSyntaxError) as exc_info:
            validate_props(SimpleProps, {'age': 30})
        assert 'Missing required prop: name' in str(exc_info.value)
    
    def test_typed_props_validation(self):
        """Test props with type validation."""
        @dataclass
        class TypedProps:
            email: Email
            age: MinMax(18, 120)
            website: Optional[Url] = None
        
        # Valid data
        result = validate_props(TypedProps, {
            'email': 'test@example.com',
            'age': 25
        })
        assert result['email'] == 'test@example.com'
        assert result['age'] == 25
        assert result['website'] is None
        
        # Invalid email
        with pytest.raises(TemplateSyntaxError) as exc_info:
            validate_props(TypedProps, {
                'email': 'not-an-email',
                'age': 25
            })
        assert 'email' in str(exc_info.value).lower()
        
        # Age out of bounds
        with pytest.raises(TemplateSyntaxError) as exc_info:
            validate_props(TypedProps, {
                'email': 'test@example.com',
                'age': 150
            })
        assert 'age' in str(exc_info.value).lower()
    
    def test_choice_validation(self):
        """Test Choice/Literal validation."""
        @dataclass
        class ChoiceProps:
            role: Choice['admin', 'user', 'guest']
            size: Literal['sm', 'md', 'lg'] = 'md'
        
        # Valid choice
        result = validate_props(ChoiceProps, {'role': 'admin'})
        assert result['role'] == 'admin'
        assert result['size'] == 'md'
        
        # Invalid choice
        with pytest.raises(TemplateSyntaxError) as exc_info:
            validate_props(ChoiceProps, {'role': 'superuser'})
        assert 'Must be one of' in str(exc_info.value)
        assert 'admin' in str(exc_info.value)
    
    def test_type_coercion(self):
        """Test automatic type coercion."""
        @dataclass
        class CoercionProps:
            age: int
            active: bool
            rating: float
        
        # String to int/float/bool
        result = validate_props(CoercionProps, {
            'age': '25',
            'active': 'true',
            'rating': '4.5'
        })
        assert result['age'] == 25
        assert result['active'] is True
        assert result['rating'] == 4.5
        
        # Boolean string variations
        for true_val in ['true', 'True', '1', 'yes', 'on']:
            result = validate_props(CoercionProps, {
                'age': 25,
                'active': true_val,
                'rating': 4.5
            })
            assert result['active'] is True
        
        for false_val in ['false', 'False', '0', 'no', 'off', '']:
            result = validate_props(CoercionProps, {
                'age': 25,
                'active': false_val,
                'rating': 4.5
            })
            assert result['active'] is False
    
    def test_custom_clean_method(self):
        """Test custom clean method on props class."""
        @dataclass
        class PropsWithClean:
            password: str
            confirm_password: str
            
            def clean(self):
                if self.password != self.confirm_password:
                    raise ValidationError("Passwords don't match")
        
        # Valid - passwords match
        result = validate_props(PropsWithClean, {
            'password': 'secret123',
            'confirm_password': 'secret123'
        })
        assert result['password'] == 'secret123'
        
        # Invalid - passwords don't match
        with pytest.raises(TemplateSyntaxError) as exc_info:
            validate_props(PropsWithClean, {
                'password': 'secret123',
                'confirm_password': 'different'
            })
        assert "Passwords don't match" in str(exc_info.value)
    
    def test_extra_attrs(self):
        """Test handling of extra attributes."""
        @dataclass
        class StrictProps:
            name: str
        
        # Extra attributes are collected
        result = validate_props(StrictProps, {
            'name': 'John',
            'extra1': 'value1',
            'extra2': 'value2'
        })
        assert result['name'] == 'John'
        assert '_extra_attrs' in result
        assert result['_extra_attrs']['extra1'] == 'value1'
        assert result['_extra_attrs']['extra2'] == 'value2'
    
    def test_optional_props_validation(self):
        """Test that optional props allow missing or None values."""
        from typing import Optional
        
        @dataclass
        class OptionalProps:
            required_name: str
            optional_email: Optional[Email] = None
            optional_age: Optional[int] = None
            optional_role: Optional[Choice['admin', 'user']] = None
        
        # Test with only required prop
        result = validate_props(OptionalProps, {'required_name': 'John'})
        assert result['required_name'] == 'John'
        assert result['optional_email'] is None
        assert result['optional_age'] is None
        assert result['optional_role'] is None
        
        # Test with some optional props provided
        result = validate_props(OptionalProps, {
            'required_name': 'Jane',
            'optional_age': 25,
            'optional_role': 'admin'
        })
        assert result['required_name'] == 'Jane'
        assert result['optional_email'] is None
        assert result['optional_age'] == 25
        assert result['optional_role'] == 'admin'
        
        # Test that missing required prop fails
        with pytest.raises(TemplateSyntaxError) as exc_info:
            validate_props(OptionalProps, {'optional_age': 30})
        assert 'Missing required prop: required_name' in str(exc_info.value)
        
        # Test that None is accepted for optional props
        result = validate_props(OptionalProps, {
            'required_name': 'Bob',
            'optional_email': None,
            'optional_age': None
        })
        assert result['optional_email'] is None
        assert result['optional_age'] is None
    
    def test_list_coercion_from_string(self):
        """Test that List types handle comma-separated strings."""
        from typing import List
        
        @dataclass
        class ListProps:
            tags: List[str]
            numbers: List[int]
            flags: List[bool] = None
        
        # Test comma-separated string -> List[str]
        result = validate_props(ListProps, {
            'tags': 'python, django, web',
            'numbers': '1, 2, 3, 4'
        })
        assert result['tags'] == ['python', 'django', 'web']
        assert result['numbers'] == [1, 2, 3, 4]
        
        # Test single value -> List
        result = validate_props(ListProps, {
            'tags': 'single-tag',
            'numbers': 42
        })
        assert result['tags'] == ['single-tag']
        assert result['numbers'] == [42]
        
        # Test already a list
        result = validate_props(ListProps, {
            'tags': ['tag1', 'tag2'],
            'numbers': [10, 20]
        })
        assert result['tags'] == ['tag1', 'tag2']
        assert result['numbers'] == [10, 20]
        
        # Test boolean list from string
        result = validate_props(ListProps, {
            'tags': 'test',
            'numbers': '1',
            'flags': 'true, false, yes, no'
        })
        assert result['flags'] == [True, False, True, False]
        
        # Test error on invalid int conversion
        with pytest.raises(TemplateSyntaxError) as exc_info:
            validate_props(ListProps, {
                'tags': 'test',
                'numbers': '1, two, 3'
            })
        assert "Cannot convert 'two' to integer" in str(exc_info.value)


class TestParseTypeSpec:
    """Test parsing type specifications from template syntax."""
    
    def test_simple_types(self):
        """Test parsing simple type names."""
        # Text() returns str
        assert parse_type_spec('text') == str
        # Integer() returns int
        assert parse_type_spec('int') == int
        # Email and Url are pre-configured Annotated types
        assert parse_type_spec('email') == Email
        assert parse_type_spec('url') == Url
    
    def test_parameterized_types(self):
        """Test parsing types with parameters."""
        # Integer with min
        int_type = parse_type_spec('int(min=18)')
        assert hasattr(int_type, '__metadata__')
        
        # Integer with min and max
        int_type = parse_type_spec('int(min=18,max=120)')
        assert hasattr(int_type, '__metadata__')
        assert len(int_type.__metadata__) == 2
        
        # Text with max_length
        text_type = parse_type_spec('text(max_length=100)')
        assert hasattr(text_type, '__metadata__')
    
    def test_choice_parsing(self):
        """Test parsing choice types."""
        # Test parentheses syntax (backward compatibility)
        choice_type = parse_type_spec('choice(admin,user,guest)')
        from typing import get_origin, get_args
        assert get_origin(choice_type) is Literal
        assert get_args(choice_type) == ('admin', 'user', 'guest')
        
        # Test square bracket syntax (preferred)
        choice_type = parse_type_spec('choice[admin,user,guest]')
        assert get_origin(choice_type) is Literal
        assert get_args(choice_type) == ('admin', 'user', 'guest')
    
    def test_list_type_parsing(self):
        """Test parsing list types from template syntax."""
        from typing import List, get_origin, get_args
        
        # List with type parameter
        list_type = parse_type_spec('list(str)')
        assert get_origin(list_type) is list
        # Text() returns str, so list(str) should have str as its type
        assert get_args(list_type)[0] == str
        
        # List with int type
        list_type = parse_type_spec('list(int)')
        assert get_origin(list_type) is list
        # Integer() returns int, so list(int) should have int as its type
        assert get_args(list_type)[0] == int
        
        # List without type defaults to str
        list_type = parse_type_spec('list')
        assert get_origin(list_type) is list
        assert get_args(list_type) == (str,)
        
        # List with text type
        list_type = parse_type_spec('list(text)')
        assert get_origin(list_type) is list
        # Text() returns str
        assert get_args(list_type)[0] == str
    
    def test_square_bracket_syntax(self):
        """Test square bracket syntax for types."""
        from typing import get_origin, get_args
        
        # Test model with square brackets
        from includecontents.django.prop_types import Model
        model_type = parse_type_spec('model[auth.User]')
        # Should return Model['auth.User']
        assert hasattr(model_type, '__metadata__')
        
        # Test queryset with square brackets
        from includecontents.django.prop_types import QuerySet
        qs_type = parse_type_spec('queryset[blog.Article]')
        # Should return QuerySet['blog.Article']
        assert hasattr(qs_type, '__metadata__')
        
        # Test list with square brackets
        list_type = parse_type_spec('list[int]')
        assert get_origin(list_type) is list
        # Integer() returns int, so list[int] should have int as its type
        assert get_args(list_type)[0] == int
        
        # Test nested square brackets
        list_type = parse_type_spec('list[text]')
        assert get_origin(list_type) is list
        # Text() returns str, so list[text] should have str as its type
        assert get_args(list_type)[0] == str
    
    def test_optional_props_from_template_syntax(self):
        """Test parsing optional props with ? marker."""
        from includecontents.shared.typed_props import parse_template_props
        
        # Test optional prop with ? marker
        props = parse_template_props('name:text email?:email age?:int')
        assert 'name' in props
        assert props['name']['required'] is True
        assert 'email' in props
        assert props['email']['required'] is False
        assert 'age' in props
        assert props['age']['required'] is False
        
        # Test optional with square bracket syntax
        props = parse_template_props('role?:choice[admin,user,guest]')
        assert 'role' in props
        assert props['role']['required'] is False
        
        # Test optional with default value (should also be optional)
        props = parse_template_props('status:choice[active,inactive]=active')
        assert 'status' in props
        # Default value makes it optional
        assert 'status' in props  # This will have a default, making it not required
        
        # Test mixed required and optional
        props = parse_template_props('id:int name:text description?:text tags?:list[str]')
        assert props['id']['required'] is True
        assert props['name']['required'] is True
        assert props['description']['required'] is False
        assert props['tags']['required'] is False
    
    def test_unknown_type(self):
        """Test unknown type defaults to string."""
        unknown_type = parse_type_spec('unknown')
        assert unknown_type is str


class TestComponentDecorator:
    """Test the @component decorator."""
    
    def test_component_registration(self):
        """Test that components are registered correctly."""
        from includecontents.shared.typed_props import get_props_class, _registry
        
        # Clear registry for test
        _registry.clear()
        
        @component('components/test-component.html')
        @dataclass
        class TestProps:
            title: str
        
        # Check registration
        assert get_props_class('components/test-component.html') is TestProps
        assert TestProps._is_component_props is True
        assert TestProps._template_path == 'components/test-component.html'
    
    def test_auto_dataclass_conversion(self):
        """Test that non-dataclasses are converted."""
        from includecontents.shared.typed_props import _registry
        from dataclasses import is_dataclass
        
        _registry.clear()
        
        @component('components/auto-convert.html')
        class AutoProps:
            name: str = 'default'
        
        # Should be converted to dataclass
        assert is_dataclass(AutoProps)
        assert hasattr(AutoProps, '__dataclass_fields__')


# Integration tests would go here, testing actual template rendering
# These would require setting up test templates and components