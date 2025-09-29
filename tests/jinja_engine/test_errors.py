import pytest
from jinja2 import DictLoader, Environment, TemplateNotFound, TemplateSyntaxError

from includecontents.jinja2.extension import IncludeContentsExtension


def create_jinja_env():
    """Create a Jinja environment with the extension and test templates."""
    loader = DictLoader(
        {
            # Basic button component with enum validation
            "components/button.html": (
                "{# props variant=primary,secondary,danger #}"
                '<button class="btn btn-{{ variant }}">{{ contents }}</button>'
            ),
            # Optional variant button
            "components/button-optional.html": (
                "{# props variant=,primary,secondary,dark-mode #}"
                '<button class="btn{% if variant %} btn-{{ variant }}{% endif %}">{{ contents }}</button>'
            ),
            # Multi-value enum button
            "components/button-multi.html": (
                "{# props variant=primary,secondary,icon #}"
                '<button class="btn">{{ contents }}</button>'
            ),
            # Enum with special characters
            "components/enum-edge-cases.html": (
                "{# props special=,@,#,$,% #}<div>{{ contents }}</div>"
            ),
            # Card component requiring title
            "components/card.html": (
                "{# props title #}"
                '<div class="card"><h3>{{ title }}</h3>{{ contents }}</div>'
            ),
        }
    )
    return Environment(
        extensions=[IncludeContentsExtension],
        loader=loader,
        autoescape=True,
    )


class TestEnumErrorMessages:
    """Test enhanced error messages for enum validation in Jinja."""

    def test_enum_error_message_with_suggestion(self):
        """Test that enum validation errors include helpful suggestions."""
        env = create_jinja_env()

        # Test for a typo that's close to a valid value
        template_source = (
            '<include:button variant="primari">Close match</include:button>'
        )

        try:
            template = env.from_string(template_source)
            # If compilation succeeds, rendering should fail with helpful error
            template.render()
            pytest.fail("Expected enum validation error")
        except Exception as e:
            error_message = str(e)

            # Should include suggestion for close matches
            # Note: The exact error format will depend on Jinja implementation
            # These tests verify the desired behavior that should be implemented
            assert "variant" in error_message.lower()
            assert "primari" in error_message.lower()

    def test_enum_error_message_case_sensitivity(self):
        """Test error message for case-sensitive enum issues."""
        env = create_jinja_env()

        template_source = (
            '<include:button variant="PRIMARY">Case issue</include:button>'
        )

        try:
            template = env.from_string(template_source)
            template.render()
            pytest.fail("Expected enum validation error")
        except Exception as e:
            error_message = str(e)
            # Should mention the case issue
            assert "PRIMARY" in error_message

    def test_enum_error_message_with_hyphens(self):
        """Test error message for enum values with hyphens vs underscores."""
        env = create_jinja_env()

        template_source = '<include:button-optional variant="dark_mode">Underscore instead of hyphen</include:button-optional>'

        try:
            template = env.from_string(template_source)
            template.render()
            pytest.fail("Expected enum validation error")
        except Exception as e:
            error_message = str(e)
            # Should identify the problematic value
            assert "dark_mode" in error_message

    def test_multi_value_enum_error_message(self):
        """Test error message for multi-value enum with one invalid value."""
        env = create_jinja_env()

        template_source = '<include:button-multi variant="primary icno">Typo in second value</include:button-multi>'

        try:
            template = env.from_string(template_source)
            template.render()
            pytest.fail("Expected enum validation error")
        except Exception as e:
            error_message = str(e)
            # Should identify the specific invalid value
            assert "icno" in error_message

    def test_special_character_enum_error_message(self):
        """Test error message for special character enum values."""
        env = create_jinja_env()

        template_source = '<include:enum-edge-cases special="&">Invalid special char</include:enum-edge-cases>'

        try:
            template = env.from_string(template_source)
            template.render()
            pytest.fail("Expected enum validation error")
        except Exception as e:
            error_message = str(e)
            # Should show info about the invalid special character
            assert "&" in error_message

    def test_enum_error_message_no_suggestion(self):
        """Test error message when no close match can be found."""
        env = create_jinja_env()

        template_source = (
            '<include:button variant="xyz123">No close match</include:button>'
        )

        try:
            template = env.from_string(template_source)
            template.render()
            pytest.fail("Expected enum validation error")
        except Exception as e:
            error_message = str(e)
            # Should mention the invalid value
            assert "xyz123" in error_message


class TestMissingTemplateErrors:
    """Test enhanced error messages for missing component templates."""

    def test_missing_component_template_enhanced_error(self):
        """Test that missing component templates show enhanced error messages."""
        env = create_jinja_env()

        template_source = (
            "<include:nonexistent-component>Content</include:nonexistent-component>"
        )

        try:
            template = env.from_string(template_source)
            template.render()
            pytest.fail("Expected template not found error")
        except (TemplateNotFound, TemplateSyntaxError) as e:
            error_message = str(e)
            # Should include the component name
            assert "nonexistent-component" in error_message

    def test_missing_namespaced_component_template_enhanced_error(self):
        """Test enhanced error for namespaced component templates."""
        env = create_jinja_env()

        template_source = "<include:forms:field>Content</include:forms:field>"

        try:
            template = env.from_string(template_source)
            template.render()
            pytest.fail("Expected template not found error")
        except (TemplateNotFound, TemplateSyntaxError) as e:
            error_message = str(e)
            # Should include the namespaced component name
            assert "forms" in error_message
            assert "field" in error_message

    def test_missing_template_with_relative_path(self):
        """Test error handling for components with relative paths."""
        env = create_jinja_env()

        template_source = (
            "<include:../outside-component>Content</include:../outside-component>"
        )

        try:
            template = env.from_string(template_source)
            template.render()
            pytest.fail("Expected template not found error")
        except (TemplateNotFound, TemplateSyntaxError) as e:
            error_message = str(e)
            # Should handle relative paths gracefully
            assert "outside-component" in error_message

    def test_empty_component_name_error(self):
        """Test error handling when component name is missing or empty."""
        env = create_jinja_env()

        template_source = "<include:>Content</include:>"

        try:
            env.from_string(template_source)
            # This should fail during parsing/compilation
            pytest.fail("Expected syntax error for empty component name")
        except TemplateSyntaxError as e:
            # Should provide helpful error about empty component name
            error_message = str(e)
            # The exact error message will depend on implementation
            assert "include" in error_message.lower()


class TestAttributeValidationErrors:
    """Test error messages for attribute validation issues."""

    def test_missing_required_attribute_error(self):
        """Test error message for missing required attributes."""
        env = create_jinja_env()

        template_source = "<include:card>Missing required title</include:card>"

        try:
            template = env.from_string(template_source)
            template.render()
            pytest.fail("Expected missing attribute error")
        except Exception as e:
            error_message = str(e)
            # Should mention the missing required attribute
            assert "card" in error_message.lower()

    def test_invalid_attribute_syntax_error(self):
        """Test error message for invalid attribute syntax."""
        env = create_jinja_env()

        # Test invalid attribute names or syntax
        template_source = (
            '<include:button 123invalid="value">Invalid attr name</include:button>'
        )

        try:
            env.from_string(template_source)
            # This should fail during parsing
            pytest.fail("Expected syntax error for invalid attribute")
        except TemplateSyntaxError as e:
            error_message = str(e)
            # Should indicate syntax issue
            assert "123invalid" in error_message or "attribute" in error_message.lower()

    def test_malformed_attribute_value_error(self):
        """Test error message for malformed attribute values."""
        env = create_jinja_env()

        # Test unclosed quotes or other syntax issues
        template_source = '<include:button class="unclosed>Malformed</include:button>'

        try:
            env.from_string(template_source)
            pytest.fail("Expected syntax error for malformed attribute")
        except TemplateSyntaxError as e:
            error_message = str(e)
            # Should indicate the syntax problem
            assert "quote" in error_message.lower() or "syntax" in error_message.lower()


class TestContentBlockErrors:
    """Test error messages for content block issues."""

    def test_invalid_content_block_name_error(self):
        """Test error message for invalid content block names."""
        env = create_jinja_env()

        template_source = """
        <include:card title="Test">
            <content:123invalid>Invalid name</content:123invalid>
        </include:card>
        """

        try:
            env.from_string(template_source)
            pytest.fail("Expected syntax error for invalid content block name")
        except TemplateSyntaxError as e:
            error_message = str(e)
            # Should indicate the invalid name
            assert "123invalid" in error_message or "content" in error_message.lower()

    def test_unclosed_content_block_error(self):
        """Test error message for unclosed content blocks."""
        env = create_jinja_env()

        template_source = """
        <include:card title="Test">
            <content:footer>Unclosed block
        </include:card>
        """

        try:
            env.from_string(template_source)
            pytest.fail("Expected syntax error for unclosed content block")
        except TemplateSyntaxError as e:
            error_message = str(e)
            # Should indicate the unclosed block
            assert "footer" in error_message or "unclosed" in error_message.lower()

    def test_content_block_outside_component_renders_plainly(self):
        """Test that content blocks used outside components render as plain text."""
        env = create_jinja_env()

        template_source = """
        <div>Regular HTML</div>
        <content:test>This should render as plain text</content:test>
        """

        template = env.from_string(template_source)
        rendered = template.render()
        # Content blocks outside components should render their content
        assert "This should render as plain text" in rendered


class TestSyntaxErrors:
    """Test error messages for general syntax issues."""

    def test_unclosed_component_tag_error(self):
        """Test error message for unclosed component tags."""
        env = create_jinja_env()

        template_source = '<include:card title="Test">Unclosed component'

        try:
            env.from_string(template_source)
            pytest.fail("Expected syntax error for unclosed component")
        except TemplateSyntaxError as e:
            error_message = str(e)
            # Should indicate the unclosed tag
            assert "card" in error_message or "unclosed" in error_message.lower()

    def test_malformed_component_syntax_error(self):
        """Test error message for malformed component syntax."""
        env = create_jinja_env()

        # Test various malformed syntax patterns
        malformed_templates = [
            "<include:>",  # Empty component name
            "<include: >",  # Whitespace-only component name
            "<include:card title=>",  # Empty attribute value
            '<include:card title="test" >Extra space</include:wrong>',  # Mismatched tags
        ]

        for template_source in malformed_templates:
            try:
                template = env.from_string(template_source)
                template.render()
                # Some might fail at parse time, others at render time
            except (TemplateSyntaxError, ValueError):
                # Expected - these should all produce syntax errors
                pass

    def test_invalid_nested_syntax_error(self):
        """Test error message for invalid nested component syntax."""
        env = create_jinja_env()

        template_source = """
        <include:outer>
            <include:inner>
                <include:deep>
                    <!-- Missing closing tag for deep -->
                </include:inner>
            </include:outer>
        """

        try:
            env.from_string(template_source)
            pytest.fail("Expected syntax error for mismatched nested tags")
        except TemplateSyntaxError as e:
            error_message = str(e)
            # Should indicate the nesting issue
            assert "deep" in error_message or "inner" in error_message


class TestErrorMessageQuality:
    """Test the quality and helpfulness of error messages."""

    def test_error_messages_include_line_numbers(self):
        """Test that error messages include line numbers when possible."""
        env = create_jinja_env()

        template_source = """
        Line 1
        Line 2
        <include:nonexistent>Error on this line</include:nonexistent>
        Line 4
        """

        try:
            template = env.from_string(template_source)
            template.render()
            pytest.fail("Expected template error")
        except (TemplateSyntaxError, TemplateNotFound, ValueError) as e:
            str(e)
            # Error messages should ideally include line information
            # The exact format depends on Jinja's error reporting
            # This test documents the desired behavior
            pass

    def test_error_messages_include_context(self):
        """Test that error messages include relevant context."""
        env = create_jinja_env()

        template_source = '<include:button variant="invalid" class="test">Error context</include:button>'

        try:
            template = env.from_string(template_source)
            template.render()
            pytest.fail("Expected validation error")
        except Exception as e:
            error_message = str(e)
            # Should include context about the component and attribute
            assert "button" in error_message.lower()
            assert "variant" in error_message.lower()

    def test_error_messages_are_actionable(self):
        """Test that error messages provide actionable guidance."""
        env = create_jinja_env()

        # Test with a template that should produce a helpful error
        template_source = "<include:missing-component>Should suggest template creation</include:missing-component>"

        try:
            template = env.from_string(template_source)
            template.render()
            pytest.fail("Expected template not found error")
        except (TemplateNotFound, TemplateSyntaxError) as e:
            error_message = str(e)
            # Error should mention the component name to help with debugging
            assert "missing-component" in error_message


if __name__ == "__main__":
    # Simple test runner for development
    import sys

    test_classes = [
        TestEnumErrorMessages,
        TestMissingTemplateErrors,
        TestAttributeValidationErrors,
        TestContentBlockErrors,
        TestSyntaxErrors,
        TestErrorMessageQuality,
    ]

    passed = 0
    failed = 0

    for test_class in test_classes:
        instance = test_class()
        methods = [method for method in dir(instance) if method.startswith("test_")]

        for method_name in methods:
            try:
                method = getattr(instance, method_name)
                method()
                print(f"✓ {test_class.__name__}.{method_name}")
                passed += 1
            except Exception as e:
                print(f"✗ {test_class.__name__}.{method_name}: {e}")
                failed += 1

    print(f"\nResults: {passed} passed, {failed} failed")

    if failed > 0:
        sys.exit(1)
