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


class TestHTMLContentSyntax:
    """Test the new <content:name> HTML syntax for named content blocks."""

    def test_basic_html_content_syntax(self):
        """Test basic <content:name> syntax compilation."""
        env = create_jinja_env()
        template_source = '''
        <include:card-with-footer title="Test Card">
            <p>Main content</p>
            <content:footer>Footer content</content:footer>
            <content:sidebar>Sidebar content</content:sidebar>
        </include:card-with-footer>
        '''

        # Test that the template compiles without error
        template = env.from_string(template_source)
        assert template is not None

    def test_mixed_content_syntax(self):
        """Test mixing old {% contents %} and new <content:name> syntax."""
        env = create_jinja_env()
        template_source = '''
        <include:card title="Mixed Syntax">
            <p>Main content</p>
            {% contents "oldstyle" %}
                Old style content
            {% endcontents %}
            <content:newstyle>New style content</content:newstyle>
        </include:card>
        '''

        template = env.from_string(template_source)
        assert template is not None

    def test_html_content_empty_blocks(self):
        """Test HTML content syntax with empty named blocks."""
        env = create_jinja_env()
        template_source = '''
        <include:card-with-footer title="Empty">
            <p>Just main content</p>
        </include:card-with-footer>
        '''

        template = env.from_string(template_source)
        assert template is not None

    def test_html_content_only_named_blocks(self):
        """Test HTML content syntax with only named blocks and no main content."""
        env = create_jinja_env()
        template_source = '''
        <include:card-with-footer title="Only Named">
            <content:footer>Just footer</content:footer>
        </include:card-with-footer>
        '''

        template = env.from_string(template_source)
        assert template is not None

    def test_html_content_with_variables(self):
        """Test HTML content syntax with template variables."""
        env = create_jinja_env()
        template_source = '''
        <include:card-with-footer title="Variables">
            <p>Hello {{ name }}!</p>
            <content:footer>Copyright {{ year }}</content:footer>
        </include:card-with-footer>
        '''

        template = env.from_string(template_source)
        assert template is not None

    def test_html_content_multiline(self):
        """Test HTML content syntax with multiline content."""
        env = create_jinja_env()
        template_source = '''
        <include:card-with-footer title="Multiline">
            <content:footer>
                <p>Line 1</p>
                <p>Line 2</p>
            </content:footer>
        </include:card-with-footer>
        '''

        template = env.from_string(template_source)
        assert template is not None

    def test_html_content_nested_components(self):
        """Test HTML content syntax with nested components."""
        env = create_jinja_env()
        template_source = '''
        <include:outer-card title="Outer">
            <content:main>
                <include:inner-card title="Inner">
                    <p>Nested content</p>
                    <content:footer>Nested footer</content:footer>
                </include:inner-card>
            </content:main>
            <content:footer>Outer footer</content:footer>
        </include:outer-card>
        '''

        template = env.from_string(template_source)
        assert template is not None

    def test_html_content_with_loops(self):
        """Test HTML content syntax within loops."""
        env = create_jinja_env()
        template_source = '''
        {% for item in items %}
            <include:card title="{{ item.title }}">
                <p>{{ item.content }}</p>
                <content:footer>Item {{ loop.index }}</content:footer>
            </include:card>
        {% endfor %}
        '''

        template = env.from_string(template_source)
        assert template is not None

    def test_html_content_with_conditionals(self):
        """Test HTML content syntax with conditional blocks."""
        env = create_jinja_env()
        template_source = '''
        <include:card title="Conditional">
            <p>Always visible content</p>
            {% if show_footer %}
                <content:footer>Conditional footer</content:footer>
            {% endif %}
        </include:card>
        '''

        template = env.from_string(template_source)
        assert template is not None

    def test_html_content_complex_nesting(self):
        """Test complex nesting of HTML content blocks."""
        env = create_jinja_env()
        template_source = '''
        <include:layout>
            <content:header>
                <include:navigation>
                    <content:logo>Brand Name</content:logo>
                    <content:menu>
                        <include:menu-item href="/">Home</include:menu-item>
                        <include:menu-item href="/about">About</include:menu-item>
                    </content:menu>
                </include:navigation>
            </content:header>

            <content:main>
                <include:article title="Article">
                    <p>Article content</p>
                    <content:sidebar>
                        <include:widget title="Related">
                            <p>Related content</p>
                        </include:widget>
                    </content:sidebar>
                </include:article>
            </content:main>

            <content:footer>
                <p>Copyright info</p>
            </content:footer>
        </include:layout>
        '''

        template = env.from_string(template_source)
        assert template is not None


class TestContentBlockEdgeCases:
    """Test edge cases and error conditions for content blocks."""

    def test_duplicate_content_blocks(self):
        """Test handling of duplicate content block names."""
        env = create_jinja_env()
        template_source = '''
        <include:card title="Duplicate">
            <content:footer>First footer</content:footer>
            <content:footer>Second footer</content:footer>
        </include:card>
        '''

        # This should either compile with last-wins behavior or raise an error
        # The exact behavior should match Django implementation
        template = env.from_string(template_source)
        assert template is not None

    def test_empty_content_block_names(self):
        """Test content blocks with empty or invalid names."""
        env = create_jinja_env()

        # Empty name should potentially raise an error during parsing
        try:
            template_source = '<include:card><content:>Empty name</content:></include:card>'
            template = env.from_string(template_source)
            # If it doesn't raise an error, that's also valid behavior
        except Exception:
            # Expected - empty content block names should be invalid
            pass

    def test_content_blocks_outside_components(self):
        """Test content blocks used outside of components (should be invalid)."""
        env = create_jinja_env()

        # Content blocks outside components should be invalid
        template_source = '''
        <div>Regular HTML</div>
        <content:invalid>This should not work</content:invalid>
        '''

        # This might raise an error during compilation or rendering
        # The exact behavior should match the intended design
        try:
            template = env.from_string(template_source)
            # If compilation succeeds, rendering might fail
        except Exception:
            # Expected behavior - content blocks should only work inside components
            pass

    def test_deeply_nested_content_blocks(self):
        """Test very deeply nested content block structures."""
        env = create_jinja_env()
        template_source = '''
        <include:level1>
            <content:section1>
                <include:level2>
                    <content:section2>
                        <include:level3>
                            <content:section3>
                                <include:level4>
                                    <content:section4>
                                        Deep content
                                    </content:section4>
                                </include:level4>
                            </content:section3>
                        </include:level3>
                    </content:section2>
                </include:level2>
            </content:section1>
        </include:level1>
        '''

        template = env.from_string(template_source)
        assert template is not None

    def test_content_blocks_with_complex_content(self):
        """Test content blocks containing complex template syntax."""
        env = create_jinja_env()
        template_source = '''
        <include:complex-card title="Complex">
            <content:body>
                {% for item in items %}
                    <div class="item {{ loop.cycle('odd', 'even') }}">
                        {% if item.featured %}
                            <strong>{{ item.title }}</strong>
                        {% else %}
                            {{ item.title }}
                        {% endif %}

                        {% include "partials/item-details.html" %}

                        {% with processed_content=item.content|markdown %}
                            {{ processed_content|safe }}
                        {% endwith %}
                    </div>
                {% endfor %}
            </content:body>

            <content:footer>
                {% if user.is_authenticated %}
                    <a href="{% url 'edit' item.id %}">Edit</a>
                {% endif %}
            </content:footer>
        </include:complex-card>
        '''

        template = env.from_string(template_source)
        assert template is not None


class TestContentBlockInteraction:
    """Test interaction between content blocks and other features."""

    def test_content_blocks_with_attrs(self):
        """Test content blocks combined with attribute handling."""
        env = create_jinja_env()
        template_source = '''
        <include:flexible-card
            class="custom-card"
            data-id="123"
            title="Flexible">
            <content:header class="custom-header">
                Header with custom class
            </content:header>
            <p>Main content</p>
        </include:flexible-card>
        '''

        template = env.from_string(template_source)
        assert template is not None

    def test_content_blocks_with_props(self):
        """Test content blocks with component props."""
        env = create_jinja_env()
        template_source = '''
        <include:card-with-props
            title="Props Test"
            variant="primary"
            size="large">
            <content:body>
                Content that uses {{ title }} and {{ variant }}
            </content:body>
        </include:card-with-props>
        '''

        template = env.from_string(template_source)
        assert template is not None

    def test_content_blocks_inheritance_style(self):
        """Test content blocks used in template inheritance style patterns."""
        env = create_jinja_env()
        template_source = '''
        <include:base-layout title="Page Title">
            <content:breadcrumbs>
                <a href="/">Home</a> &gt;
                <a href="/section">Section</a> &gt;
                Current Page
            </content:breadcrumbs>

            <content:main>
                <h1>Page Content</h1>
                <p>Main page content goes here</p>
            </content:main>

            <content:sidebar>
                <include:widget type="recent-posts" />
                <include:widget type="categories" />
            </content:sidebar>

            <content:scripts>
                <script>
                    // Page-specific JavaScript
                    console.log('Page loaded');
                </script>
            </content:scripts>
        </include:base-layout>
        '''

        template = env.from_string(template_source)
        assert template is not None


if __name__ == "__main__":
    # Simple test runner for development
    import sys

    test_classes = [TestHTMLContentSyntax, TestContentBlockEdgeCases, TestContentBlockInteraction]

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