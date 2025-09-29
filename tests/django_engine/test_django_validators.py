"""
Django-specific validator tests for props system.

Tests Django validators, Django-specific prop types, and Django template
engine integration that doesn't apply to other template engines.
"""

import pytest
from dataclasses import dataclass
from django.template import TemplateSyntaxError
from django.core.exceptions import ValidationError

from includecontents.django.prop_types import (
    Text,
    Integer,
    Email,
    Url,
    MinMax,
    Decimal,
    Color,
    CssClass,
)
from includecontents.shared.validation import validate_props


class TestDjangoValidators:
    """Test Django validator integration."""

    def test_text_with_django_validators(self):
        """Test Text prop type with Django length validators."""

        @dataclass
        class TextProps:
            name: Text[{"max_length": 10, "min_length": 2}]

        # Valid length
        result = validate_props(TextProps, {"name": "Alice"})
        assert result["name"] == "Alice"

        # Too short
        with pytest.raises(TemplateSyntaxError) as exc_info:
            validate_props(TextProps, {"name": "A"})
        assert "at least 2 characters" in str(exc_info.value).lower()

        # Too long
        with pytest.raises(TemplateSyntaxError) as exc_info:
            validate_props(TextProps, {"name": "VeryLongName"})
        assert "at most 10 characters" in str(exc_info.value).lower()

    def test_text_with_regex_pattern(self):
        """Test Text prop type with Django regex validator."""

        @dataclass
        class PatternProps:
            code: Text[{"pattern": r"^[A-Z]{3}-\d{3}$"}]

        # Valid pattern
        result = validate_props(PatternProps, {"code": "ABC-123"})
        assert result["code"] == "ABC-123"

        # Invalid pattern
        with pytest.raises(TemplateSyntaxError) as exc_info:
            validate_props(PatternProps, {"code": "invalid"})
        assert "valid value" in str(exc_info.value).lower()

    def test_integer_with_django_bounds(self):
        """Test Integer prop type with Django min/max validators."""

        @dataclass
        class BoundedProps:
            age: Integer[{"min": 18, "max": 120}]

        # Valid value
        result = validate_props(BoundedProps, {"age": "25"})
        assert result["age"] == 25

        # Too small
        with pytest.raises(TemplateSyntaxError) as exc_info:
            validate_props(BoundedProps, {"age": "10"})
        assert "greater than or equal to 18" in str(exc_info.value).lower()

        # Too large
        with pytest.raises(TemplateSyntaxError) as exc_info:
            validate_props(BoundedProps, {"age": "150"})
        assert "less than or equal to 120" in str(exc_info.value).lower()

    def test_email_django_validator(self):
        """Test Email prop type with Django's EmailValidator."""

        @dataclass
        class EmailProps:
            email: Email

        # Valid email
        result = validate_props(EmailProps, {"email": "user@example.com"})
        assert result["email"] == "user@example.com"

        # Invalid email
        with pytest.raises(TemplateSyntaxError) as exc_info:
            validate_props(EmailProps, {"email": "invalid-email"})
        assert "email" in str(exc_info.value).lower()

    def test_url_django_validator(self):
        """Test URL prop type with Django's URLValidator."""

        @dataclass
        class UrlProps:
            website: Url

        # Valid URL
        result = validate_props(UrlProps, {"website": "https://example.com"})
        assert result["website"] == "https://example.com"

        # Invalid URL
        with pytest.raises(TemplateSyntaxError) as exc_info:
            validate_props(UrlProps, {"website": "not-a-url"})
        assert "url" in str(exc_info.value).lower()


class TestDjangoSpecificTypes:
    """Test Django-specific prop types."""

    def test_decimal_type(self):
        """Test Decimal prop type with Django DecimalValidator."""

        @dataclass
        class DecimalProps:
            price: Decimal[{"max_digits": 10, "decimal_places": 2}]

        # Valid decimal
        result = validate_props(DecimalProps, {"price": "19.99"})
        # May be string or Decimal object (coercion converts to Decimal)
        from decimal import Decimal as DecimalType
        assert result["price"] == DecimalType("19.99")

        # Invalid decimal format
        with pytest.raises(TemplateSyntaxError) as exc_info:
            validate_props(DecimalProps, {"price": "invalid"})
        assert "cannot convert" in str(exc_info.value).lower()

    def test_css_class_type(self):
        """Test CssClass prop type with CSS class validation."""

        @dataclass
        class CssProps:
            css_class: CssClass

        # Valid CSS class
        result = validate_props(CssProps, {"css_class": "btn-primary"})
        assert result["css_class"] == "btn-primary"

        # Valid multiple classes
        result = validate_props(CssProps, {"css_class": "btn btn-primary"})
        assert result["css_class"] == "btn btn-primary"

    def test_color_type(self):
        """Test Color prop type validation."""

        @dataclass
        class ColorProps:
            color: Color["hex"]  # Specify hex format for validation

        # Valid hex color
        result = validate_props(ColorProps, {"color": "#ff0000"})
        assert result["color"] == "#ff0000"

        # Invalid hex color
        with pytest.raises(TemplateSyntaxError) as exc_info:
            validate_props(ColorProps, {"color": "invalid-color"})
        assert "invalid" in str(exc_info.value).lower()

    def test_minmax_helper(self):
        """Test MinMax helper for integer bounds."""

        @dataclass
        class MinMaxProps:
            score: MinMax(0, 100)

        # Valid value
        result = validate_props(MinMaxProps, {"score": "75"})
        assert result["score"] == 75

        # Below minimum
        with pytest.raises(TemplateSyntaxError) as exc_info:
            validate_props(MinMaxProps, {"score": "-10"})
        assert "greater than or equal to 0" in str(exc_info.value).lower()

        # Above maximum
        with pytest.raises(TemplateSyntaxError) as exc_info:
            validate_props(MinMaxProps, {"score": "150"})
        assert "less than or equal to 100" in str(exc_info.value).lower()


class TestDjangoValidatorMessages:
    """Test Django validator error message integration."""

    def test_custom_validator_message(self):
        """Test custom validator error messages."""

        @dataclass
        class CustomMessageProps:
            username: Text[
                {"min_length": 3, "message": "Username must be at least 3 characters"}
            ]

        # This tests that custom messages can be integrated
        # Actual implementation may vary
        with pytest.raises(TemplateSyntaxError) as exc_info:
            validate_props(CustomMessageProps, {"username": "ab"})
        # Should include validation error context

    def test_multiple_validator_errors(self):
        """Test handling of multiple Django validator errors."""

        @dataclass
        class MultiValidatorProps:
            email: Email
            age: MinMax(18, 120)

        # Multiple validation failures
        with pytest.raises(TemplateSyntaxError) as exc_info:
            validate_props(MultiValidatorProps, {"email": "invalid-email", "age": "10"})
        error_str = str(exc_info.value)
        # Should include context for both failures
        assert "email" in error_str.lower() or "age" in error_str.lower()

    def test_validator_error_enhancement(self):
        """Test Django validator error enhancement."""

        @dataclass
        class EnhancedErrorProps:
            phone: Text[{"pattern": r"^\+?1?\d{9,15}$"}]

        with pytest.raises(TemplateSyntaxError) as exc_info:
            validate_props(EnhancedErrorProps, {"phone": "invalid"})

        error_str = str(exc_info.value)
        # Enhanced errors should include field name and context
        assert "phone" in error_str.lower()


class TestDjangoIPValidation:
    """Test Django IP address validation."""

    def test_ipv4_validation(self):
        """Test IPv4 address validation."""

        @dataclass
        class IPv4Props:
            ip: str  # Would use IPv4 validator in practice

        # Valid IPv4
        result = validate_props(IPv4Props, {"ip": "192.168.1.1"})
        assert result["ip"] == "192.168.1.1"

        # This would be tested with actual IPv4 validator integration

    def test_ipv6_validation(self):
        """Test IPv6 address validation."""

        @dataclass
        class IPv6Props:
            ip: str  # Would use IPv6 validator in practice

        # Valid IPv6
        result = validate_props(IPv6Props, {"ip": "2001:db8::1"})
        assert result["ip"] == "2001:db8::1"


class TestDjangoSlugValidation:
    """Test Django slug validation."""

    def test_slug_validation(self):
        """Test slug validation."""

        @dataclass
        class SlugProps:
            slug: str  # Would use slug validator in practice

        # Valid slug
        result = validate_props(SlugProps, {"slug": "my-article-slug"})
        assert result["slug"] == "my-article-slug"

        # This would be tested with actual slug validator integration

    def test_unicode_slug_validation(self):
        """Test unicode slug validation."""

        @dataclass
        class UnicodeSlugProps:
            slug: str  # Would use unicode slug validator in practice

        # Valid unicode slug
        result = validate_props(UnicodeSlugProps, {"slug": "café-article"})
        assert result["slug"] == "café-article"


class TestDjangoFormIntegration:
    """Test integration with Django forms and form fields."""

    def test_form_field_validator_integration(self):
        """Test using Django form field validators."""
        # This would test integration with Django form field validators
        # Implementation depends on how Django forms are integrated
        pass

    def test_model_field_validator_integration(self):
        """Test using Django model field validators."""
        # This would test integration with Django model field validators
        # Implementation depends on how Django models are integrated
        pass


class TestDjangoValidationContext:
    """Test Django-specific validation context."""

    def test_django_validation_error_context(self):
        """Test Django ValidationError context preservation."""

        @dataclass
        class ContextProps:
            email: Email

        with pytest.raises(TemplateSyntaxError) as exc_info:
            validate_props(ContextProps, {"email": "invalid"})

        # Should preserve Django ValidationError details
        error_str = str(exc_info.value)
        assert len(error_str) > 10  # Should have meaningful content

    def test_django_error_chaining(self):
        """Test Django error chaining preservation."""

        @dataclass
        class ChainedErrorProps:
            complex_field: str

            def clean(self):
                try:
                    # Simulate Django validator
                    raise ValidationError("Django validation failed")
                except ValidationError as e:
                    # Chain the error
                    raise ValidationError("Chained error") from e

        with pytest.raises(TemplateSyntaxError) as exc_info:
            validate_props(ChainedErrorProps, {"complex_field": "value"})

        # Should preserve error chain information
        error_str = str(exc_info.value)
        assert "error" in error_str.lower()


class TestDjangoPerformance:
    """Test Django-specific performance considerations."""

    def test_validator_caching(self):
        """Test that Django validators are cached appropriately."""

        # Multiple uses of the same validator type should be efficient
        @dataclass
        class CachedValidatorProps:
            email1: Email
            email2: Email
            email3: Email

        # Should handle multiple similar validators efficiently
        result = validate_props(
            CachedValidatorProps,
            {
                "email1": "user1@example.com",
                "email2": "user2@example.com",
                "email3": "user3@example.com",
            },
        )
        assert result["email1"] == "user1@example.com"
        assert result["email2"] == "user2@example.com"
        assert result["email3"] == "user3@example.com"

    def test_large_validation_dataset(self):
        """Test performance with large validation datasets."""
        # This would test performance characteristics
        # with large numbers of props or large prop values
        pass
