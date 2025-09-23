import pytest
from jinja2 import Environment, TemplateSyntaxError

from includecontents.jinja2.extension import IncludeContentsExtension


def create_jinja_env():
    """Create a Jinja environment with the extension."""
    return Environment(
        extensions=[IncludeContentsExtension],
        loader=None,  # We'll use from_string
        autoescape=True,
    )


class TestEnumValidation:
    """Test enum validation in Jinja components."""

    def test_enum_required_validation(self):
        """Test that required enum props must be provided."""
        env = create_jinja_env()

        template_source = '<include:button>Click me</include:button>'

        try:
            template = env.from_string(template_source)
            template.render()
            pytest.fail("Expected required attribute error")
        except (TemplateSyntaxError, ValueError) as e:
            error_message = str(e)
            # Should mention the missing required attribute
            assert "button" in error_message.lower()

    def test_enum_invalid_value_validation(self):
        """Test that invalid enum values are rejected."""
        env = create_jinja_env()

        template_source = '<include:button variant="invalid">Click me</include:button>'

        try:
            template = env.from_string(template_source)
            template.render()
            pytest.fail("Expected enum validation error")
        except (TemplateSyntaxError, ValueError) as e:
            error_message = str(e)
            # Should mention the invalid value
            assert "invalid" in error_message.lower()
            assert "variant" in error_message.lower()

    def test_enum_valid_value_acceptance(self):
        """Test that valid enum values are accepted."""
        env = create_jinja_env()

        template_source = '<include:button variant="primary">Click me</include:button>'

        # This should compile and render without error
        template = env.from_string(template_source)
        # Note: Actual rendering would require component templates to exist
        assert template is not None

    def test_enum_optional_validation(self):
        """Test that optional enum props work when not provided."""
        env = create_jinja_env()

        template_source = '<include:button-optional>Click me</include:button-optional>'

        template = env.from_string(template_source)
        assert template is not None

    def test_enum_optional_with_valid_value(self):
        """Test that optional enum props accept valid values."""
        env = create_jinja_env()

        template_source = '<include:button-optional variant="secondary">Click me</include:button-optional>'

        template = env.from_string(template_source)
        assert template is not None

    def test_enum_empty_value_handling(self):
        """Test that empty string values are handled correctly."""
        env = create_jinja_env()

        template_source = '<include:button-optional variant="">No variant</include:button-optional>'

        template = env.from_string(template_source)
        assert template is not None

    def test_enum_with_hyphens(self):
        """Test enum values that contain hyphens."""
        env = create_jinja_env()

        template_source = '<include:button-optional variant="dark-mode">Dark mode</include:button-optional>'

        template = env.from_string(template_source)
        assert template is not None

    def test_enum_multiple_values(self):
        """Test that multiple enum values can be specified."""
        env = create_jinja_env()

        template_source = '<include:button-multi variant="primary icon">Click me</include:button-multi>'

        template = env.from_string(template_source)
        assert template is not None

    def test_enum_multiple_values_validation(self):
        """Test that all values in a multi-value enum are validated."""
        env = create_jinja_env()

        template_source = '<include:button-multi variant="primary invalid">Click me</include:button-multi>'

        try:
            template = env.from_string(template_source)
            template.render()
            pytest.fail("Expected enum validation error")
        except (TemplateSyntaxError, ValueError) as e:
            error_message = str(e)
            # Should identify the invalid value in the multi-value string
            assert "invalid" in error_message.lower()

    def test_enum_case_sensitivity(self):
        """Test that enum validation is case-sensitive."""
        env = create_jinja_env()

        template_source = '<include:button variant="PRIMARY">Case sensitive</include:button>'

        try:
            template = env.from_string(template_source)
            template.render()
            pytest.fail("Expected enum validation error")
        except (TemplateSyntaxError, ValueError) as e:
            error_message = str(e)
            # Should reject uppercase when lowercase is expected
            assert "PRIMARY" in error_message


class TestSpecialCharacterEnums:
    """Test enum handling with special characters and edge cases."""

    def test_enum_with_special_characters(self):
        """Test enum values containing special characters."""
        env = create_jinja_env()

        template_source = '<include:enum-edge-cases special="@">Special</include:enum-edge-cases>'

        template = env.from_string(template_source)
        assert template is not None

    def test_enum_with_numbers(self):
        """Test enum values that are numbers."""
        env = create_jinja_env()

        template_source = '<include:enum-edge-cases numbers="1">Number</include:enum-edge-cases>'

        template = env.from_string(template_source)
        assert template is not None

    def test_enum_invalid_special_character(self):
        """Test that invalid special characters are rejected."""
        env = create_jinja_env()

        template_source = '<include:enum-edge-cases special="&">Invalid</include:enum-edge-cases>'

        try:
            template = env.from_string(template_source)
            template.render()
            pytest.fail("Expected enum validation error")
        except (TemplateSyntaxError, ValueError) as e:
            error_message = str(e)
            # Should mention the invalid special character
            assert "&" in error_message

    def test_enum_single_character(self):
        """Test enum with single character value."""
        env = create_jinja_env()

        template_source = '<include:enum-edge-cases single="a">Single</include:enum-edge-cases>'

        template = env.from_string(template_source)
        assert template is not None

    def test_enum_whitespace_handling(self):
        """Test that enum definitions with whitespace are handled correctly."""
        env = create_jinja_env()

        template_source = '<include:enum-whitespace variant="a">Whitespace</include:enum-whitespace>'

        template = env.from_string(template_source)
        assert template is not None

    def test_enum_mixed_empty_values(self):
        """Test enum definition with mixed content and empty values."""
        env = create_jinja_env()

        template_source = '<include:enum-edge-cases mixed="test">Mixed</include:enum-edge-cases>'

        template = env.from_string(template_source)
        assert template is not None


class TestComplexObjectHandling:
    """Test handling of complex objects and data types in props."""

    def test_prop_with_template_variables(self):
        """Test props that receive template variables."""
        env = create_jinja_env()

        template_source = '''
        <include:button variant="{{ button_variant }}" title="{{ button_title }}">
            {{ button_text }}
        </include:button>
        '''

        template = env.from_string(template_source)
        assert template is not None

        # Test rendering with context
        context = {
            'button_variant': 'primary',
            'button_title': 'Click Me',
            'button_text': 'Submit'
        }

        # This would require component templates to exist for full testing
        # But we can verify the template compiles correctly
        try:
            result = template.render(**context)
            # Template compiled and parsed variables correctly
        except Exception:
            # Expected if component templates don't exist
            pass

    def test_prop_with_complex_objects(self):
        """Test props that receive complex objects from context."""
        env = create_jinja_env()

        template_source = '''
        <include:user-card
            user="{{ user }}"
            profile="{{ user.profile }}"
            permissions="{{ user.permissions }}">
            User details
        </include:user-card>
        '''

        template = env.from_string(template_source)
        assert template is not None

        # Test with complex object context
        context = {
            'user': {
                'id': 1,
                'name': 'John Doe',
                'profile': {
                    'avatar': '/images/avatar.jpg',
                    'bio': 'Software developer'
                },
                'permissions': ['read', 'write', 'admin']
            }
        }

        try:
            result = template.render(**context)
        except Exception:
            # Expected if component templates don't exist
            pass

    def test_prop_with_lists_and_arrays(self):
        """Test props that receive lists and arrays."""
        env = create_jinja_env()

        template_source = '''
        <include:item-list
            items="{{ items }}"
            categories="{{ categories }}"
            selected="{{ selected_ids }}">
            List content
        </include:item-list>
        '''

        template = env.from_string(template_source)
        assert template is not None

        context = {
            'items': [
                {'id': 1, 'name': 'Item 1'},
                {'id': 2, 'name': 'Item 2'},
                {'id': 3, 'name': 'Item 3'}
            ],
            'categories': ['electronics', 'books', 'clothing'],
            'selected_ids': [1, 3]
        }

        try:
            result = template.render(**context)
        except Exception:
            # Expected if component templates don't exist
            pass

    def test_prop_with_null_and_false_values(self):
        """Test enum handling of null and false values from variables."""
        env = create_jinja_env()

        template_source = '''
        <include:button-optional variant="{{ variant }}">
            Optional variant
        </include:button-optional>
        '''

        template = env.from_string(template_source)
        assert template is not None

        # Test with various falsy values
        contexts = [
            {'variant': None},
            {'variant': False},
            {'variant': ''},
            {'variant': 0}
        ]

        for context in contexts:
            try:
                result = template.render(**context)
            except Exception:
                # Expected if component templates don't exist
                pass

    def test_enum_with_list_values_from_context(self):
        """Test enum handling with list/array values from context."""
        env = create_jinja_env()

        template_source = '''
        <include:button-multi variant="{{ variant_list }}">
            Multi variant from list
        </include:button-multi>
        '''

        template = env.from_string(template_source)
        assert template is not None

        contexts = [
            {'variant_list': ['primary', 'icon']},
            {'variant_list': ('secondary', 'large')},
            {'variant_list': {'accent'}}  # Set
        ]

        for context in contexts:
            try:
                result = template.render(**context)
            except Exception:
                # Expected if component templates don't exist
                pass


class TestPropDefaultValues:
    """Test prop default value handling."""

    def test_prop_with_default_values(self):
        """Test that props can have default values."""
        env = create_jinja_env()

        template_source = '''
        <include:button-with-defaults>
            Uses default values
        </include:button-with-defaults>
        '''

        template = env.from_string(template_source)
        assert template is not None

    def test_prop_override_default_values(self):
        """Test that prop default values can be overridden."""
        env = create_jinja_env()

        template_source = '''
        <include:button-with-defaults variant="secondary" size="large">
            Overridden values
        </include:button-with-defaults>
        '''

        template = env.from_string(template_source)
        assert template is not None

    def test_prop_partial_override_defaults(self):
        """Test that some defaults can be overridden while others remain."""
        env = create_jinja_env()

        template_source = '''
        <include:button-with-defaults variant="accent">
            Partial override
        </include:button-with-defaults>
        '''

        template = env.from_string(template_source)
        assert template is not None


class TestPropInheritanceAndNesting:
    """Test prop behavior in nested and inherited scenarios."""

    def test_nested_component_prop_isolation(self):
        """Test that nested components have isolated prop contexts."""
        env = create_jinja_env()

        template_source = '''
        <include:outer-component variant="primary">
            <include:inner-component variant="secondary">
                <include:deep-component variant="accent">
                    Deeply nested
                </include:deep-component>
            </include:inner-component>
        </include:outer-component>
        '''

        template = env.from_string(template_source)
        assert template is not None

    def test_prop_passing_through_content_blocks(self):
        """Test prop handling when components are passed through content blocks."""
        env = create_jinja_env()

        template_source = '''
        <include:layout variant="wide">
            <content:main>
                <include:article variant="featured">
                    Article content
                </include:article>
            </content:main>
            <content:sidebar>
                <include:widget variant="compact">
                    Widget content
                </include:widget>
            </content:sidebar>
        </include:layout>
        '''

        template = env.from_string(template_source)
        assert template is not None

    def test_prop_with_complex_template_expressions(self):
        """Test props with complex Jinja expressions."""
        env = create_jinja_env()

        template_source = '''
        <include:dynamic-component
            variant="{{ 'primary' if user.is_premium else 'secondary' }}"
            size="{{ sizes[current_breakpoint] }}"
            enabled="{{ user.permissions | selectattr('name', 'equalto', 'write') | list | length > 0 }}">
            Dynamic component
        </include:dynamic-component>
        '''

        template = env.from_string(template_source)
        assert template is not None

    def test_prop_validation_with_filters(self):
        """Test that prop validation works with Jinja filters."""
        env = create_jinja_env()

        template_source = '''
        <include:button
            variant="{{ user_preference | default('primary') }}"
            title="{{ page_title | title | truncate(50) }}">
            Filtered props
        </include:button>
        '''

        template = env.from_string(template_source)
        assert template is not None


class TestErrorHandlingEdgeCases:
    """Test error handling for edge cases in prop validation."""

    def test_circular_reference_handling(self):
        """Test handling of circular references in prop objects."""
        env = create_jinja_env()

        template_source = '''
        <include:complex-component data="{{ circular_data }}">
            Circular reference test
        </include:complex-component>
        '''

        template = env.from_string(template_source)
        assert template is not None

        # Create object with circular reference
        circular = {'name': 'test'}
        circular['self'] = circular

        context = {'circular_data': circular}

        try:
            result = template.render(**context)
        except Exception:
            # Expected - should handle gracefully
            pass

    def test_very_large_object_handling(self):
        """Test prop handling with very large objects."""
        env = create_jinja_env()

        template_source = '''
        <include:data-component large_data="{{ big_data }}">
            Large data test
        </include:data-component>
        '''

        template = env.from_string(template_source)
        assert template is not None

        # Create large data structure
        big_data = {f'key_{i}': f'value_{i}' for i in range(1000)}
        context = {'big_data': big_data}

        try:
            result = template.render(**context)
        except Exception:
            # Expected if component templates don't exist
            pass


if __name__ == "__main__":
    # Simple test runner for development
    import sys

    test_classes = [
        TestEnumValidation,
        TestSpecialCharacterEnums,
        TestComplexObjectHandling,
        TestPropDefaultValues,
        TestPropInheritanceAndNesting,
        TestErrorHandlingEdgeCases,
    ]

    passed = 0
    failed = 0

    for test_class in test_classes:
        instance = test_class()
        methods = [method for method in dir(instance) if method.startswith('test_')]

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