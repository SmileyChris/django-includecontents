"""Tests for callable attrs functionality across Django and Jinja2 engines."""

from django.template import Template
from jinja2 import DictLoader, Environment

from includecontents.jinja2 import IncludeContentsExtension
from includecontents.templatetags.includecontents import Attrs as DjangoAttrs
from includecontents.jinja2.attrs import Attrs as JinjaAttrs


class TestCallableAttrsBasic:
    """Test basic callable functionality for attrs objects."""

    def test_django_attrs_callable_basic(self):
        """Test Django attrs object is callable with basic kwargs."""
        attrs = DjangoAttrs()
        attrs["existing"] = "value"

        result = attrs(**{"class": "btn", "type": "button"})

        assert result["existing"] == "value"  # Original preserved
        assert result["class"] == "btn"  # Fallback applied
        assert result["type"] == "button"  # Fallback applied

    def test_jinja_attrs_callable_basic(self):
        """Test Jinja2 attrs object is callable with basic kwargs."""
        attrs = JinjaAttrs()
        attrs["existing"] = "value"

        result = attrs(**{"class": "btn", "type": "button"})

        assert result["existing"] == "value"  # Original preserved
        assert result["class"] == "btn"  # Fallback applied
        assert result["type"] == "button"  # Fallback applied

    def test_existing_attrs_override_fallbacks(self):
        """Test that existing attrs override callable fallbacks."""
        attrs = DjangoAttrs()
        attrs["class"] = "existing-class"
        attrs["data-id"] = "123"

        result = attrs(**{"class": "btn", "type": "button", "data-id": "456"})

        # Existing values should override fallbacks
        assert result["class"] == "existing-class"
        assert result["data-id"] == "123"
        # New fallbacks should be applied
        assert result["type"] == "button"

    def test_immutability(self):
        """Test that callable returns new object without modifying original."""
        attrs = DjangoAttrs()
        attrs["original"] = "value"

        result = attrs(new="added")

        # Original should be unchanged
        assert "new" not in attrs
        assert attrs["original"] == "value"

        # Result should have both
        assert result["original"] == "value"
        assert result["new"] == "added"

    def test_chaining(self):
        """Test that callable attrs can be chained."""
        attrs = DjangoAttrs()

        result = attrs(type="button")(**{"class": "btn"})(disabled=True)

        assert result["type"] == "button"
        assert result["class"] == "btn"
        assert result["disabled"] is True


class TestCallableAttrsClassMerging:
    """Test class merging functionality in callable attrs."""

    def test_append_class_with_ampersand(self):
        """Test class='& suffix' appends to existing class."""
        attrs = DjangoAttrs()
        attrs["class"] = "existing"

        result = attrs(**{"class": "& btn"})

        # Check the final rendered output
        str_result = str(result)
        assert "existing" in str_result
        assert "btn" in str_result

    def test_prepend_class_with_ampersand(self):
        """Test class='prefix &' prepends to existing class."""
        attrs = DjangoAttrs()
        attrs["class"] = "existing"

        result = attrs(**{"class": "btn &"})

        # Check the final rendered output
        str_result = str(result)
        assert "btn" in str_result
        assert "existing" in str_result
        # btn should come first
        assert str_result.index("btn") < str_result.index("existing")

    def test_class_with_no_existing(self):
        """Test class merging when no existing class."""
        attrs = DjangoAttrs()

        result1 = attrs(**{"class": "& btn"})
        result2 = attrs(**{"class": "btn &"})

        # Should just add the class without ampersand
        assert "btn" in str(result1)
        assert "btn" in str(result2)


class TestCallableAttrsConditionalClasses:
    """Test conditional class functionality in callable attrs."""

    def test_conditional_class_dict_unpacking(self):
        """Test conditional classes using dict unpacking."""
        attrs = DjangoAttrs()

        result = attrs(
            **{"class": "btn", "class:active": True, "class:disabled": False}
        )

        # Check that the conditional classes are set in the conditional modifiers
        assert result._conditional_modifiers["class"]["active"] is True
        assert result._conditional_modifiers["class"]["disabled"] is False

    def test_conditional_class_mixed_with_regular_attrs(self):
        """Test mixing conditional classes with regular attributes."""
        attrs = DjangoAttrs()

        result = attrs(
            **{
                "class": "btn",
                "class:active": True,
                "class:disabled": False,
                "data-id": "123",
            }
        )

        assert result._conditional_modifiers["class"]["active"] is True
        assert result._conditional_modifiers["class"]["disabled"] is False
        assert result["data-id"] == "123"


class TestCallableAttrsSpecialAttributes:
    """Test handling of special attribute names."""

    def test_javascript_framework_attributes(self):
        """Test JS framework attributes are preserved."""
        attrs = DjangoAttrs()

        # Use dict unpacking for special characters
        result = attrs(
            **{
                "@click": "handleClick()",
                ":disabled": "isDisabled",
                "v-model": "value",
                "x-on:click": "toggle()",
                "hx-get": "/api/data",
            }
        )

        assert result["@click"] == "handleClick()"
        assert result[":disabled"] == "isDisabled"
        assert result["v-model"] == "value"
        assert result["x-on:click"] == "toggle()"
        assert result["hx-get"] == "/api/data"

    def test_data_attributes(self):
        """Test data-* attributes work correctly."""
        attrs = DjangoAttrs()

        result = attrs(
            **{"data-id": "123", "data-testid": "button", "data-toggle": "modal"}
        )

        assert result["data-id"] == "123"
        assert result["data-testid"] == "button"
        assert result["data-toggle"] == "modal"

    def test_boolean_attributes(self):
        """Test boolean HTML attributes."""
        attrs = DjangoAttrs()

        result = attrs(disabled=True, checked=False, readonly=True)

        assert result["disabled"] is True
        assert result["checked"] is False
        assert result["readonly"] is True

    def test_reserved_keyword_class(self):
        """Test that class attribute works with both dict unpacking and underscore suffix."""
        attrs = DjangoAttrs()

        # Method 1: Dict unpacking for 'class' since it's a Python reserved word
        result1 = attrs(**{"class": "card", "id": "default-card"})
        assert result1["class"] == "card"
        assert result1["id"] == "default-card"

        # Method 2: Trailing underscore is stripped (more ergonomic)
        result2 = attrs(class_="btn", id="my-button")
        assert result2["class"] == "btn"
        assert result2["id"] == "my-button"

        # Test that underscore stripping works with class merging
        attrs3 = DjangoAttrs()
        attrs3["class"] = "existing"
        result3 = attrs3(class_="& added")
        # Check the final rendered output
        str_result = str(result3)
        assert "existing" in str_result
        assert "added" in str_result

    def test_html_escaping_behavior(self):
        """Test HTML escaping behavior differs between Django and Jinja2."""
        dangerous_value = 'Hello "World" & <script>alert("xss")</script>'

        # Django should escape HTML characters
        django_attrs = DjangoAttrs()
        django_attrs["title"] = dangerous_value
        django_str = str(django_attrs)
        assert "&quot;" in django_str  # " escaped
        assert "&amp;" in django_str  # & escaped
        assert "&lt;" in django_str  # < escaped
        assert "&gt;" in django_str  # > escaped
        assert "<script>" not in django_str

        # Jinja2 should not escape (handled at template level)
        jinja_attrs = JinjaAttrs()
        jinja_attrs["title"] = dangerous_value
        jinja_str = str(jinja_attrs)
        assert "&quot;" not in jinja_str
        assert "&amp;" not in jinja_str
        assert "<script>" in jinja_str

        # Test with callable functionality
        django_result = DjangoAttrs()(title=dangerous_value)
        jinja_result = JinjaAttrs()(title=dangerous_value)

        django_callable_str = str(django_result)
        jinja_callable_str = str(jinja_result)

        assert "&quot;" in django_callable_str
        assert "&quot;" not in jinja_callable_str


class TestCallableAttrsNestedAccess:
    """Test nested attrs functionality with callable."""

    def test_nested_attrs_callable(self):
        """Test that nested attrs are also callable."""
        attrs = DjangoAttrs()
        attrs["inner.existing"] = "value"

        # Access nested attrs and call it
        result = attrs.inner(class_="nested")

        assert result["existing"] == "value"
        assert result["class"] == "nested"  # underscore was stripped

    def test_nested_attrs_via_dict_unpacking(self):
        """Test setting nested attrs via dict unpacking."""
        attrs = DjangoAttrs()

        result = attrs(**{"inner.class": "nested-class", "inner.data-id": "456"})

        # Check that the nested attrs were created
        assert hasattr(result, "inner")
        inner = result.inner
        assert inner["class"] == "nested-class"
        assert inner["data-id"] == "456"


class TestDjangoTemplateIntegration:
    """Test that Django {% attrs %} tag uses the new callable."""

    def test_attrs_syntax_still_parses(self):
        """Test Django {% attrs %} tag syntax still parses correctly."""
        # Test that the attrs tag syntax parses without errors
        # We don't need to render it, just verify the syntax is valid
        template_code = """
        {% load includecontents %}
        {% includecontents "components/test.html" %}
            <div {% attrs class="btn" type="button" %}>Content</div>
            <button {% attrs class="btn" class:active=True %}>Button</button>
        {% endincludecontents %}
        """

        # Should parse without syntax errors
        template = Template(template_code)
        assert template is not None  # Template parsed successfully


class TestJinjaTemplateIntegration:
    """Test Jinja2 templates can use callable attrs directly."""

    def test_jinja_callable_attrs_basic(self):
        """Test basic callable usage in Jinja2 template."""
        env = Environment(
            loader=DictLoader(
                {
                    "components/test.html": "{{ attrs(**{'class': 'btn', 'type': 'button'}) }}",
                    "main.html": """
                {% includecontents "test" %}
                Content
                {% endincludecontents %}
                """,
                }
            ),
            extensions=[IncludeContentsExtension],
        )

        template = env.get_template("main.html")
        result = template.render()

        assert 'class="btn"' in result
        assert 'type="button"' in result

    def test_jinja_callable_attrs_with_unpacking(self):
        """Test callable with dict unpacking in Jinja2."""
        env = Environment(
            loader=DictLoader(
                {
                    "components/test.html": "{{ attrs(type='button', **{'@click': 'handler', 'data-id': '123'}) }}",
                    "main.html": """
                {% includecontents "test" %}
                Content
                {% endincludecontents %}
                """,
                }
            ),
            extensions=[IncludeContentsExtension],
        )

        template = env.get_template("main.html")
        result = template.render()

        assert 'type="button"' in result
        assert '@click="handler"' in result
        assert 'data-id="123"' in result

    def test_jinja_component_with_callable_attrs(self):
        """Test using callable attrs in a Jinja2 component."""
        env = Environment(
            loader=DictLoader(
                {
                    "components/button.html": """
                {# props variant="" #}
                <button {{ attrs(type='button', class='& btn') }}>{{ contents }}</button>
                """,
                    "test.html": """
                {% includecontents "button" class="btn-primary" variant="primary" %}
                Click me
                {% endincludecontents %}
                """,
                }
            ),
            extensions=[IncludeContentsExtension],
        )

        template = env.get_template("test.html")
        result = template.render()

        assert 'type="button"' in result
        assert "class=" in result
        assert "btn" in result
        assert "btn-primary" in result
        assert "Click me" in result


class TestEdgeCases:
    """Test edge cases and error conditions."""

    def test_empty_kwargs(self):
        """Test calling attrs with no arguments."""
        attrs = DjangoAttrs()
        attrs["existing"] = "value"

        result = attrs()

        assert result["existing"] == "value"
        assert result is not attrs  # Should be new object

    def test_none_values(self):
        """Test handling of None values."""
        attrs = DjangoAttrs()

        result = attrs(class_=None, visible=None, data_id=None)

        # None values should be preserved (underscore stripped from class_)
        assert result["class"] is None
        assert result["visible"] is None
        assert result["data_id"] is None

    def test_complex_chaining(self):
        """Test complex chaining scenario."""
        attrs = DjangoAttrs()
        attrs["base"] = "value"

        result = attrs(type_="button")(class_="& btn")(**{"@click": "handler"})(
            disabled=True
        )

        assert result["base"] == "value"
        assert result["type"] == "button"  # underscore was stripped
        assert "btn" in str(result)  # Use str() to check class merging
        assert result["@click"] == "handler"
        assert result["disabled"] is True
