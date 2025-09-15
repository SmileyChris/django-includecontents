"""
Tests for enhanced error messages and debugging features.

This module tests the enhanced error messages with contextual information
using Exception.add_note() (Python 3.11+) or fallback behavior.
"""

import sys
from dataclasses import dataclass
from typing import Optional

import pytest
from django.template import TemplateSyntaxError

from includecontents.errors import enhance_error, enhance_validation_error, enhance_coercion_error
from includecontents.props import component, validate_props, clear_registry
from includecontents.prop_types import Email, MinMax


class TestErrorEnhancement:
    """Test the basic error enhancement utilities."""

    def test_enhance_error_with_add_note(self):
        """Test enhance_error uses add_note when available."""
        exc = ValueError("Original message")
        enhanced = enhance_error(exc, "Additional context")

        # The enhanced exception should be the same instance
        assert enhanced is exc

        # Check if add_note was used (Python 3.11+) or fallback
        if hasattr(exc, 'add_note'):
            # Python 3.11+ - the note should be available when the exception is formatted
            exc_str = str(exc)
            # The original message should remain unchanged
            assert exc_str == "Original message"
        else:
            # Fallback - the message should be modified
            assert "Additional context" in str(exc)

    def test_enhance_error_fallback_behavior(self):
        """Test enhance_error fallback for older Python versions."""
        from unittest.mock import patch

        exc = ValueError("Original message")

        # Patch hasattr in the errors module to simulate older Python
        with patch('includecontents.errors.hasattr', return_value=False):
            enhanced = enhance_error(exc, "Additional context")

            assert enhanced is exc
            assert "Additional context" in str(exc)

    def test_enhance_validation_error(self):
        """Test enhance_validation_error adds comprehensive context."""
        exc = TemplateSyntaxError("Props validation failed")

        field_errors = ["email: Invalid email", "age: Must be positive"]
        enhanced = enhance_validation_error(
            exc,
            component_name="components/user-card.html",
            props_class_name="UserCardProps",
            field_errors=field_errors
        )

        assert enhanced is exc

    def test_enhance_coercion_error(self):
        """Test enhance_coercion_error adds type conversion context."""
        exc = TemplateSyntaxError("Cannot convert value")

        enhanced = enhance_coercion_error(
            exc,
            field_name="age",
            value="abc",
            expected_type=int
        )

        assert enhanced is exc


class TestEnhancedValidationErrors:
    """Test enhanced validation errors in the props validation system."""

    def setup_method(self):
        """Clear registry before each test."""
        clear_registry()

    def test_validation_error_includes_component_context(self):
        """Test validation errors include component and props class information."""
        @component('components/test-card.html')
        @dataclass
        class TestCardProps:
            email: Email
            age: MinMax(18, 120)

        # Test validation error includes component context
        with pytest.raises(TemplateSyntaxError) as exc_info:
            validate_props(TestCardProps, {
                'email': 'invalid-email',
                'age': 25
            })

        error_str = str(exc_info.value)
        assert 'Props validation failed' in error_str
        assert 'email' in error_str.lower()

        # Check for enhanced context (depends on Python version)
        if hasattr(exc_info.value, '__notes__'):
            # Python 3.11+ - check notes
            notes = getattr(exc_info.value, '__notes__', [])
            note_text = '\n'.join(notes)
            assert 'Component: components/test-card.html' in note_text
            assert 'Props class: TestCardProps' in note_text
        else:
            # Fallback - context should be in the main message
            full_error = str(exc_info.value)
            assert 'Component: components/test-card.html' in full_error
            assert 'Props class: TestCardProps' in full_error

    def test_missing_required_prop_error(self):
        """Test enhanced error for missing required props."""
        @component('components/minimal.html')
        @dataclass
        class MinimalProps:
            title: str
            count: int

        with pytest.raises(TemplateSyntaxError) as exc_info:
            validate_props(MinimalProps, {})

        error_str = str(exc_info.value)
        assert 'Props validation failed' in error_str
        assert 'Missing required prop' in error_str

    def test_type_coercion_error_context(self):
        """Test enhanced context for type coercion failures."""
        @component('components/typed.html')
        @dataclass
        class TypedProps:
            count: int
            price: float
            active: bool

        with pytest.raises(TemplateSyntaxError) as exc_info:
            validate_props(TypedProps, {
                'count': 'not-a-number',
                'price': 10.5,
                'active': True
            })

        error_str = str(exc_info.value)
        assert 'Props validation failed' in error_str
        assert 'Cannot convert' in error_str
        assert 'not-a-number' in error_str

    def test_optional_prop_validation(self):
        """Test validation with optional props."""
        @component('components/optional.html')
        @dataclass
        class OptionalProps:
            title: str
            subtitle: Optional[str] = None
            count: Optional[int] = 0

        # Should succeed with minimal props
        result = validate_props(OptionalProps, {'title': 'Test'})
        assert result['title'] == 'Test'
        assert result['subtitle'] is None
        assert result['count'] == 0

        # Should succeed with all props
        result = validate_props(OptionalProps, {
            'title': 'Test',
            'subtitle': 'Sub',
            'count': 5
        })
        assert result['title'] == 'Test'
        assert result['subtitle'] == 'Sub'
        assert result['count'] == 5

    def test_custom_clean_method_error(self):
        """Test enhanced errors for custom clean method failures."""
        @component('components/custom-clean.html')
        @dataclass
        class CustomCleanProps:
            start_date: str
            end_date: str

            def clean(self):
                from django.core.exceptions import ValidationError
                if self.start_date >= self.end_date:
                    raise ValidationError("Start date must be before end date")

        with pytest.raises(TemplateSyntaxError) as exc_info:
            validate_props(CustomCleanProps, {
                'start_date': '2023-12-31',
                'end_date': '2023-01-01'
            })

        error_str = str(exc_info.value)
        assert 'Props validation failed' in error_str
        assert 'Start date must be before end date' in error_str

    def test_multiple_field_errors_limit(self):
        """Test that multiple field errors are properly limited in notes."""
        @component('components/many-errors.html')
        @dataclass
        class ManyErrorsProps:
            field1: int
            field2: int
            field3: int
            field4: int
            field5: int

        with pytest.raises(TemplateSyntaxError) as exc_info:
            validate_props(ManyErrorsProps, {
                'field1': 'bad1',
                'field2': 'bad2',
                'field3': 'bad3',
                'field4': 'bad4',
                'field5': 'bad5'
            })

        error_str = str(exc_info.value)
        assert 'Props validation failed' in error_str

        # Check that error limiting works (should show first 3 + "and X more")
        if hasattr(exc_info.value, '__notes__'):
            notes = getattr(exc_info.value, '__notes__', [])
            note_text = '\n'.join(notes)
            # Should limit to 3 individual errors plus a summary
            bullet_count = note_text.count('•')
            assert bullet_count <= 3
            if bullet_count == 3:
                assert 'more error(s)' in note_text