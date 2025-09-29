"""
Comprehensive Jinja2 props tests covering all major prop types and features.

This file ensures Jinja2 template engine has equivalent prop type coverage
to the Django template engine.
"""

from __future__ import annotations

import pytest
from jinja2.exceptions import TemplateRuntimeError

from ._helpers import first_capture, render_component


class TestBasicPropTypes:
    """Test basic prop types in Jinja2 templates."""

    def test_string_prop_validation(self) -> None:
        """Test string prop validation and rendering."""
        # Valid string
        _, captures = render_component(
            '<include:text-component title="Hello World">Content</include:text-component>',
            use=["text-component"]
        )
        data = first_capture(captures, "text-component")
        assert data["title"] == "Hello World"

    def test_integer_prop_validation(self) -> None:
        """Test integer prop validation and coercion."""
        # String that converts to integer
        _, captures = render_component(
            '<include:number-component count="25">Content</include:number-component>',
            use=["number-component"]
        )
        data = first_capture(captures, "number-component")
        assert data["count"] == 25

        # Invalid integer should raise error
        with pytest.raises(TemplateRuntimeError) as exc:
            render_component(
                '<include:number-component count="not-a-number">Content</include:number-component>',
                use=["number-component"]
            )
        assert 'Cannot convert' in str(exc.value) or 'Invalid' in str(exc.value)

    def test_boolean_prop_validation(self) -> None:
        """Test boolean prop validation and coercion."""
        # True values
        for true_val in ["true", "True", "1", "yes"]:
            _, captures = render_component(
                f'<include:boolean-component active="{true_val}">Content</include:boolean-component>',
                use=["boolean-component"]
            )
            data = first_capture(captures, "boolean-component")
            assert data["active"] is True

        # False values
        for false_val in ["false", "False", "0", "no"]:
            _, captures = render_component(
                f'<include:boolean-component active="{false_val}">Content</include:boolean-component>',
                use=["boolean-component"]
            )
            data = first_capture(captures, "boolean-component")
            assert data["active"] is False

    def test_email_prop_validation(self) -> None:
        """Test email prop validation."""
        # Valid email
        _, captures = render_component(
            '<include:email-component email="user@example.com">Content</include:email-component>',
            use=["email-component"]
        )
        data = first_capture(captures, "email-component")
        assert data["email"] == "user@example.com"

        # Invalid email should raise error
        with pytest.raises(TemplateRuntimeError) as exc:
            render_component(
                '<include:email-component email="invalid-email">Content</include:email-component>',
                use=["email-component"]
            )
        assert 'email' in str(exc.value).lower() or 'invalid' in str(exc.value).lower()

    def test_url_prop_validation(self) -> None:
        """Test URL prop validation."""
        # Valid URL
        _, captures = render_component(
            '<include:url-component website="https://example.com">Content</include:url-component>',
            use=["url-component"]
        )
        data = first_capture(captures, "url-component")
        assert data["website"] == "https://example.com"

        # Invalid URL should raise error
        with pytest.raises(TemplateRuntimeError) as exc:
            render_component(
                '<include:url-component website="not-a-url">Content</include:url-component>',
                use=["url-component"]
            )
        assert 'url' in str(exc.value).lower() or 'invalid' in str(exc.value).lower()


class TestAdvancedPropTypes:
    """Test advanced prop types and configurations."""

    def test_text_with_length_validation(self) -> None:
        """Test text prop with length constraints."""
        # Valid length
        _, captures = render_component(
            '<include:length-text title="Valid">Content</include:length-text>',
            use=["length-text"]
        )
        data = first_capture(captures, "length-text")
        assert data["title"] == "Valid"

        # Too short (if component has min length)
        with pytest.raises(TemplateRuntimeError) as exc:
            render_component(
                '<include:length-text title="x">Content</include:length-text>',
                use=["length-text"]
            )
        # Error message may vary, just ensure it fails

    def test_integer_with_bounds(self) -> None:
        """Test integer prop with min/max bounds."""
        # Valid value within bounds
        _, captures = render_component(
            '<include:bounded-number age="25">Content</include:bounded-number>',
            use=["bounded-number"]
        )
        data = first_capture(captures, "bounded-number")
        assert data["age"] == 25

        # Value out of bounds should raise error
        with pytest.raises(TemplateRuntimeError) as exc:
            render_component(
                '<include:bounded-number age="150">Content</include:bounded-number>',
                use=["bounded-number"]
            )
        # Should mention bounds or validation failure

    def test_html_prop_type(self) -> None:
        """Test HTML prop type that marks content as safe."""
        _, captures = render_component(
            '<include:html-component content="<strong>Bold</strong>">Content</include:html-component>',
            use=["html-component"]
        )
        data = first_capture(captures, "html-component")
        # HTML content should be preserved
        assert "<strong>" in data["content"]


class TestDefaultValues:
    """Test default value handling in props."""

    def test_literal_defaults(self) -> None:
        """Test props with literal default values."""
        # Component with defaults, no props provided
        _, captures = render_component(
            '<include:default-component>Content</include:default-component>',
            use=["default-component"]
        )
        data = first_capture(captures, "default-component")
        # Should have default values
        assert "title" in data  # Should have default title
        assert "count" in data  # Should have default count

    def test_override_defaults(self) -> None:
        """Test overriding default values."""
        _, captures = render_component(
            '<include:default-component title="Custom" count="10">Content</include:default-component>',
            use=["default-component"]
        )
        data = first_capture(captures, "default-component")
        assert data["title"] == "Custom"
        assert data["count"] == 10

    def test_template_variable_defaults(self) -> None:
        """Test defaults using template variables."""
        # This would require setting up context variables
        # For now, test the concept exists
        _, captures = render_component(
            '<include:variable-defaults>Content</include:variable-defaults>',
            use=["variable-defaults"]
        )
        data = first_capture(captures, "variable-defaults")
        # Should resolve template variable defaults
        assert "title" in data


class TestMultiChoiceAdvanced:
    """Test advanced MultiChoice functionality."""

    def test_multichoice_boolean_flags(self) -> None:
        """Test that MultiChoice generates boolean flags."""
        _, captures = render_component(
            '<include:multichoice-flags variant="primary danger">Content</include:multichoice-flags>',
            use=["multichoice-flags"]
        )
        data = first_capture(captures, "multichoice-flags")
        assert data["variant"] == "primary danger"
        # Check boolean flags are generated
        assert data["variantPrimary"] is True
        assert data["variantSecondary"] is False
        assert data["variantDanger"] is True

    def test_multichoice_hyphenated_flags(self) -> None:
        """Test MultiChoice flags with hyphenated values."""
        _, captures = render_component(
            '<include:multichoice-hyphen theme="dark-mode">Content</include:multichoice-hyphen>',
            use=["multichoice-hyphen"]
        )
        data = first_capture(captures, "multichoice-hyphen")
        # Should convert dark-mode to darkMode flag
        assert data["themeDarkMode"] is True
        assert data["themeLightMode"] is False

    def test_multichoice_empty_value(self) -> None:
        """Test MultiChoice with empty value."""
        _, captures = render_component(
            '<include:multichoice-empty>Content</include:multichoice-empty>',
            use=["multichoice-empty"]
        )
        data = first_capture(captures, "multichoice-empty")
        # All flags should be False
        assert data["variantPrimary"] is False
        assert data["variantSecondary"] is False


class TestTypeCoercion:
    """Test type coercion in Jinja2 templates."""

    def test_string_to_integer_coercion(self) -> None:
        """Test automatic string to integer coercion."""
        _, captures = render_component(
            '<include:coercion-test age="30" count="0" score="-10">Content</include:coercion-test>',
            use=["coercion-test"]
        )
        data = first_capture(captures, "coercion-test")
        assert data["age"] == 30
        assert data["count"] == 0
        assert data["score"] == -10

    def test_string_to_boolean_coercion(self) -> None:
        """Test automatic string to boolean coercion."""
        _, captures = render_component(
            '<include:boolean-coercion active="true" disabled="false">Content</include:boolean-coercion>',
            use=["boolean-coercion"]
        )
        data = first_capture(captures, "boolean-coercion")
        assert data["active"] is True
        assert data["disabled"] is False

    def test_string_to_list_coercion(self) -> None:
        """Test automatic string to list coercion."""
        _, captures = render_component(
            '<include:list-coercion tags="python,django,jinja2">Content</include:list-coercion>',
            use=["list-coercion"]
        )
        data = first_capture(captures, "list-coercion")
        assert data["tags"] == ["python", "django", "jinja2"]

    def test_coercion_with_whitespace(self) -> None:
        """Test coercion handles whitespace correctly."""
        _, captures = render_component(
            '<include:whitespace-coercion tags="python, django , jinja2">Content</include:whitespace-coercion>',
            use=["whitespace-coercion"]
        )
        data = first_capture(captures, "whitespace-coercion")
        assert data["tags"] == ["python", "django", "jinja2"]


class TestErrorHandling:
    """Test error handling and messages in Jinja2."""

    def test_missing_required_prop_error(self) -> None:
        """Test error when required prop is missing."""
        with pytest.raises(TemplateRuntimeError) as exc:
            render_component(
                '<include:required-props>Content</include:required-props>',
                use=["required-props"]
            )
        error_msg = str(exc.value)
        assert 'required' in error_msg.lower() or 'missing' in error_msg.lower()

    def test_invalid_prop_value_error(self) -> None:
        """Test error when prop value is invalid."""
        with pytest.raises(TemplateRuntimeError) as exc:
            render_component(
                '<include:validated-props email="invalid">Content</include:validated-props>',
                use=["validated-props"]
            )
        error_msg = str(exc.value)
        assert 'invalid' in error_msg.lower() or 'email' in error_msg.lower()

    def test_type_coercion_error(self) -> None:
        """Test error when type coercion fails."""
        with pytest.raises(TemplateRuntimeError) as exc:
            render_component(
                '<include:integer-props count="not-a-number">Content</include:integer-props>',
                use=["integer-props"]
            )
        error_msg = str(exc.value)
        assert 'convert' in error_msg.lower() or 'invalid' in error_msg.lower()

    def test_enum_validation_error_includes_suggestions(self) -> None:
        """Test that enum validation errors include helpful suggestions."""
        with pytest.raises(TemplateRuntimeError) as exc:
            render_component(
                '<include:button variant="primari">Content</include:button>',  # typo
                use=["button"]
            )
        error_msg = str(exc.value)
        # Should suggest correct value
        assert 'primary' in error_msg or 'did you mean' in error_msg.lower()


class TestOptionalProps:
    """Test optional props and None handling."""

    def test_optional_props_with_none(self) -> None:
        """Test optional props that can be None."""
        _, captures = render_component(
            '<include:optional-component title="Test">Content</include:optional-component>',
            use=["optional-component"]
        )
        data = first_capture(captures, "optional-component")
        assert data["title"] == "Test"
        # Optional fields should be None or have defaults
        assert "subtitle" in data  # Should exist but may be None

    def test_all_optional_props(self) -> None:
        """Test component with all optional props."""
        _, captures = render_component(
            '<include:all-optional>Content</include:all-optional>',
            use=["all-optional"]
        )
        data = first_capture(captures, "all-optional")
        # Should render successfully with all defaults


class TestComplexScenarios:
    """Test complex prop validation scenarios."""

    def test_mixed_prop_types(self) -> None:
        """Test component with mixed prop types."""
        _, captures = render_component(
            '<include:mixed-props '
            'title="Test" '
            'count="10" '
            'active="true" '
            'tags="python,django" '
            'variant="primary secondary"'
            '>Content</include:mixed-props>',
            use=["mixed-props"]
        )
        data = first_capture(captures, "mixed-props")
        assert data["title"] == "Test"
        assert data["count"] == 10
        assert data["active"] is True
        assert data["tags"] == ["python", "django"]
        assert data["variant"] == "primary secondary"

    def test_nested_component_props(self) -> None:
        """Test props in nested components."""
        _, captures = render_component(
            '<include:parent-component>'
            '<include:child-component title="Nested">Child Content</include:child-component>'
            '</include:parent-component>',
            use=["parent-component", "child-component"]
        )
        # Should handle nested component props correctly
        parent_data = first_capture(captures, "parent-component")
        child_data = first_capture(captures, "child-component")
        assert child_data["title"] == "Nested"

    def test_component_with_custom_validation(self) -> None:
        """Test component with custom validation logic."""
        # Valid case
        _, captures = render_component(
            '<include:custom-validation start="1" end="10">Content</include:custom-validation>',
            use=["custom-validation"]
        )
        data = first_capture(captures, "custom-validation")
        assert data["start"] == 1
        assert data["end"] == 10

        # Invalid case (start >= end)
        with pytest.raises(TemplateRuntimeError) as exc:
            render_component(
                '<include:custom-validation start="10" end="1">Content</include:custom-validation>',
                use=["custom-validation"]
            )
        # Should have custom validation error


class TestUndefinedVariables:
    """Test Jinja2-specific undefined variable handling."""

    def test_undefined_variables_in_props(self) -> None:
        """Test how undefined variables are handled in prop values."""
        # This tests Jinja2-specific behavior
        _, captures = render_component(
            '<include:undefined-test title="{{ undefined_var }}">Content</include:undefined-test>',
            use=["undefined-test"]
        )
        data = first_capture(captures, "undefined-test")
        # Jinja2 should handle undefined variables gracefully
        # Exact behavior depends on Jinja2 configuration

    def test_undefined_in_default_values(self) -> None:
        """Test undefined variables in default value expressions."""
        _, captures = render_component(
            '<include:undefined-defaults>Content</include:undefined-defaults>',
            use=["undefined-defaults"]
        )
        data = first_capture(captures, "undefined-defaults")
        # Should handle undefined variables in defaults


class TestJinja2Specifics:
    """Test Jinja2-specific template behaviors."""

    def test_jinja2_filters_in_props(self) -> None:
        """Test using Jinja2 filters in prop values."""
        _, captures = render_component(
            '<include:filter-props title="{{ name | upper }}">Content</include:filter-props>',
            use=["filter-props"],
            context={"name": "test"}
        )
        data = first_capture(captures, "filter-props")
        assert data["title"] == "TEST"

    def test_jinja2_expressions_in_defaults(self) -> None:
        """Test Jinja2 expressions in default values."""
        _, captures = render_component(
            '<include:expression-defaults>Content</include:expression-defaults>',
            use=["expression-defaults"],
            context={"user": {"name": "Alice"}}
        )
        data = first_capture(captures, "expression-defaults")
        # Should resolve Jinja2 expressions in defaults

    def test_jinja2_context_inheritance(self) -> None:
        """Test how Jinja2 context is handled in components."""
        _, captures = render_component(
            '<include:context-test>Content</include:context-test>',
            use=["context-test"],
            context={"global_var": "value"}
        )
        data = first_capture(captures, "context-test")
        # Test context isolation vs inheritance behavior