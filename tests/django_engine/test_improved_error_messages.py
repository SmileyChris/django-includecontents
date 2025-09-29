import pytest
from django.template import TemplateSyntaxError, Context
from includecontents.django.base import Template


def test_enum_error_message_with_suggestion():
    """Test that enum validation errors include helpful suggestions."""
    with pytest.raises(TemplateSyntaxError) as exc_info:
        Template(
            '<include:button variant="primari">Close match</include:button>'  # Close to "primary"
        ).render(Context())

    error_message = str(exc_info.value)

    # Should include the suggestion
    assert "Did you mean 'primary'?" in error_message

    # Should include example usage
    assert 'Example: <include:button variant="primary">' in error_message

    # Should include allowed values
    assert "Allowed values: 'primary', 'secondary', 'accent'" in error_message


def test_enum_error_message_with_distant_suggestion():
    """Test error message when the typo is more distant."""
    with pytest.raises(TemplateSyntaxError) as exc_info:
        Template(
            '<include:button variant="secondari">Distant match</include:button>'  # Close to "secondary"
        ).render(Context())

    error_message = str(exc_info.value)

    # Should include the suggestion
    assert "Did you mean 'secondary'?" in error_message


def test_enum_error_message_no_suggestion():
    """Test error message when no close match can be found."""
    with pytest.raises(TemplateSyntaxError) as exc_info:
        Template(
            '<include:button variant="xyz123">No close match</include:button>'
        ).render(Context())

    error_message = str(exc_info.value)

    # Should not include a suggestion
    assert "Did you mean" not in error_message

    # Should still include example usage
    assert 'Example: <include:button variant="primary">' in error_message


def test_enum_error_message_case_sensitivity():
    """Test error message for case-sensitive issues."""
    with pytest.raises(TemplateSyntaxError) as exc_info:
        Template(
            '<include:button variant="PRIMARY">Case issue</include:button>'  # Wrong case
        ).render(Context())

    error_message = str(exc_info.value)

    # Should suggest the correct case
    assert "Did you mean 'primary'?" in error_message


def test_enum_error_message_with_hyphens():
    """Test error message for enum values with hyphens."""
    with pytest.raises(TemplateSyntaxError) as exc_info:
        Template(
            '<include:button-optional variant="dark_mode">Underscore instead of hyphen</include:button-optional>'
        ).render(Context())

    error_message = str(exc_info.value)

    # Should suggest the hyphenated version
    assert "Did you mean 'dark-mode'?" in error_message


def test_multi_value_enum_error_message():
    """Test error message for multi-value enum with one invalid value."""
    with pytest.raises(TemplateSyntaxError) as exc_info:
        Template(
            '<include:button-multi variant="primary icno">Typo in second value</include:button-multi>'  # "icno" should be "icon"
        ).render(Context())

    error_message = str(exc_info.value)

    # Should identify the specific invalid value
    assert 'Invalid value "icno"' in error_message

    # Should suggest the correct value
    assert "Did you mean 'icon'?" in error_message


def test_special_character_enum_error_message():
    """Test error message for special character enum values."""
    with pytest.raises(TemplateSyntaxError) as exc_info:
        Template(
            '<include:enum-edge-cases special="&">Invalid special char</include:enum-edge-cases>'
        ).render(Context())

    error_message = str(exc_info.value)

    # Should show the allowed special characters
    assert "Allowed values: '@', '#', '$', '%'" in error_message

    # Should include example with first allowed value
    assert 'Example: <include:enum-edge-cases special="@">' in error_message


def test_detailed_error_message_format():
    """Test the overall format of the improved error message."""
    with pytest.raises(TemplateSyntaxError) as exc_info:
        Template('<include:button variant="invalid">Test</include:button>').render(
            Context()
        )

    error_message = str(exc_info.value)
    lines = error_message.split("\n")

    # Should have exactly 2 lines: error description + example
    assert len(lines) == 2

    # First line should be the error description
    assert 'Invalid value "invalid" for attribute "variant"' in lines[0]
    assert "Allowed values:" in lines[0]

    # Second line should be the example
    assert lines[1].startswith("Example: ")


def test_suggestion_algorithm_edge_cases():
    """Test the suggestion algorithm with various edge cases."""
    from includecontents.templatetags.includecontents import IncludeContentsNode

    # Test with empty inputs
    assert IncludeContentsNode._suggest_closest_enum_value("", ()) is None
    assert IncludeContentsNode._suggest_closest_enum_value("test", ()) is None

    # Test with very different strings (should return None due to low similarity)
    result = IncludeContentsNode._suggest_closest_enum_value(
        "xyz", ("primary", "secondary")
    )
    assert result is None  # Should be below the 40% cutoff

    # Test with close matches
    result = IncludeContentsNode._suggest_closest_enum_value(
        "primery", ("primary", "secondary")
    )
    assert result == "primary"

    # Test with exact match (shouldn't normally happen in error path, but good to test)
    result = IncludeContentsNode._suggest_closest_enum_value(
        "primary", ("primary", "secondary")
    )
    assert result == "primary"


def test_error_message_integration_with_existing_validation():
    """Test that the improved error messages work with existing validation patterns."""
    # Test with enum that has empty string as valid value
    with pytest.raises(TemplateSyntaxError) as exc_info:
        Template(
            '<include:button-optional variant="invalid">Should allow empty</include:button-optional>'
        ).render(Context())

    error_message = str(exc_info.value)

    # Should include allowed values and not break the suggestion
    assert "Allowed values:" in error_message
    assert 'Example: <include:button-optional variant="primary">' in error_message


def test_error_message_preserves_original_functionality():
    """Test that improved error messages don't break existing error detection."""
    # Invalid enum value should still be caught
    with pytest.raises(TemplateSyntaxError, match='Invalid value "nonexistent"'):
        Template('<include:button variant="nonexistent">Test</include:button>').render(
            Context()
        )

    # Valid enum value should still work
    template = Template('<include:button variant="primary">Test</include:button>')
    output = template.render(Context())
    assert "btn-primary" in output
    assert "Test" in output
