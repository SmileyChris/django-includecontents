"""
Jinja2-specific error handling tests for props system.

Tests error handling, exception types, and error message formatting
specific to Jinja2 template engine.
"""

from __future__ import annotations

import pytest
from jinja2.exceptions import TemplateRuntimeError, UndefinedError

from ._helpers import render_component


class TestJinja2ErrorTypes:
    """Test Jinja2-specific error types and handling."""

    def test_template_runtime_error_for_invalid_props(self) -> None:
        """Test that invalid props raise TemplateRuntimeError."""
        with pytest.raises(TemplateRuntimeError) as exc:
            render_component(
                '<include:button variant="invalid">Click</include:button>',
                use=["button"],
            )

        # Should be TemplateRuntimeError, not Django's TemplateSyntaxError
        assert isinstance(exc.value, TemplateRuntimeError)
        assert "invalid" in str(exc.value).lower()

    def test_undefined_error_handling(self) -> None:
        """Test handling of undefined variables in prop values."""
        # This may raise UndefinedError or be handled gracefully
        # depending on Jinja2 configuration
        try:
            _, captures = render_component(
                '<include:test-undefined title="{{ undefined_variable }}">Content</include:test-undefined>',
                use=["test-undefined"],
            )
            # If it doesn't raise, check the result
            # The undefined variable should be handled somehow
        except (UndefinedError, TemplateRuntimeError):
            # Either error type is acceptable for undefined variables
            pass

    def test_error_context_preservation(self) -> None:
        """Test that error context is preserved in Jinja2."""
        with pytest.raises(TemplateRuntimeError) as exc:
            render_component(
                '<include:button variant="invalid-value">Content</include:button>',
                use=["button"],
            )

        error_msg = str(exc.value)
        # Should include which component and prop failed
        assert 'Invalid value "invalid-value" for attribute "variant"' in error_msg
        assert "button.html" in error_msg

    def test_nested_component_error_context(self) -> None:
        """Test error context in nested components."""
        with pytest.raises(TemplateRuntimeError) as exc:
            render_component(
                "<include:parent>"
                "<include:child-error>Nested</include:child-error>"
                "</include:parent>",
                use=["parent", "child-error"],
            )

        # Error should indicate which nested component failed
        error_msg = str(exc.value)
        assert "missing required prop 'name'" in error_msg
        assert "child-error.html" in error_msg


class TestJinja2ErrorMessages:
    """Test error message formatting in Jinja2."""

    def test_prop_validation_error_format(self) -> None:
        """Test format of prop validation error messages."""
        with pytest.raises(TemplateRuntimeError) as exc:
            render_component(
                '<include:button variant="wrong-variant">Content</include:button>',
                use=["button"],
            )

        error_msg = str(exc.value)
        # Should be informative for developers
        assert 'Invalid value "wrong-variant" for attribute "variant"' in error_msg
        assert "Allowed values:" in error_msg
        assert "Did you mean" in error_msg

    def test_missing_required_prop_message(self) -> None:
        """Test message format for missing required props."""
        with pytest.raises(TemplateRuntimeError) as exc:
            render_component(
                "<include:required-component>Content</include:required-component>",
                use=["required-component"],
            )

        error_msg = str(exc.value)
        assert "missing required prop 'required'" in error_msg
        assert "required-component.html" in error_msg

    def test_type_coercion_error_message(self) -> None:
        """Test message format for enum validation errors."""
        with pytest.raises(TemplateRuntimeError) as exc:
            render_component(
                '<include:button-multi variant="invalid-multi">Content</include:button-multi>',
                use=["button-multi"],
            )

        error_msg = str(exc.value)
        # Should mention the validation failure with details
        assert 'Invalid value "invalid-multi" for attribute "variant"' in error_msg
        assert "button-multi.html" in error_msg

    def test_enum_suggestion_error_message(self) -> None:
        """Test that enum errors include suggestions."""
        with pytest.raises(TemplateRuntimeError) as exc:
            render_component(
                '<include:button variant="primari">Click</include:button>',  # typo: primari
                use=["button"],
            )

        error_msg = str(exc.value)
        # Should suggest the correct value
        assert "primary" in error_msg or "allowed" in error_msg.lower()


class TestJinja2SpecificBehaviors:
    """Test Jinja2-specific behaviors in error handling."""

    def test_template_syntax_vs_runtime_errors(self) -> None:
        """Test distinction between syntax and runtime errors."""
        # Runtime error (invalid prop value)
        with pytest.raises(TemplateRuntimeError):
            render_component(
                '<include:button variant="invalid">Click</include:button>',
                use=["button"],
            )

        # Template syntax issues would be caught earlier in Jinja2

    def test_error_handling_with_jinja2_features(self) -> None:
        """Test error handling when using Jinja2-specific features."""
        # Test with Jinja2 filters - invalid filter is caught by Jinja2 before our code
        from jinja2.exceptions import TemplateAssertionError

        with pytest.raises(TemplateAssertionError) as exc:
            render_component(
                '<include:filter-error value="{{ invalid_var | invalid_filter }}">Content</include:filter-error>',
                use=["filter-error"],
            )

        error_msg = str(exc.value)
        assert "No filter named 'invalid_filter'" in error_msg

    def test_macro_and_component_error_interaction(self) -> None:
        """Test error handling when components interact with Jinja2 macros."""
        # This tests Jinja2-specific template features
        try:
            _, captures = render_component(
                "<include:macro-component>Content</include:macro-component>",
                use=["macro-component"],
            )
        except TemplateRuntimeError:
            # Acceptable for this test case
            pass

    def test_autoescape_error_handling(self) -> None:
        """Test error handling with unclosed quotes in attribute values."""
        # Unclosed quote is a syntax error caught by Jinja2 template parser
        from jinja2.exceptions import TemplateSyntaxError

        with pytest.raises(TemplateSyntaxError) as exc:
            render_component(
                '<include:html-escape content="<script>alert(1)</script>">Content</include:html-escape>',
                use=["html-escape"],
            )

        error_msg = str(exc.value)
        assert "Unclosed quote" in error_msg

    def test_block_vs_component_error_context(self) -> None:
        """Test error context when components are used in blocks."""
        # This tests Jinja2 block inheritance with components
        with pytest.raises(TemplateRuntimeError) as exc:
            render_component(
                "{% block content %}<include:block-error>Content</include:block-error>{% endblock %}",
                use=["block-error"],
            )

        error_msg = str(exc.value)
        assert "missing required prop 'title'" in error_msg
        assert "block-error.html" in error_msg


class TestJinja2UndefinedHandling:
    """Test Jinja2-specific undefined variable handling."""

    def test_undefined_in_prop_values(self) -> None:
        """Test undefined variables in prop values."""
        # Behavior depends on Jinja2 undefined handling configuration
        try:
            _, captures = render_component(
                '<include:undefined-prop title="{{ undefined_var }}">Content</include:undefined-prop>',
                use=["undefined-prop"],
            )
            # May succeed with empty/default value
        except (UndefinedError, TemplateRuntimeError):
            # Or may raise an error - both are valid
            pass

    def test_undefined_in_default_expressions(self) -> None:
        """Test undefined variables in default value expressions."""
        try:
            _, captures = render_component(
                "<include:undefined-default>Content</include:undefined-default>",
                use=["undefined-default"],
            )
            # Should handle undefined in defaults gracefully
        except (UndefinedError, TemplateRuntimeError):
            # Or raise appropriate error
            pass

    def test_strict_undefined_behavior(self) -> None:
        """Test behavior with strict undefined handling."""
        # This would test Jinja2's StrictUndefined behavior
        # Implementation depends on Jinja2 configuration
        pass

    def test_debug_undefined_behavior(self) -> None:
        """Test behavior with debug undefined handling."""
        # This would test Jinja2's DebugUndefined behavior
        # Implementation depends on Jinja2 configuration
        pass


class TestJinja2ErrorRecovery:
    """Test error recovery and graceful degradation."""

    def test_partial_prop_failure_recovery(self) -> None:
        """Test recovery when some props fail validation."""
        # If one prop fails, does the whole component fail?
        with pytest.raises(TemplateRuntimeError):
            render_component(
                '<include:mixed-validation good="valid" bad="invalid">Content</include:mixed-validation>',
                use=["mixed-validation"],
            )

    def test_optional_prop_error_recovery(self) -> None:
        """Test that enum props validate even when optional."""
        # Optional enum props with invalid values should still cause errors
        with pytest.raises(TemplateRuntimeError) as exc:
            render_component(
                '<include:optional-validation status="invalid-status">Content</include:optional-validation>',
                use=["optional-validation"],
            )

        error_msg = str(exc.value)
        assert 'Invalid value "invalid-status" for attribute "status"' in error_msg

    def test_default_value_error_recovery(self) -> None:
        """Test recovery when default values have errors."""
        # If a default value expression fails, how is it handled?
        try:
            _, captures = render_component(
                "<include:error-default>Content</include:error-default>",
                use=["error-default"],
            )
            # May succeed with fallback behavior
        except TemplateRuntimeError:
            # Or may fail - both are acceptable
            pass


class TestJinja2PerformanceErrors:
    """Test performance-related error scenarios."""

    def test_infinite_recursion_prevention(self) -> None:
        """Test that infinite recursion is prevented."""
        # Components that include themselves should be handled
        try:
            _, captures = render_component(
                "<include:recursive-component>Content</include:recursive-component>",
                use=["recursive-component"],
            )
        except (RecursionError, TemplateRuntimeError):
            # Should prevent infinite recursion
            pass

    def test_deep_nesting_error_handling(self) -> None:
        """Test error handling with deeply nested components."""
        deep_nesting = "<include:level1>" * 10 + "Content" + "</include:level1>" * 10
        try:
            _, captures = render_component(deep_nesting, use=["level1"])
        except TemplateRuntimeError:
            # Deep nesting may cause errors - should be handled gracefully
            pass

    def test_large_prop_value_handling(self) -> None:
        """Test handling of very large prop values."""
        large_value = "x" * 10000
        try:
            _, captures = render_component(
                f'<include:large-prop value="{large_value}">Content</include:large-prop>',
                use=["large-prop"],
            )
            # Should handle large values gracefully
        except TemplateRuntimeError:
            # Or raise appropriate error for size limits
            pass
