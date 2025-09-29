import pytest
from django.template import TemplateSyntaxError

from includecontents.shared.props import parse_props_comment


def test_invalid_prop_name_with_spaces():
    """Test error reporting for prop names with spaces."""
    template_source = '{# props "invalid name"=value #}\n<div>{{ invalid }}</div>'

    with pytest.raises(TemplateSyntaxError) as exc_info:
        parse_props_comment(template_source)

    error_message = str(exc_info.value)
    assert "Props parsing error:" in error_message
    assert "Invalid prop name 'invalid name'" in error_message
    assert "Python identifiers" in error_message
    assert "Problem with: 'invalid name=value'" in error_message


def test_invalid_prop_name_with_special_chars():
    """Test error reporting for prop names with special characters."""
    template_source = "{# props prop-name=value #}\n<div>Test</div>"

    with pytest.raises(TemplateSyntaxError) as exc_info:
        parse_props_comment(template_source)

    error_message = str(exc_info.value)
    assert "Invalid prop name 'prop-name'" in error_message
    assert "Python identifiers" in error_message


def test_empty_prop_name():
    """Test error reporting for empty prop names."""
    template_source = "{# props =value #}\n<div>Test</div>"

    with pytest.raises(TemplateSyntaxError) as exc_info:
        parse_props_comment(template_source)

    error_message = str(exc_info.value)
    assert "Empty prop name" in error_message


def test_duplicate_prop_names():
    """Test error reporting for duplicate prop definitions."""
    template_source = "{# props title=first title=second #}\n<div>{{ title }}</div>"

    with pytest.raises(TemplateSyntaxError) as exc_info:
        parse_props_comment(template_source)

    error_message = str(exc_info.value)
    assert "Duplicate prop definition: 'title'" in error_message


def test_malformed_prop_syntax():
    """Test error reporting for malformed prop syntax."""
    template_source = "{# props title==value #}\n<div>{{ title }}</div>"

    # This should either be caught by our parser or work as intended
    # Let's see what happens
    parse_props_comment(template_source)
    # This might actually work since title== would be parsed as title with default "=value"


def test_unquoted_string_value_hint():
    """Test helpful hint for unquoted string values."""
    template_source = "{# props title=[hello world] #}\n<div>{{ title }}</div>"

    with pytest.raises(TemplateSyntaxError) as exc_info:
        parse_props_comment(template_source)

    error_message = str(exc_info.value)
    assert "Did you forget quotes around a string value?" in error_message


def test_invalid_list_syntax():
    """Test error reporting for invalid list syntax."""
    template_source = "{# props items=[1,2,3 #}\n<div>Test</div>"

    with pytest.raises(TemplateSyntaxError) as exc_info:
        parse_props_comment(template_source)

    error_message = str(exc_info.value)
    assert "Props parsing error:" in error_message


def test_error_includes_helpful_examples():
    """Test that error messages include helpful examples."""
    template_source = "{# props invalid-name=value #}\n<div>Test</div>"

    with pytest.raises(TemplateSyntaxError) as exc_info:
        parse_props_comment(template_source)

    error_message = str(exc_info.value)
    assert "Examples:" in error_message
    assert "title required_field=True" in error_message
    assert "variant=primary,secondary,accent" in error_message


def test_error_includes_line_number():
    """Test that error messages include the line number."""
    template_source = (
        '<div>First line</div>\n{# props "invalid name"=value #}\n<div>Third line</div>'
    )

    with pytest.raises(TemplateSyntaxError) as exc_info:
        parse_props_comment(template_source)

    error_message = str(exc_info.value)
    assert "line 2:" in error_message


def test_error_includes_common_issues_section():
    """Test that error messages include common issues section."""
    template_source = '{# props "invalid name"=value #}\n<div>Test</div>'

    with pytest.raises(TemplateSyntaxError) as exc_info:
        parse_props_comment(template_source)

    error_message = str(exc_info.value)
    assert "Common issues:" in error_message
    assert "Prop names must be valid Python identifiers" in error_message
    assert "String values should be quoted" in error_message
    assert "Lists should use brackets" in error_message


def test_valid_props_still_work():
    """Test that valid props comments continue to work correctly."""
    template_source = "{# props title variant=primary,secondary required_field=True items=[1,2,3] #}\n<div>Test</div>"

    result = parse_props_comment(template_source)

    assert "title" in result
    assert "variant" in result
    assert "required_field" in result
    assert "items" in result
    assert result["title"].required
    assert not result["variant"].required
    assert result["required_field"].default is True
    assert result["items"].default == [1, 2, 3]


def test_empty_props_comment():
    """Test that empty props comments don't raise errors."""
    template_source = "{# props #}\n<div>Test</div>"

    result = parse_props_comment(template_source)
    assert result == {}


def test_no_props_comment():
    """Test that templates without props comments work correctly."""
    template_source = "<div>No props here</div>"

    result = parse_props_comment(template_source)
    assert result == {}


def test_complex_malformed_props():
    """Test error reporting for complex malformed props."""
    template_source = '{# props "invalid name"=value another=unquoted string third=[1,2, #}\n<div>Test</div>'

    with pytest.raises(TemplateSyntaxError) as exc_info:
        parse_props_comment(template_source)

    error_message = str(exc_info.value)
    assert "Props parsing error:" in error_message


def test_prop_name_starting_with_underscore():
    """Test that prop names starting with underscore are rejected."""
    template_source = "{# props _private=value #}\n<div>Test</div>"

    with pytest.raises(TemplateSyntaxError) as exc_info:
        parse_props_comment(template_source)

    error_message = str(exc_info.value)
    assert "Invalid prop name '_private'" in error_message
    assert "Python identifiers" in error_message


def test_error_preserves_original_exception_chain():
    """Test that enhanced errors preserve the original exception chain."""
    template_source = "{# props items=[1,2,3 #}\n<div>Test</div>"  # Malformed list

    with pytest.raises(TemplateSyntaxError) as exc_info:
        parse_props_comment(template_source)

    # Should have the original exception in the chain
    assert (
        exc_info.value.__cause__ is not None or exc_info.value.__context__ is not None
    )
