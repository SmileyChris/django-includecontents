"""
Tests for Python dataclass props integration.

Tests the @component decorator and dataclass-based props system
that works across both Django and Jinja2 template engines.
"""

import pytest
from dataclasses import dataclass
from django.template import TemplateSyntaxError

from includecontents.shared.typed_props import (
    component,
    get_props_class,
    clear_registry,
)
from includecontents.shared.validation import validate_props


class TestComponentDecorator:
    """Test the @component decorator for registering props classes."""

    def setup_method(self):
        """Clear registry before each test."""
        clear_registry()

    def test_basic_component_registration(self):
        """Test basic component registration with decorator."""

        @component("components/test-card.html")
        @dataclass
        class TestCardProps:
            title: str
            subtitle: str = "Default"

        # Should be registered
        props_class = get_props_class("components/test-card.html")
        assert props_class is TestCardProps

    def test_component_with_no_props(self):
        """Test component registration with empty props class."""

        @component("components/empty.html")
        @dataclass
        class EmptyProps:
            pass

        props_class = get_props_class("components/empty.html")
        assert props_class is EmptyProps

        # Should validate with empty data
        result = validate_props(EmptyProps, {})
        assert result == {}

    def test_duplicate_component_registration(self):
        """Test handling of duplicate component registrations."""

        @component("components/duplicate.html")
        @dataclass
        class FirstProps:
            title: str

        @component("components/duplicate.html")
        @dataclass
        class SecondProps:
            name: str

        # Should keep the first registration
        props_class = get_props_class("components/duplicate.html")
        assert props_class is FirstProps

    def test_registry_isolation(self):
        """Test that different components are isolated."""

        @component("components/card.html")
        @dataclass
        class CardProps:
            title: str

        @component("components/button.html")
        @dataclass
        class ButtonProps:
            text: str

        assert get_props_class("components/card.html") is CardProps
        assert get_props_class("components/button.html") is ButtonProps
        assert get_props_class("components/nonexistent.html") is None


class TestDataclassValidation:
    """Test validation with dataclass-based props."""

    def setup_method(self):
        """Clear registry before each test."""
        clear_registry()

    def test_required_and_optional_fields(self):
        """Test validation with required and optional fields."""

        @dataclass
        class MixedProps:
            title: str  # Required
            count: int = 0  # Optional with default
            description: str | None = None

        # All fields provided
        result = validate_props(
            MixedProps, {"title": "Test", "count": 5, "description": "A test"}
        )
        assert result["title"] == "Test"
        assert result["count"] == 5
        assert result["description"] == "A test"

        # Only required field
        result = validate_props(MixedProps, {"title": "Test"})
        assert result["title"] == "Test"
        assert result["count"] == 0
        assert result["description"] is None

        # Missing required field
        with pytest.raises(TemplateSyntaxError):
            validate_props(MixedProps, {"count": 5})

    def test_complex_types(self):
        """Test validation with complex types."""

        @dataclass
        class ComplexProps:
            tags: list[str]
            metadata: dict
            active: bool

        result = validate_props(
            ComplexProps,
            {
                "tags": ["python", "django"],
                "metadata": {"key": "value"},
                "active": True,
            },
        )
        assert result["tags"] == ["python", "django"]
        assert result["metadata"] == {"key": "value"}
        assert result["active"] is True

    def test_type_hints_with_defaults(self):
        """Test type hints work correctly with default values."""

        @dataclass
        class DefaultTypesProps:
            name: str = "Guest"
            age: int = 18
            active: bool = True
            tags: list[str] = None

        # Use all defaults
        result = validate_props(DefaultTypesProps, {})
        assert result["name"] == "Guest"
        assert result["age"] == 18
        assert result["active"] is True
        assert result["tags"] is None

        # Override some defaults
        result = validate_props(DefaultTypesProps, {"name": "Alice", "tags": ["admin"]})
        assert result["name"] == "Alice"
        assert result["age"] == 18  # default
        assert result["active"] is True  # default
        assert result["tags"] == ["admin"]


class TestCustomValidation:
    """Test custom validation methods in dataclasses."""

    def setup_method(self):
        """Clear registry before each test."""
        clear_registry()

    def test_clean_method_validation(self):
        """Test custom validation via clean() method."""

        @dataclass
        class ValidatedProps:
            start: int
            end: int

            def clean(self):
                from django.core.exceptions import ValidationError

                if self.start >= self.end:
                    raise ValidationError("Start must be less than end")

        # Valid values
        result = validate_props(ValidatedProps, {"start": 1, "end": 10})
        assert result["start"] == 1
        assert result["end"] == 10

        # Invalid values
        with pytest.raises(TemplateSyntaxError) as exc_info:
            validate_props(ValidatedProps, {"start": 10, "end": 1})
        assert "Start must be less than end" in str(exc_info.value)

    def test_multiple_validation_errors(self):
        """Test handling of multiple validation errors."""

        @dataclass
        class MultiValidateProps:
            username: str
            password: str

            def clean(self):
                from django.core.exceptions import ValidationError

                errors = []
                if len(self.username) < 3:
                    errors.append("Username too short")
                if len(self.password) < 8:
                    errors.append("Password too short")
                if errors:
                    raise ValidationError(errors)

        # Valid values
        result = validate_props(
            MultiValidateProps, {"username": "alice", "password": "secretpassword"}
        )
        assert result["username"] == "alice"

        # Multiple validation errors
        with pytest.raises(TemplateSyntaxError) as exc_info:
            validate_props(MultiValidateProps, {"username": "al", "password": "short"})
        error_str = str(exc_info.value)
        assert "Username too short" in error_str
        assert "Password too short" in error_str


class TestInheritance:
    """Test dataclass inheritance and composition."""

    def setup_method(self):
        """Clear registry before each test."""
        clear_registry()

    def test_dataclass_inheritance(self):
        """Test validation with dataclass inheritance."""

        @dataclass
        class BaseProps:
            title: str
            description: str = ""

        @dataclass
        class ExtendedProps(BaseProps):
            category: str = "general"  # Give it a default to fix field ordering
            priority: int = 1

        result = validate_props(
            ExtendedProps, {"title": "Test", "category": "Important"}
        )
        assert result["title"] == "Test"
        assert result["description"] == ""  # inherited default
        assert result["category"] == "Important"
        assert result["priority"] == 1  # extended default

    def test_nested_dataclass_composition(self):
        """Test validation with nested dataclass composition."""

        @dataclass
        class Author:
            name: str
            email: str

        @dataclass
        class ArticleProps:
            title: str
            author: Author
            published: bool = False

        # This would require more complex validation logic
        # For now, test that we can define the structure
        assert hasattr(ArticleProps, "__dataclass_fields__")
        assert "author" in ArticleProps.__dataclass_fields__


class TestRegistryManagement:
    """Test registry management and introspection."""

    def setup_method(self):
        """Clear registry before each test."""
        clear_registry()

    def test_registry_lookup_patterns(self):
        """Test different patterns for registry lookup."""

        @component("components/user-card.html")
        @dataclass
        class UserCardProps:
            name: str

        # Exact match
        assert get_props_class("components/user-card.html") is UserCardProps

        # Non-existent component
        assert get_props_class("components/nonexistent.html") is None

    def test_clear_registry(self):
        """Test registry clearing functionality."""

        @component("components/temp.html")
        @dataclass
        class TempProps:
            value: str

        assert get_props_class("components/temp.html") is TempProps

        clear_registry()
        assert get_props_class("components/temp.html") is None


class TestErrorHandling:
    """Test error handling in dataclass props."""

    def setup_method(self):
        """Clear registry before each test."""
        clear_registry()

    def test_invalid_dataclass_structure(self):
        """Test error handling for invalid dataclass structures."""

        # Non-dataclass should not be registerable
        @component("components/invalid.html")
        class InvalidProps:  # Not a dataclass
            title: str

        # This should work but validation might behave differently
        # The @component decorator should handle this gracefully

    def test_validation_with_invalid_field_types(self):
        """Test validation behavior with complex/invalid field types."""

        @dataclass
        class ComplexProps:
            # These would require special handling
            callback: callable = None
            metadata: dict = None

        # Should handle gracefully
        result = validate_props(ComplexProps, {})
        assert result["callback"] is None
        assert result["metadata"] is None
