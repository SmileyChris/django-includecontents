"""
Tests for the prop_types validation system.
"""

import pytest
from dataclasses import dataclass
from typing import Optional, Literal
from django.template import TemplateSyntaxError
from django.template.loader import render_to_string
from django.core.exceptions import ValidationError

from includecontents.prop_types import (
    Text, Integer, Email, Url, Choice, CssClass, MinMax
)
from includecontents.props import component, validate_props, parse_type_spec


class TestPropTypes:
    """Test the prop_types module."""
    
    def test_text_type(self):
        """Test Text prop type with validation."""
        # Basic text
        text_type = Text()
        assert text_type is str
        
        # Text with max length
        text_type = Text(max_length=10)
        assert hasattr(text_type, '__metadata__')
        assert len(text_type.__metadata__) == 1
        
        # Text with multiple validators
        text_type = Text(max_length=10, min_length=2, pattern=r'^[A-Z]')
        assert len(text_type.__metadata__) == 3
    
    def test_integer_type(self):
        """Test Integer prop type with bounds."""
        # Basic integer
        int_type = Integer()
        assert int_type is int
        
        # Integer with min
        int_type = Integer(min=18)
        assert hasattr(int_type, '__metadata__')
        assert len(int_type.__metadata__) == 1
        
        # Integer with min and max
        int_type = Integer(min=18, max=120)
        assert len(int_type.__metadata__) == 2
    
    def test_choice_type(self):
        """Test Choice prop type."""
        # Single choice
        choice_type = Choice['admin']
        assert choice_type == Literal['admin']
        
        # Multiple choices
        choice_type = Choice['admin', 'user', 'guest']
        assert choice_type == Literal['admin', 'user', 'guest']
    
    def test_predefined_types(self):
        """Test predefined prop types."""
        assert hasattr(Email, '__metadata__')
        assert hasattr(Url, '__metadata__')
        assert hasattr(CssClass(), '__metadata__')
        
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


class TestParseTypeSpec:
    """Test parsing type specifications from template syntax."""
    
    def test_simple_types(self):
        """Test parsing simple type names."""
        assert parse_type_spec('text') == Text
        assert parse_type_spec('int') == Integer
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
        choice_type = parse_type_spec('choice(admin,user,guest)')
        # Can't directly compare Literal types, but we can check it's the right origin
        from typing import get_origin, get_args
        assert get_origin(choice_type) is Literal
        assert get_args(choice_type) == ('admin', 'user', 'guest')
    
    def test_unknown_type(self):
        """Test unknown type defaults to string."""
        unknown_type = parse_type_spec('unknown')
        assert unknown_type is str


class TestComponentDecorator:
    """Test the @component decorator."""
    
    def test_component_registration(self):
        """Test that components are registered correctly."""
        from includecontents.props import get_props_class, _registry
        
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
        from includecontents.props import _registry
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