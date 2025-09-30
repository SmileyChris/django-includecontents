"""
Tests for the prop_types validation system.
"""

from dataclasses import dataclass
from typing import Literal, Optional

import pytest
from django.core.exceptions import ValidationError
from django.template import TemplateSyntaxError

from includecontents.prop_types import (
    CssClass,
    Email,
    HexColor,
    RgbColor,
    Url,
)
from includecontents.shared.template_parser import parse_type_spec
from includecontents.shared.typed_props import component
from includecontents.shared.validation import validate_props


def assert_has_metadata(type_obj, expected_length=None):
    """Helper to assert a type has metadata and optionally check its length."""
    assert hasattr(type_obj, "__metadata__")
    if expected_length is not None:
        assert len(type_obj.__metadata__) == expected_length


class TestPropTypes:
    """Test the prop_types module."""

    def test_text_type(self):
        """Test text type with validation via Annotated."""
        from typing import Annotated
        from django.core.validators import (
            MaxLengthValidator,
            MinLengthValidator,
            RegexValidator,
        )

        # Basic text
        text_type = str
        assert text_type is str

        # Text with max length
        text_type = Annotated[str, MaxLengthValidator(10)]
        assert_has_metadata(text_type, 1)

        # Text with multiple validators
        text_type = Annotated[
            str,
            MaxLengthValidator(10),
            MinLengthValidator(2),
            RegexValidator(r"^[A-Z]"),
        ]
        assert_has_metadata(text_type, 3)

    def test_integer_type(self):
        """Test integer type with bounds via Annotated."""
        from typing import Annotated
        from django.core.validators import MinValueValidator, MaxValueValidator

        # Basic integer
        int_type = int
        assert int_type is int

        # Integer with min
        int_type = Annotated[int, MinValueValidator(18)]
        assert_has_metadata(int_type, 1)

        # Integer with min and max
        int_type = Annotated[int, MinValueValidator(18), MaxValueValidator(120)]
        assert_has_metadata(int_type, 2)

    def test_decimal_type(self):
        """Test Decimal type with validation via Annotated."""
        from typing import Annotated
        from django.core.validators import (
            MinValueValidator,
            MaxValueValidator,
            DecimalValidator,
        )
        import decimal

        # Basic decimal
        decimal_type = decimal.Decimal
        assert decimal_type is decimal.Decimal

        # Decimal with bounds
        decimal_type = Annotated[
            decimal.Decimal, MinValueValidator(0), MaxValueValidator(999.99)
        ]
        assert_has_metadata(decimal_type, 2)

        # Decimal with precision
        decimal_type = Annotated[decimal.Decimal, DecimalValidator(10, 2)]
        assert_has_metadata(decimal_type, 1)

    def test_choice_type(self):
        """Test Literal type for choices (previously Choice)."""
        # Single choice
        choice_type = Literal["admin"]
        assert choice_type == Literal["admin"]

        # Multiple choices
        choice_type = Literal["admin", "user", "guest"]
        assert choice_type == Literal["admin", "user", "guest"]

    def test_color_type(self):
        """Test color validators - HexColor, RgbColor, RgbaColor."""
        # Pre-configured color validators
        assert_has_metadata(HexColor)
        assert_has_metadata(RgbColor)

        # Can also create custom color validators
        from typing import Annotated
        from django.core.validators import RegexValidator

        rgba_color = Annotated[
            str,
            RegexValidator(
                r"^rgba\(\s*\d{1,3}\s*,\s*\d{1,3}\s*,\s*\d{1,3}\s*,\s*[01]?\.?\d*\s*\)$"
            ),
        ]
        assert_has_metadata(rgba_color)

    def test_predefined_types(self):
        """Test predefined prop types."""
        assert_has_metadata(Email)
        assert_has_metadata(Url)

        # CssClass with default pattern - now just Annotated[str, validator]
        assert_has_metadata(CssClass)

        # For custom patterns, use Annotated directly
        from typing import Annotated
        from django.core.validators import RegexValidator

        custom_css = Annotated[
            str, RegexValidator(r"^custom-pattern$", "Invalid CSS class name")
        ]
        assert_has_metadata(custom_css)

        # MinMax equivalent using Annotated
        from typing import Annotated
        from django.core.validators import MinValueValidator, MaxValueValidator

        age_type = Annotated[int, MinValueValidator(0), MaxValueValidator(100)]
        assert_has_metadata(age_type, 2)


class TestPropsValidation:
    """Test the props validation system."""

    def test_simple_props_class(self):
        """Test a simple props class validation."""

        @dataclass
        class SimpleProps:
            name: str
            age: int = 25

        # Valid data
        result = validate_props(SimpleProps, {"name": "John", "age": 30})
        assert result["name"] == "John"
        assert result["age"] == 30

        # Using default
        result = validate_props(SimpleProps, {"name": "Jane"})
        assert result["name"] == "Jane"
        assert result["age"] == 25

        # Missing required field
        with pytest.raises(TemplateSyntaxError) as exc_info:
            validate_props(SimpleProps, {"age": 30})
        assert "Missing required prop: name" in str(exc_info.value)

    def test_typed_props_validation(self):
        """Test props with type validation."""
        from typing import Annotated
        from django.core.validators import MinValueValidator, MaxValueValidator

        AgeType = Annotated[int, MinValueValidator(18), MaxValueValidator(120)]

        @dataclass
        class TypedProps:
            email: Email
            age: AgeType
            website: Optional[Url] = None

        # Valid data
        result = validate_props(TypedProps, {"email": "test@example.com", "age": 25})
        assert result["email"] == "test@example.com"
        assert result["age"] == 25
        assert result["website"] is None

        # Invalid email
        with pytest.raises(TemplateSyntaxError) as exc_info:
            validate_props(TypedProps, {"email": "not-an-email", "age": 25})
        assert "email" in str(exc_info.value).lower()

        # Age out of bounds
        with pytest.raises(TemplateSyntaxError) as exc_info:
            validate_props(TypedProps, {"email": "test@example.com", "age": 150})
        assert "age" in str(exc_info.value).lower()

    def test_choice_validation(self):
        """Test Choice/Literal validation."""

        @dataclass
        class ChoiceProps:
            role: Literal["admin", "user", "guest"]
            size: Literal["sm", "md", "lg"] = "md"

        # Valid choice
        result = validate_props(ChoiceProps, {"role": "admin"})
        assert result["role"] == "admin"
        assert result["size"] == "md"

        # Invalid choice
        with pytest.raises(TemplateSyntaxError) as exc_info:
            validate_props(ChoiceProps, {"role": "superuser"})
        assert "Must be one of" in str(exc_info.value)
        assert "admin" in str(exc_info.value)

    def test_type_coercion(self):
        """Test automatic type coercion."""

        @dataclass
        class CoercionProps:
            age: int
            active: bool
            rating: float

        # String to int/float/bool
        result = validate_props(
            CoercionProps, {"age": "25", "active": "true", "rating": "4.5"}
        )
        assert result["age"] == 25
        assert result["active"] is True
        assert result["rating"] == 4.5

        # Boolean string variations
        for true_val in ["true", "True", "1", "yes", "on"]:
            result = validate_props(
                CoercionProps, {"age": 25, "active": true_val, "rating": 4.5}
            )
            assert result["active"] is True

        for false_val in ["false", "False", "0", "no", "off", ""]:
            result = validate_props(
                CoercionProps, {"age": 25, "active": false_val, "rating": 4.5}
            )
            assert result["active"] is False

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
        result = validate_props(
            PropsWithClean, {"password": "secret123", "confirm_password": "secret123"}
        )
        assert result["password"] == "secret123"

        # Invalid - passwords don't match
        with pytest.raises(TemplateSyntaxError) as exc_info:
            validate_props(
                PropsWithClean,
                {"password": "secret123", "confirm_password": "different"},
            )
        assert "Passwords don't match" in str(exc_info.value)

    def test_extra_attrs(self):
        """Test handling of extra attributes."""

        @dataclass
        class StrictProps:
            name: str

        # Extra attributes are collected
        result = validate_props(
            StrictProps, {"name": "John", "extra1": "value1", "extra2": "value2"}
        )
        assert result["name"] == "John"
        assert "_extra_attrs" in result
        assert result["_extra_attrs"]["extra1"] == "value1"
        assert result["_extra_attrs"]["extra2"] == "value2"

    def test_optional_props_validation(self):
        """Test that optional props allow missing or None values."""
        from typing import Optional

        @dataclass
        class OptionalProps:
            required_name: str
            optional_email: Optional[Email] = None
            optional_age: Optional[int] = None
            optional_role: Optional[Literal["admin", "user"]] = None

        # Test with only required prop
        result = validate_props(OptionalProps, {"required_name": "John"})
        assert result["required_name"] == "John"
        assert result["optional_email"] is None
        assert result["optional_age"] is None
        assert result["optional_role"] is None

        # Test with some optional props provided
        result = validate_props(
            OptionalProps,
            {"required_name": "Jane", "optional_age": 25, "optional_role": "admin"},
        )
        assert result["required_name"] == "Jane"
        assert result["optional_email"] is None
        assert result["optional_age"] == 25
        assert result["optional_role"] == "admin"

        # Test that missing required prop fails
        with pytest.raises(TemplateSyntaxError) as exc_info:
            validate_props(OptionalProps, {"optional_age": 30})
        assert "Missing required prop: required_name" in str(exc_info.value)

        # Test that None is accepted for optional props
        result = validate_props(
            OptionalProps,
            {"required_name": "Bob", "optional_email": None, "optional_age": None},
        )
        assert result["optional_email"] is None
        assert result["optional_age"] is None

    def test_list_coercion_from_string(self):
        """Test that List types handle comma-separated strings."""
        from typing import List

        @dataclass
        class ListProps:
            tags: List[str]
            numbers: List[int]
            flags: Optional[List[bool]] = None

        # Test comma-separated string -> List[str]
        result = validate_props(
            ListProps, {"tags": "python, django, web", "numbers": "1, 2, 3, 4"}
        )
        assert result["tags"] == ["python", "django", "web"]
        assert result["numbers"] == [1, 2, 3, 4]

        # Test single value -> List
        result = validate_props(ListProps, {"tags": "single-tag", "numbers": 42})
        assert result["tags"] == ["single-tag"]
        assert result["numbers"] == [42]

        # Test already a list
        result = validate_props(
            ListProps, {"tags": ["tag1", "tag2"], "numbers": [10, 20]}
        )
        assert result["tags"] == ["tag1", "tag2"]
        assert result["numbers"] == [10, 20]

        # Test boolean list from string
        result = validate_props(
            ListProps, {"tags": "test", "numbers": "1", "flags": "true, false, yes, no"}
        )
        assert result["flags"] == [True, False, True, False]

        # Test error on invalid int conversion
        with pytest.raises(TemplateSyntaxError) as exc_info:
            validate_props(ListProps, {"tags": "test", "numbers": "1, two, 3"})
        assert "Cannot convert 'two' to integer" in str(exc_info.value)


class TestParseTypeSpec:
    """Test parsing type specifications from template syntax."""

    def test_simple_types(self):
        """Test parsing simple type names."""
        # Text() returns str
        assert parse_type_spec("text") is str
        # Integer() returns int
        assert parse_type_spec("int") is int
        # Email and Url are pre-configured Annotated types
        assert parse_type_spec("email") is Email
        assert parse_type_spec("url") is Url

    def test_parameterized_types(self):
        """Test parsing types with parameters."""
        # Integer with min
        int_type = parse_type_spec("int[min=18]")
        assert_has_metadata(int_type)

        # Integer with min and max
        int_type = parse_type_spec("int[min=18,max=120]")
        assert_has_metadata(int_type, 2)

        # Text with max_length
        text_type = parse_type_spec("text[max_length=100]")
        assert_has_metadata(text_type)

    def test_choice_parsing(self):
        """Test parsing choice types."""
        from typing import get_args, get_origin

        # Test square bracket syntax
        choice_type = parse_type_spec("choice[admin,user,guest]")
        assert get_origin(choice_type) is Literal
        assert get_args(choice_type) == ("admin", "user", "guest")

    def test_list_type_parsing(self):
        """Test parsing list types from template syntax."""
        from typing import get_args, get_origin

        # List with type parameter
        list_type = parse_type_spec("list[str]")
        assert get_origin(list_type) is list
        # str type should be preserved
        assert get_args(list_type)[0] is str

        # List with int type
        list_type = parse_type_spec("list[int]")
        assert get_origin(list_type) is list
        # int type should be preserved
        assert get_args(list_type)[0] is int

        # List without type defaults to str
        list_type = parse_type_spec("list")
        assert get_origin(list_type) is list
        assert get_args(list_type) == (str,)

        # List with text type
        list_type = parse_type_spec("list[text]")
        assert get_origin(list_type) is list
        # text becomes str
        assert get_args(list_type)[0] is str

    def test_square_bracket_syntax(self):
        """Test square bracket syntax for types."""
        from typing import get_args, get_origin

        # Test model with square brackets
        model_type = parse_type_spec("model[auth.User]")
        # Should return Model['auth.User']
        assert_has_metadata(model_type)

        # Test queryset with square brackets
        qs_type = parse_type_spec("queryset[blog.Article]")
        # Should return QuerySet['blog.Article']
        assert_has_metadata(qs_type)

        # Test list with square brackets
        list_type = parse_type_spec("list[int]")
        assert get_origin(list_type) is list
        # Integer() returns int, so list[int] should have int as its type
        assert get_args(list_type)[0] is int

        # Test nested square brackets
        list_type = parse_type_spec("list[text]")
        assert get_origin(list_type) is list
        # Text() returns str, so list[text] should have str as its type
        assert get_args(list_type)[0] is str

    def test_optional_props_from_template_syntax(self):
        """Test parsing optional props with ? marker."""
        from includecontents.shared.typed_props import parse_template_props

        # Test optional prop with ? marker
        props = parse_template_props("name:text email?:email age?:int")
        assert "name" in props
        assert props["name"]["required"] is True
        assert "email" in props
        assert props["email"]["required"] is False
        assert "age" in props
        assert props["age"]["required"] is False

        # Test optional with square bracket syntax
        props = parse_template_props("role?:choice[admin,user,guest]")
        assert "role" in props
        assert props["role"]["required"] is False

        # Test optional with default value (should also be optional)
        props = parse_template_props("status:choice[active,inactive]=active")
        assert "status" in props
        # Default value makes it optional
        assert "status" in props  # This will have a default, making it not required

        # Test mixed required and optional
        props = parse_template_props(
            "id:int name:text description?:text tags?:list[str]"
        )
        assert props["id"]["required"] is True
        assert props["name"]["required"] is True
        assert props["description"]["required"] is False
        assert props["tags"]["required"] is False

    def test_unknown_type(self):
        """Test unknown type defaults to string."""
        unknown_type = parse_type_spec("unknown")
        assert unknown_type is str


class TestComponentDecorator:
    """Test the @component decorator."""

    def test_component_registration(self):
        """Test that components are registered correctly."""
        from includecontents.shared.typed_props import _registry, get_props_class

        # Clear registry for test
        _registry.clear()

        @component("components/test-component.html")
        @dataclass
        class TestProps:
            title: str

        # Check registration
        assert get_props_class("components/test-component.html") is TestProps
        assert TestProps._is_component_props is True
        assert TestProps._template_path == "components/test-component.html"

    def test_auto_dataclass_conversion(self):
        """Test that non-dataclasses are converted."""
        from dataclasses import is_dataclass

        from includecontents.shared.typed_props import _registry

        _registry.clear()

        @component("components/auto-convert.html")
        class AutoProps:
            name: str = "default"

        # Should be converted to dataclass
        assert is_dataclass(AutoProps)
        assert hasattr(AutoProps, "__dataclass_fields__")


# Integration tests would go here, testing actual template rendering
# These would require setting up test templates and components
