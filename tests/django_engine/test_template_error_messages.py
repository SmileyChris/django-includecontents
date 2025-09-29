import pytest
from django.template import TemplateDoesNotExist, TemplateSyntaxError, Context
from includecontents.django.base import Template


def test_missing_component_template_enhanced_error():
    """Test that missing component templates show enhanced error messages."""
    with pytest.raises(TemplateDoesNotExist) as exc_info:
        Template(
            "<include:nonexistent-component>Content</include:nonexistent-component>"
        ).render(Context())

    error_message = str(exc_info.value)

    # Should include the component name in the error
    assert (
        "Component template not found: <include:nonexistent-component>" in error_message
    )

    # Should show what template was looked for
    assert "Looked for:" in error_message

    # Should include helpful suggestions
    assert "Suggestions:" in error_message
    assert "Create template:" in error_message
    assert "templates/components/nonexistent-component.html" in error_message

    # Should suggest checking template directories
    assert "Check TEMPLATES['DIRS'] setting" in error_message


def test_missing_namespaced_component_template_enhanced_error():
    """Test enhanced error for namespaced component templates."""
    with pytest.raises(TemplateDoesNotExist) as exc_info:
        Template("<include:forms:field>Content</include:forms:field>").render(Context())

    error_message = str(exc_info.value)

    # Should include the component name
    assert "Component template not found: <include:forms:field>" in error_message

    # Should suggest the correct path structure
    assert "forms/field" in error_message or "forms:field" in error_message


def test_enhanced_error_preserves_original_tried_list():
    """Test that enhanced errors preserve the original tried list from Django."""
    with pytest.raises(TemplateDoesNotExist) as exc_info:
        Template(
            "<include:missing-component>Content</include:missing-component>"
        ).render(Context())

    error_message = str(exc_info.value)

    # The exception should have the tried attribute
    assert hasattr(exc_info.value, "tried")

    # If there are tries, they should be included in the message
    if exc_info.value.tried:
        assert "Template loader tried:" in error_message


def test_enhanced_error_with_app_structure_suggestion():
    """Test enhanced error includes app-based template suggestions."""
    with pytest.raises(TemplateDoesNotExist) as exc_info:
        Template("<include:user-profile>Content</include:user-profile>").render(
            Context()
        )

    error_message = str(exc_info.value)

    # Should suggest app-based component structure
    assert "For app-based components:" in error_message
    assert "<app>/templates/components/" in error_message


def test_enhanced_error_chaining_preserves_original():
    """Test that error chaining preserves the original exception."""
    with pytest.raises(TemplateDoesNotExist) as exc_info:
        Template("<include:missing>Content</include:missing>").render(Context())

    # Should have the original exception as the cause
    assert exc_info.value.__cause__ is not None
    assert isinstance(exc_info.value.__cause__, TemplateDoesNotExist)


def test_error_enhancement_only_for_components():
    """Test that error enhancement only applies to component includes, not regular includes."""
    with pytest.raises(TemplateDoesNotExist):
        # This uses the regular Django include tag, not our component syntax
        # So it should get normal Django error handling
        Template(
            '{% load includecontents %}{% includecontents "nonexistent.html" %}{% endincludecontents %}'
        ).render(Context())


def test_enhanced_error_message_formatting():
    """Test the formatting and structure of enhanced error messages."""
    with pytest.raises(TemplateDoesNotExist) as exc_info:
        Template("<include:test-component>Content</include:test-component>").render(
            Context()
        )

    error_message = str(exc_info.value)
    lines = error_message.split("\n")

    # Should have structured sections
    component_line = None
    looked_for_line = None
    suggestions_line = None

    for i, line in enumerate(lines):
        if "Component template not found:" in line:
            component_line = i
        elif "Looked for:" in line:
            looked_for_line = i
        elif "Suggestions:" in line:
            suggestions_line = i

    # All sections should be present
    assert component_line is not None
    assert looked_for_line is not None
    assert suggestions_line is not None

    # Should be in logical order
    assert component_line < looked_for_line < suggestions_line


def test_enhanced_error_with_relative_path_components():
    """Test enhanced error handling for components with relative paths."""
    with pytest.raises(TemplateDoesNotExist) as exc_info:
        Template(
            "<include:../outside-component>Content</include:../outside-component>"
        ).render(Context())

    error_message = str(exc_info.value)

    # Should handle relative paths gracefully
    assert "Component template not found:" in error_message
    assert "../outside-component" in error_message


def test_enhanced_error_suggestions_are_actionable():
    """Test that error suggestions provide actionable guidance."""
    with pytest.raises(TemplateDoesNotExist) as exc_info:
        Template("<include:my-widget>Content</include:my-widget>").render(Context())

    error_message = str(exc_info.value)

    # Should provide numbered suggestions
    assert "1." in error_message
    assert "2." in error_message

    # Suggestions should be specific and actionable
    assert "templates/components/my-widget.html" in error_message
    assert "TEMPLATES" in error_message or "template" in error_message.lower()


def test_enhanced_error_handles_empty_template_name():
    """Test enhanced error handling when template name is missing or empty."""
    # This is an edge case that might occur with malformed templates
    # The test ensures our enhancement doesn't break in this scenario
    with pytest.raises((TemplateDoesNotExist, TemplateSyntaxError)):
        # Create a scenario that might result in empty template name
        Template("<include:>Content</include:>").render(Context())
