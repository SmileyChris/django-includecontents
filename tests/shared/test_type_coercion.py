"""
Tests for type coercion logic.

Tests the conversion of string inputs to appropriate Python types
across both Django and Jinja2 template engines.
"""

import pytest
from dataclasses import dataclass
from django.template import TemplateSyntaxError

from includecontents.shared.validation import validate_props
from includecontents.shared.typed_props import coerce_value


class TestBasicTypeCoercion:
    """Test basic type coercion for common types."""

    def test_string_coercion(self):
        """Test string values pass through unchanged."""
        assert coerce_value("hello", str) == "hello"
        assert coerce_value("", str) == ""
        assert coerce_value("123", str) == "123"

    def test_integer_coercion(self):
        """Test string to integer conversion."""
        assert coerce_value("25", int) == 25
        assert coerce_value("0", int) == 0
        assert coerce_value("-10", int) == -10

        # Invalid integer strings should return original value (for validation to handle)
        assert coerce_value("not-a-number", int) == "not-a-number"
        assert coerce_value("25.5", int) == "25.5"

    def test_float_coercion(self):
        """Test string to float conversion."""
        assert coerce_value("25.5", float) == 25.5
        assert coerce_value("0.0", float) == 0.0
        assert coerce_value("-10.25", float) == -10.25
        assert coerce_value("25", float) == 25.0  # Integer string to float

        # Invalid float strings should return original value (for validation to handle)
        assert coerce_value("not-a-number", float) == "not-a-number"

    def test_boolean_coercion(self):
        """Test string to boolean conversion."""
        # True values
        for true_val in ["true", "True", "TRUE", "1", "yes", "on"]:
            assert coerce_value(true_val, bool) is True

        # False values
        for false_val in ["false", "False", "FALSE", "0", "no", "off"]:
            assert coerce_value(false_val, bool) is False

        # Invalid boolean strings should return False (strict handling)
        assert coerce_value("maybe", bool) is False
        assert coerce_value("", bool) is False


class TestListCoercion:
    """Test list and comma-separated value coercion."""

    def test_comma_separated_string_to_list(self):
        """Test conversion of comma-separated strings to lists."""
        assert coerce_value("red,blue,green", list[str]) == ["red", "blue", "green"]
        assert coerce_value("apple", list[str]) == ["apple"]
        assert coerce_value("", list[str]) == []

    def test_list_with_whitespace(self):
        """Test list coercion handles whitespace correctly."""
        assert coerce_value("red, blue, green", list[str]) == ["red", "blue", "green"]
        assert coerce_value(" apple ", list[str]) == ["apple"]
        assert coerce_value("one,  two  , three", list[str]) == ["one", "two", "three"]


class TestChoiceCoercion:
    """Test choice and multichoice coercion."""

    def test_choice_validation(self):
        """Test choice validation against allowed values."""
        @dataclass
        class ChoiceProps:
            variant: str  # Will be validated as choice in actual usage

        # This would be handled by the choice validator in practice
        # Testing the coercion part here
        assert coerce_value("primary", str) == "primary"

    def test_multichoice_coercion(self):
        """Test multichoice value coercion to list."""
        # Multiple values
        assert coerce_value("primary,secondary", list[str]) == ["primary", "secondary"]

        # Single value
        assert coerce_value("primary", list[str]) == ["primary"]

        # Empty value
        assert coerce_value("", list[str]) == []


class TestIntegratedCoercion:
    """Test coercion in the context of full prop validation."""

    def test_coercion_in_dataclass_validation(self):
        """Test type coercion works with dataclass validation."""
        @dataclass
        class CoercionProps:
            name: str
            age: int
            active: bool
            tags: list[str]

        # All string inputs that need coercion
        result = validate_props(CoercionProps, {
            'name': 'John',
            'age': '30',  # String to int
            'active': 'true',  # String to bool
            'tags': 'red,blue,green'  # String to list
        })

        assert result['name'] == 'John'
        assert result['age'] == 30
        assert result['active'] is True
        assert result['tags'] == ['red', 'blue', 'green']

    def test_coercion_with_defaults(self):
        """Test coercion works with default values."""
        @dataclass
        class DefaultProps:
            count: int = 5
            enabled: bool = True

        # No coercion needed for defaults
        result = validate_props(DefaultProps, {})
        assert result['count'] == 5
        assert result['enabled'] is True

        # Coercion needed for provided values
        result = validate_props(DefaultProps, {
            'count': '10',
            'enabled': 'false'
        })
        assert result['count'] == 10
        assert result['enabled'] is False


class TestCoercionErrors:
    """Test error handling during type coercion."""

    def test_invalid_integer_coercion_error(self):
        """Test error messages for failed integer coercion."""
        @dataclass
        class IntProps:
            age: int

        with pytest.raises(TemplateSyntaxError) as exc_info:
            validate_props(IntProps, {'age': 'not-a-number'})

        error_str = str(exc_info.value)
        assert 'Cannot convert' in error_str
        assert 'not-a-number' in error_str
        assert 'integer' in error_str.lower()

    def test_invalid_boolean_coercion_behavior(self):
        """Test behavior for ambiguous boolean values."""
        @dataclass
        class BoolProps:
            active: bool

        # Invalid boolean strings return False (strict behavior)
        result = validate_props(BoolProps, {'active': 'maybe'})
        assert result['active'] is False

    def test_coercion_error_includes_field_context(self):
        """Test that coercion errors include field name context."""
        @dataclass
        class ContextProps:
            user_age: int

        with pytest.raises(TemplateSyntaxError) as exc_info:
            validate_props(ContextProps, {'user_age': 'invalid'})

        error_str = str(exc_info.value)
        assert 'user_age' in error_str
        # Check that field name is included in error context
        assert 'field' in error_str.lower() or 'user_age' in error_str


class TestEdgeCases:
    """Test edge cases in type coercion."""

    def test_none_values(self):
        """Test handling of None values."""
        # None should pass through for optional fields
        assert coerce_value(None, str) is None

    def test_already_correct_type(self):
        """Test that values of the correct type pass through unchanged."""
        assert coerce_value(25, int) == 25
        assert coerce_value(True, bool) is True
        assert coerce_value(['a', 'b'], list) == ['a', 'b']

    def test_empty_string_coercion(self):
        """Test coercion of empty strings."""
        assert coerce_value("", str) == ""
        assert coerce_value("", list[str]) == []

        # Empty string to int should return original (for validation to handle)
        assert coerce_value("", int) == ""
        # Empty string to bool should return False
        assert coerce_value("", bool) is False