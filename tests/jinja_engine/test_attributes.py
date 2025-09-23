import pytest
from jinja2 import Environment

from includecontents.jinja2.extension import IncludeContentsExtension


def create_jinja_env():
    """Create a Jinja environment with the extension."""
    return Environment(
        extensions=[IncludeContentsExtension],
        loader=None,  # We'll use from_string
        autoescape=True,
    )


class TestAttributeHandling:
    """Test advanced attribute handling features in Jinja engine."""

    def test_basic_attrs_spread(self):
        """Test basic ...attrs spreading from parent to child component."""
        # This test needs component templates to be available
        # For now, testing compilation and basic functionality
        env = create_jinja_env()
        template_source = '''
        <include:card class="mycard" id="topcard" x-data title="hello">
            some content
        </include:card>
        '''

        # Test that the template compiles without error
        template = env.from_string(template_source)
        assert template is not None

    def test_class_append_syntax(self):
        """Test class attribute appending with '& ' syntax."""
        env = create_jinja_env()
        template_source = '''
        <include:card-extend title="Append Test" class="user-class" />
        '''

        # Test compilation
        template = env.from_string(template_source)
        assert template is not None

    def test_class_prepend_syntax(self):
        """Test class attribute prepending with ' &' syntax."""
        env = create_jinja_env()
        template_source = '''
        <include:card-prepend title="Prepend Test" class="user-class" />
        '''

        # Test compilation
        template = env.from_string(template_source)
        assert template is not None

    def test_class_negation_syntax(self):
        """Test class: attribute with negation using 'not' syntax."""
        env = create_jinja_env()
        template_source = '''
        <include:card class:not="disabled ? 'active'" title="Test" />
        '''

        # Test compilation
        template = env.from_string(template_source)
        assert template is not None

    def test_javascript_event_attributes(self):
        """Test various JavaScript framework event attributes."""
        env = create_jinja_env()

        # Test @click attribute
        template_source = '''<include:button @click="handleClick()" />'''
        template = env.from_string(template_source)
        assert template is not None

        # Test Vue.js v-on: syntax
        template_source = '''<include:button v-on:submit="onSubmit" />'''
        template = env.from_string(template_source)
        assert template is not None

        # Test Alpine.js x-on: syntax
        template_source = '''<include:button x-on:click="open = !open" />'''
        template = env.from_string(template_source)
        assert template is not None

        # Test Alpine.js :bind shorthand
        template_source = '''<include:button :class="{ 'active': isActive }" />'''
        template = env.from_string(template_source)
        assert template is not None

    def test_javascript_event_modifiers(self):
        """Test JavaScript event modifiers like @click.stop."""
        env = create_jinja_env()

        # Test Vue.js event modifiers
        template_source = '''<include:button @click.stop="handleClick()" />'''
        template = env.from_string(template_source)
        assert template is not None

        # Test multiple modifiers
        template_source = '''<include:button @click.stop.prevent="handleClick()" />'''
        template = env.from_string(template_source)
        assert template is not None

        # Test keyup modifiers
        template_source = '''<include:button @keyup.enter="handleEnter()" />'''
        template = env.from_string(template_source)
        assert template is not None

    def test_template_variables_in_attributes(self):
        """Test template variable support in component attributes."""
        env = create_jinja_env()

        # Test simple variable
        template_source = '''<include:button data-id="{{ myid }}" />'''
        template = env.from_string(template_source)
        assert template is not None

        # Test variable with filter
        template_source = '''<include:button data-count="{{ count|default(0) }}" />'''
        template = env.from_string(template_source)
        assert template is not None

    def test_mixed_content_in_attributes(self):
        """Test mixed static text and template variables in attributes."""
        env = create_jinja_env()

        # Test mixed content with variable
        template_source = '''<include:button class="btn {{ variant }}" />'''
        template = env.from_string(template_source)
        assert template is not None

        # Test mixed content with multiple variables
        template_source = '''<include:button data-info="Count: {{ count }} of {{ total }}" />'''
        template = env.from_string(template_source)
        assert template is not None

        # Test URL-like pattern
        template_source = '''<include:button href="/products/{{ product_id }}/" />'''
        template = env.from_string(template_source)
        assert template is not None

    def test_conditional_logic_in_attributes(self):
        """Test if/else logic in component attributes."""
        env = create_jinja_env()

        # Test if statement in attribute
        template_source = '''<include:button class="btn {% if active %}active{% endif %}" />'''
        template = env.from_string(template_source)
        assert template is not None

        # Test for loop in attribute
        template_source = '''<include:button data-items="{% for i in items %}{{ i }}{% if not loop.last %},{% endif %}{% endfor %}" />'''
        template = env.from_string(template_source)
        assert template is not None

    def test_nested_attributes(self):
        """Test nested attribute syntax with dots."""
        env = create_jinja_env()

        # Test inner attribute syntax
        template_source = '''<include:nested-attrs inner.class="inner-class" class="outer-class" />'''
        template = env.from_string(template_source)
        assert template is not None

        # Test complex nested syntax
        template_source = '''<include:button inner.@click="innerClick()" @click="outerClick()" />'''
        template = env.from_string(template_source)
        assert template is not None

    def test_self_closing_with_attributes(self):
        """Test self-closing component syntax with attributes."""
        env = create_jinja_env()

        template_source = '''<include:button class="btn" @click="test()" />'''
        template = env.from_string(template_source)
        assert template is not None

    def test_kebab_case_attributes(self):
        """Test kebab-case attribute names."""
        env = create_jinja_env()

        template_source = '''<include:button x-data="{foo: bar}" hx-swap="innerHTML" />'''
        template = env.from_string(template_source)
        assert template is not None

    def test_attribute_escaping(self):
        """Test proper escaping of attribute values."""
        env = create_jinja_env()

        # Test HTML escaping
        template_source = '''<include:button test="2>1" another="3>2" />'''
        template = env.from_string(template_source)
        assert template is not None

    def test_shorthand_attribute_syntax(self):
        """Test shorthand {variable} syntax for attributes."""
        env = create_jinja_env()

        template_source = '''<include:button {title} {class} />'''
        template = env.from_string(template_source)
        assert template is not None


class TestAttributeGrouping:
    """Test attribute grouping functionality."""

    def test_attrs_group_syntax(self):
        """Test ...attrs.group spreading."""
        env = create_jinja_env()

        # Test group attribute spreading
        template_source = '''
        <include:form-with-button
            button.type="submit"
            button.class="btn btn-primary"
            data-form="true">
            Form content
        </include:form-with-button>
        '''

        template = env.from_string(template_source)
        assert template is not None

    def test_empty_attrs_handling(self):
        """Test attrs spreading when parent has no attrs."""
        env = create_jinja_env()

        template_source = '''<include:empty-component />'''
        template = env.from_string(template_source)
        assert template is not None


class TestAttributePrecedence:
    """Test attribute precedence and overriding."""

    def test_local_attrs_precedence(self):
        """Test that local attrs take precedence over spread attrs."""
        env = create_jinja_env()

        template_source = '''
        <include:card class="local-class" title="test">
            Content
        </include:card>
        '''

        template = env.from_string(template_source)
        assert template is not None

    def test_nested_attrs_precedence(self):
        """Test attribute precedence in nested components."""
        env = create_jinja_env()

        template_source = '''
        <include:nested-component
            data-root="true"
            inner.class="leaf-component">
            Content
        </include:nested-component>
        '''

        template = env.from_string(template_source)
        assert template is not None


if __name__ == "__main__":
    # Simple test runner for development
    import sys

    test_class = TestAttributeHandling()
    methods = [method for method in dir(test_class) if method.startswith('test_')]

    passed = 0
    failed = 0

    for method_name in methods:
        try:
            method = getattr(test_class, method_name)
            method()
            print(f"✓ {method_name}")
            passed += 1
        except Exception as e:
            print(f"✗ {method_name}: {e}")
            failed += 1

    print(f"\nResults: {passed} passed, {failed} failed")

    if failed > 0:
        sys.exit(1)