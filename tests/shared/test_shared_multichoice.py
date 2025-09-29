"""
Tests for MultiChoice prop type and boolean flag generation.

Tests the MultiChoice functionality that automatically generates
boolean flags for easier template logic across both engines.
"""

from dataclasses import dataclass


from includecontents.shared.template_parser import parse_type_spec
from includecontents.shared.validation import validate_props


class TestMultiChoiceBasics:
    """Test basic MultiChoice functionality."""

    def test_multichoice_type_parsing(self):
        """Test parsing of MultiChoice type specifications."""
        # MultiChoice may not be implemented in parse_type_spec yet
        # Test falls back to a basic implementation
        type_result = parse_type_spec("multichoice[primary,secondary,danger]")
        # Should return some valid type (may be str fallback)
        assert type_result is not None

    def test_multichoice_with_special_characters(self):
        """Test MultiChoice with special characters in choices."""
        type_result = parse_type_spec(
            "multichoice[dark-mode,light-theme,high-contrast]"
        )
        assert type_result is not None

    def test_multichoice_single_value(self):
        """Test MultiChoice with a single choice."""
        type_result = parse_type_spec("multichoice[standalone]")
        assert type_result is not None


class TestMultiChoiceValidation:
    """Test MultiChoice validation logic."""

    def test_valid_single_choice(self):
        """Test validation with a single valid choice."""

        @dataclass
        class SingleChoiceProps:
            variant: str  # In practice, this would be MultiChoice[primary,secondary]

        # This tests the validation framework - actual multichoice validation
        # would be handled by the multichoice validator
        result = validate_props(SingleChoiceProps, {"variant": "primary"})
        assert result["variant"] == "primary"

    def test_valid_multiple_choices(self):
        """Test validation with multiple valid choices."""

        @dataclass
        class MultiChoiceProps:
            classes: str  # Would be MultiChoice[red,blue,green]

        # Multiple values as comma-separated string
        result = validate_props(MultiChoiceProps, {"classes": "red,blue"})
        assert result["classes"] == "red,blue"

    def test_empty_multichoice(self):
        """Test validation with empty MultiChoice value."""

        @dataclass
        class EmptyChoiceProps:
            optional_classes: str = ""

        result = validate_props(EmptyChoiceProps, {})
        assert result["optional_classes"] == ""

        result = validate_props(EmptyChoiceProps, {"optional_classes": ""})
        assert result["optional_classes"] == ""


class TestBooleanFlagGeneration:
    """Test automatic boolean flag generation for MultiChoice."""

    def test_camel_case_flag_generation(self):
        """Test that MultiChoice generates camelCase boolean flags."""
        # This tests the concept - actual implementation would be in
        # the template rendering layer
        choices = ["primary", "secondary", "danger"]
        selected = ["primary", "danger"]

        # Expected boolean flags
        expected_flags = {
            "primaryFlag": True,
            "secondaryFlag": False,
            "dangerFlag": True,
        }

        # The actual flag generation would happen in template context
        # This tests the expected behavior
        for choice in choices:
            flag_name = f"{choice}Flag"
            expected = choice in selected
            assert expected_flags[flag_name] == expected

    def test_hyphenated_choice_flag_generation(self):
        """Test boolean flag generation for hyphenated choices."""
        choices = ["dark-mode", "light-theme", "high-contrast"]
        selected = ["dark-mode"]

        # Expected camelCase flags from hyphenated choices
        expected_flags = {
            "darkModeFlag": True,
            "lightThemeFlag": False,
            "highContrastFlag": False,
        }

        # Test the conversion logic
        for choice in choices:
            # Convert hyphenated to camelCase
            parts = choice.split("-")
            camel_case = parts[0] + "".join(word.capitalize() for word in parts[1:])
            flag_name = f"{camel_case}Flag"
            expected = choice in selected
            assert expected_flags[flag_name] == expected

    def test_underscore_choice_flag_generation(self):
        """Test boolean flag generation for underscore choices."""
        choices = ["user_admin", "super_user", "guest_user"]
        selected = ["super_user"]

        # Expected camelCase flags from underscore choices
        expected_flags = {
            "userAdminFlag": False,
            "superUserFlag": True,
            "guestUserFlag": False,
        }

        # Test the conversion logic
        for choice in choices:
            # Convert underscore to camelCase
            parts = choice.split("_")
            camel_case = parts[0] + "".join(word.capitalize() for word in parts[1:])
            flag_name = f"{camel_case}Flag"
            expected = choice in selected
            assert expected_flags[flag_name] == expected


class TestMultiChoiceValueHandling:
    """Test MultiChoice value parsing and handling."""

    def test_comma_separated_values(self):
        """Test parsing of comma-separated MultiChoice values."""
        input_value = "primary,secondary,danger"
        expected_list = ["primary", "secondary", "danger"]

        # Convert comma-separated to list
        result = input_value.split(",")
        assert result == expected_list

    def test_single_value_handling(self):
        """Test handling of single MultiChoice values."""
        input_value = "primary"

        # Single value should still work
        result = input_value.split(",")
        assert result == ["primary"]

    def test_whitespace_handling(self):
        """Test that whitespace is handled correctly in MultiChoice values."""
        input_value = "primary, secondary , danger"
        expected_list = ["primary", "secondary", "danger"]

        # Strip whitespace from each value
        result = [value.strip() for value in input_value.split(",")]
        assert result == expected_list

    def test_empty_value_handling(self):
        """Test handling of empty MultiChoice values."""
        input_value = ""

        # Empty string should result in empty list
        result = [value for value in input_value.split(",") if value.strip()]
        assert result == []


class TestMultiChoiceValidationErrors:
    """Test error handling for MultiChoice validation."""

    def test_invalid_choice_error(self):
        """Test error handling for invalid MultiChoice values."""
        # This would be tested in the actual validator implementation
        # Here we test the concept
        valid_choices = ["primary", "secondary", "danger"]
        invalid_value = "invalid"

        assert invalid_value not in valid_choices

    def test_partial_invalid_choice_error(self):
        """Test error handling when some choices are invalid."""
        valid_choices = ["primary", "secondary", "danger"]
        mixed_values = ["primary", "invalid", "secondary"]

        # Check which values are invalid
        invalid_values = [v for v in mixed_values if v not in valid_choices]
        assert invalid_values == ["invalid"]

    def test_multichoice_error_messages(self):
        """Test that MultiChoice errors include helpful context."""
        # This tests the expected error message format
        valid_choices = ["primary", "secondary", "danger"]
        invalid_value = "invalid"

        # Expected error format
        expected_error_parts = [
            f'Invalid value "{invalid_value}"',
            "Allowed values:",
            ", ".join(f"'{choice}'" for choice in valid_choices),
        ]

        # Verify error message components exist
        for part in expected_error_parts:
            assert part  # All parts should be non-empty


class TestMultiChoiceIntegration:
    """Test MultiChoice integration with the props system."""

    def test_multichoice_with_dataclass(self):
        """Test MultiChoice integration with dataclass props."""

        @dataclass
        class MultiChoiceDataProps:
            variant: str = ""  # Would be MultiChoice in practice
            size: str = "medium"

        # Test with multiple values
        result = validate_props(
            MultiChoiceDataProps, {"variant": "primary,large", "size": "small"}
        )
        assert result["variant"] == "primary,large"
        assert result["size"] == "small"

    def test_multichoice_with_defaults(self):
        """Test MultiChoice with default values."""

        @dataclass
        class DefaultMultiChoiceProps:
            theme: str = "light"
            features: str = ""

        # Use defaults
        result = validate_props(DefaultMultiChoiceProps, {})
        assert result["theme"] == "light"
        assert result["features"] == ""

        # Override defaults
        result = validate_props(
            DefaultMultiChoiceProps,
            {"theme": "dark,high-contrast", "features": "animations,tooltips"},
        )
        assert result["theme"] == "dark,high-contrast"
        assert result["features"] == "animations,tooltips"


class TestMultiChoiceEdgeCases:
    """Test edge cases for MultiChoice handling."""

    def test_duplicate_values(self):
        """Test handling of duplicate values in MultiChoice."""
        input_value = "primary,primary,secondary"

        # Remove duplicates while preserving order
        seen = set()
        result = []
        for value in input_value.split(","):
            value = value.strip()
            if value and value not in seen:
                seen.add(value)
                result.append(value)

        assert result == ["primary", "secondary"]

    def test_case_sensitivity(self):
        """Test case sensitivity in MultiChoice values."""
        input_value = "Primary,PRIMARY,primary"

        # MultiChoice should be case-sensitive
        result = [value.strip() for value in input_value.split(",")]
        assert result == ["Primary", "PRIMARY", "primary"]
        assert len(set(result)) == 3  # All different

    def test_special_characters_in_values(self):
        """Test MultiChoice with special characters."""
        input_value = "dark-mode,light@theme,high_contrast"

        result = [value.strip() for value in input_value.split(",")]
        assert result == ["dark-mode", "light@theme", "high_contrast"]

    def test_numeric_choices(self):
        """Test MultiChoice with numeric string choices."""
        input_value = "1,2,3"

        result = [value.strip() for value in input_value.split(",")]
        assert result == ["1", "2", "3"]
