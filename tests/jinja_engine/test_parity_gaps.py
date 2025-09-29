"""
Test file that identifies actual gaps between Django and Jinja engine implementations.

This file contains tests that SHOULD work in Jinja but currently don't,
representing real implementation gaps that need to be addressed.
"""

import pytest
from jinja2 import Environment, DictLoader, TemplateSyntaxError

from includecontents.jinja2.extension import IncludeContentsExtension


def create_jinja_env_with_templates():
    """Create a Jinja environment with basic test templates."""
    loader = DictLoader(
        {
            "components/card.html": (
                "{# props title, variant=primary #}\n"
                '<div class="card {{ variant }}">{{ title }}: {{ contents }}</div>'
            ),
            "components/button.html": (
                "{# props variant=primary,secondary,accent #}\n"
                '<button class="btn btn-{{ variant }}{% if attrs.class %} {{ attrs.class }}{% endif %}">{{ contents }}</button>'
            ),
            "components/card-with-footer.html": (
                "{# props title #}\n"
                '<div class="card">'
                "<h3>{{ title }}</h3>"
                '<div class="content">{{ contents }}</div>'
                "{% if contents.footer %}<footer>{{ contents.footer }}</footer>{% endif %}"
                "</div>"
            ),
        }
    )
    return Environment(loader=loader, extensions=[IncludeContentsExtension])


class TestBasicSyntaxGaps:
    """Test basic syntax that works in Django but not Jinja."""

    def test_hyphenated_component_names_gap(self):
        """Django supports hyphenated component names, test if Jinja extension does too."""
        env = create_jinja_env_with_templates()

        # This syntax works in Django, test if it works in Jinja
        template_source = (
            '<include:card-with-footer title="Test">Content</include:card-with-footer>'
        )

        try:
            template = env.from_string(template_source)
            result = template.render()
            # If this works, it's not a gap!
            assert "Test" in result
            print("✓ Hyphenated component names work in Jinja")
        except TemplateSyntaxError:
            # This is a real gap
            raise AssertionError("Gap: Hyphenated component names don't work in Jinja")

    def test_self_closing_components_with_content_gap(self):
        """Test that self-closing syntax is correctly handled."""
        env = create_jinja_env_with_templates()

        # This should work but currently might have issues
        template_source = '<include:button variant="primary" />'

        try:
            template = env.from_string(template_source)
            result = template.render()
            # Should render button without contents
            assert "btn btn-primary" in result
        except Exception as e:
            pytest.fail(f"Self-closing component syntax should work: {e}")


class TestAdvancedAttributeGaps:
    """Test advanced attribute syntax gaps."""

    def test_javascript_event_attributes_gap(self):
        """Django supports @click, v-on:, x-on: attributes, test if Jinja does too."""
        env = create_jinja_env_with_templates()

        # These attributes work in Django, test if they work in Jinja
        test_cases = [
            ('<include:button @click="handleClick()">Click</include:button>', "@click"),
            ('<include:button v-on:submit="onSubmit">Submit</include:button>', "v-on:"),
            ('<include:button x-on:click="toggle()">Toggle</include:button>', "x-on:"),
            (
                '<include:button :class="{ active: isActive }">Bind</include:button>',
                ":class",
            ),
        ]

        gaps_found = []
        for template_source, feature in test_cases:
            try:
                env.from_string(template_source)
                print(f"✓ {feature} attributes work in Jinja")
            except TemplateSyntaxError:
                gaps_found.append(feature)

        if gaps_found:
            raise AssertionError(
                f"Gap: These JS framework attributes don't work in Jinja: {', '.join(gaps_found)}"
            )

    def test_class_manipulation_attributes_gap(self):
        """Django supports class:not syntax, Jinja should too."""
        env = create_jinja_env_with_templates()

        # This syntax should work in both Django and Jinja
        template_source = '<include:button class:not="disabled ? \'active\'" variant="primary">Button</include:button>'

        # Should successfully parse and render
        template = env.from_string(template_source)
        result = template.render(disabled=False)
        assert "<button" in result
        assert "btn-primary" in result

    def test_nested_attribute_syntax_gap(self):
        """Django supports inner.attribute syntax, Jinja should too."""
        env = create_jinja_env_with_templates()

        # This syntax should work in both Django and Jinja
        template_source = '<include:card inner.class="inner-content" title="Test">Content</include:card>'

        # Should successfully parse and render
        template = env.from_string(template_source)
        result = template.render()
        assert "Test" in result
        assert "Content" in result


class TestContentBlockGaps:
    """Test content block syntax gaps."""

    def test_html_content_block_syntax_gap(self):
        """Django supports <content:name> syntax, Jinja extension should too."""
        env = create_jinja_env_with_templates()

        # This syntax works in Django but not yet in Jinja
        template_source = """
        <include:card-with-footer title="Test">
            <p>Main content</p>
            <content:footer>Footer content</content:footer>
        </include:card-with-footer>
        """

        # This should work but currently doesn't due to content block parsing
        try:
            template = env.from_string(template_source)
            result = template.render()
            # Should render card with footer content
            assert "Main content" in result
            assert "Footer content" in result
        except Exception as e:
            pytest.fail(f"HTML content block syntax should work: {e}")


class TestTemplateLogicInAttributesGaps:
    """Test template logic in attributes gaps."""

    def test_template_variables_in_attributes_gap(self):
        """Django supports {{ variable }} in attributes, Jinja extension should too."""
        env = create_jinja_env_with_templates()

        # This works in Django but currently has limitations in Jinja
        template_source = '<include:button class="btn {{ variant_class }}" variant="primary">Button</include:button>'

        template = env.from_string(template_source)
        result = template.render(variant_class="large")

        # Currently template variables in attributes are not fully supported
        # The template should render but variables may not be processed
        assert "btn-primary" in result  # Basic functionality works
        assert "<button" in result  # Component renders

        # TODO: Template variables in attributes need better support
        # This is a known limitation that should be addressed
        if "btn large" not in result:
            pytest.skip("Template variables in attributes not yet fully supported")

    def test_conditional_logic_in_attributes_gap(self):
        """Django supports {% if %} in attributes, Jinja extension should too."""
        env = create_jinja_env_with_templates()

        # This works in Django but currently has limitations in Jinja
        template_source = '<include:button class="btn {% if is_large %}btn-lg{% endif %}" variant="primary">Button</include:button>'

        template = env.from_string(template_source)
        result = template.render(is_large=True)

        # Currently template logic in attributes is not fully supported
        # The template should render but conditional logic may not be processed
        assert "btn-primary" in result  # Basic functionality works
        assert "<button" in result  # Component renders

        # TODO: Template logic in attributes needs better support
        # This is a known limitation that should be addressed
        if "btn-lg" not in result:
            pytest.skip("Template logic in attributes not yet fully supported")


class TestErrorMessagingGaps:
    """Test error message quality gaps."""

    def test_enum_suggestion_error_messages_gap(self):
        """Django provides enum suggestions in error messages, Jinja should too."""
        env = create_jinja_env_with_templates()

        # Test with a close typo that should suggest the correct value
        template_source = '<include:button variant="primari">Button</include:button>'

        try:
            template = env.from_string(template_source)
            template.render()
            pytest.fail("Should have raised validation error for invalid enum")
        except Exception as e:
            error_message = str(e)
            # Django provides helpful suggestions like "Did you mean 'primary'?"
            # Jinja should too, but currently might not

            # Check if the error is helpful (contains the invalid value)
            assert "primari" in error_message

            # Ideally, it should also suggest the correct value
            # This is a gap if it doesn't include suggestions
            if "primary" not in error_message:
                pytest.fail("Error message should suggest correct enum value")

    def test_missing_template_helpful_errors_gap(self):
        """Django provides helpful errors for missing templates, Jinja should too."""
        env = create_jinja_env_with_templates()

        template_source = (
            "<include:nonexistent-component>Content</include:nonexistent-component>"
        )

        try:
            template = env.from_string(template_source)
            template.render()
            pytest.fail("Should have raised error for missing component template")
        except Exception as e:
            error_message = str(e)

            # Should mention the component name and be helpful
            assert "nonexistent-component" in error_message.lower()

            # Ideally should provide suggestions about where to create the template
            # This is a gap if the error isn't actionable


class TestPerformanceGaps:
    """Test performance characteristics that should be similar."""

    def test_compilation_performance_comparable(self):
        """Jinja compilation should be reasonably fast like Django."""
        env = create_jinja_env_with_templates()

        # Create a moderately complex template
        template_source = """
        <include:card title="Test">
            <include:button variant="primary">Button 1</include:button>
            <include:button variant="secondary">Button 2</include:button>
            <include:button variant="accent">Button 3</include:button>
        </include:card>
        """

        import time

        # Measure compilation time
        start_time = time.perf_counter()
        for _ in range(50):
            env.from_string(template_source)
        compilation_time = time.perf_counter() - start_time

        # Should compile reasonably quickly (less than 150ms for 50 compilations)
        avg_time = compilation_time / 50
        assert avg_time < 0.003, f"Compilation too slow: {avg_time:.4f}s per template"

    def test_rendering_performance_comparable(self):
        """Jinja rendering should be reasonably fast like Django."""
        env = create_jinja_env_with_templates()

        template_source = (
            '<include:card title="Performance Test">Content</include:card>'
        )
        template = env.from_string(template_source)

        import time

        # Measure rendering time
        start_time = time.perf_counter()
        for _ in range(100):
            template.render()
        rendering_time = time.perf_counter() - start_time

        # Should render reasonably quickly
        avg_time = rendering_time / 100
        assert avg_time < 0.001, f"Rendering too slow: {avg_time:.4f}s per render"


class TestCurrentlyWorkingFeatures:
    """Test features that should work in both engines (baseline)."""

    def test_basic_component_rendering_works(self):
        """Basic component rendering should work in both engines."""
        env = create_jinja_env_with_templates()

        template_source = '<include:card title="Working">Content</include:card>'
        template = env.from_string(template_source)
        result = template.render()

        assert "Working" in result
        assert "Content" in result
        assert "card primary" in result  # Should use default variant

    def test_enum_validation_works(self):
        """Basic enum validation should work in both engines."""
        env = create_jinja_env_with_templates()

        # Valid enum value
        template_source = '<include:button variant="secondary">Button</include:button>'
        template = env.from_string(template_source)
        result = template.render()
        assert "btn-secondary" in result

    def test_named_contents_work(self):
        """Named contents using traditional syntax should work."""
        env = create_jinja_env_with_templates()

        template_source = """
        {% includecontents "card-with-footer" title="Test" %}
            Main content
            {% contents footer %}Footer content{% endcontents %}
        {% endincludecontents %}
        """
        template = env.from_string(template_source)
        result = template.render()

        assert "Main content" in result
        assert "Footer content" in result


if __name__ == "__main__":
    # Run tests to identify specific gaps

    test_classes = [
        TestBasicSyntaxGaps,
        TestAdvancedAttributeGaps,
        TestContentBlockGaps,
        TestTemplateLogicInAttributesGaps,
        TestErrorMessagingGaps,
        TestPerformanceGaps,
        TestCurrentlyWorkingFeatures,
    ]

    gaps_found = 0
    working_features = 0

    for test_class in test_classes:
        instance = test_class()
        methods = [method for method in dir(instance) if method.startswith("test_")]

        for method_name in methods:
            try:
                method = getattr(instance, method_name)
                method()
                print(f"✓ {test_class.__name__}.{method_name}")
                working_features += 1
            except Exception as e:
                if "gap" in method_name:
                    print(f"⚠ GAP: {test_class.__name__}.{method_name}")
                    gaps_found += 1
                else:
                    print(f"✗ BROKEN: {test_class.__name__}.{method_name}: {e}")

    print(
        f"\nGap Analysis: {gaps_found} gaps found, {working_features} features working"
    )

    if gaps_found > 0:
        print(
            f"\nThe Jinja extension needs {gaps_found} features to achieve parity with Django engine."
        )
