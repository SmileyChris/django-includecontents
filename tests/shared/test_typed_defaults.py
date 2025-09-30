"""
Tests for typed defaults in template-typed props.
Ensures that {# props name:type=default #} syntax applies defaults correctly.
"""

import pytest
from django.template import Context, Template
from django.template.exceptions import TemplateSyntaxError


@pytest.mark.django_db
class TestTypedDefaults:
    """Test that template-typed props apply defaults correctly."""

    def test_string_default(self):
        """Test that {# props title:str='Default Title' #} applies string default."""
        template = Template(
            "{% load includecontents %}"
            '{% includecontents "typed_defaults/test_string_default.html" %}{% endincludecontents %}'
        )

        context = Context({})
        output = template.render(context)
        assert "Title: Default Title" in output

    def test_integer_default(self):
        """Test that {# props count:int=10 #} applies integer default."""
        template = Template(
            "{% load includecontents %}"
            '{% includecontents "typed_defaults/test_integer_default.html" %}{% endincludecontents %}'
        )

        context = Context({})
        output = template.render(context)
        assert "Count: 10" in output

    def test_float_default(self):
        """Test that {# props price:float=99.99 #} applies float default."""
        template = Template(
            "{% load includecontents %}"
            '{% includecontents "typed_defaults/test_float_default.html" %}{% endincludecontents %}'
        )

        context = Context({})
        output = template.render(context)
        assert "Price: 99.99" in output

    def test_boolean_default_true(self):
        """Test that {# props active:bool=true #} applies boolean default."""
        template = Template(
            "{% load includecontents %}"
            '{% includecontents "typed_defaults/test_boolean_default_true.html" %}{% endincludecontents %}'
        )

        context = Context({})
        output = template.render(context)
        assert "Active: True" in output

    def test_boolean_default_false(self):
        """Test that {# props enabled:bool=false #} applies boolean default."""
        template = Template(
            "{% load includecontents %}"
            '{% includecontents "typed_defaults/test_boolean_default_false.html" %}{% endincludecontents %}'
        )

        context = Context({})
        output = template.render(context)
        assert "Enabled: False" in output

    def test_choice_default(self):
        """Test that {# props role:choice[admin,user,guest]=user #} applies choice default."""
        template = Template(
            "{% load includecontents %}"
            '{% includecontents "typed_defaults/test_choice_default.html" %}{% endincludecontents %}'
        )

        context = Context({})
        output = template.render(context)
        assert "Role: user" in output

    def test_list_str_empty_default(self):
        """Test that {# props tags:list[str]=[] #} applies empty list default."""
        template = Template(
            "{% load includecontents %}"
            '{% includecontents "typed_defaults/test_list_str_empty_default.html" %}{% endincludecontents %}'
        )

        context = Context({})
        output = template.render(context)
        assert "Tags: 0" in output  # Should show count of 0 items

    def test_list_str_with_values_default(self):
        """Test that {# props tags:list[str]=[python,django] #} applies list with values."""
        template = Template(
            "{% load includecontents %}"
            '{% includecontents "typed_defaults/test_list_str_values_default.html" %}{% endincludecontents %}'
        )

        context = Context({})
        output = template.render(context)
        assert "python,django" in output

    def test_list_int_default(self):
        """Test that {# props numbers:list[int]=[1,2,3] #} applies integer list default."""
        template = Template(
            "{% load includecontents %}"
            '{% includecontents "typed_defaults/test_list_int_default.html" %}{% endincludecontents %}'
        )

        context = Context({})
        output = template.render(context)
        assert "1,2,3" in output

    def test_variable_default(self):
        """Test that {# props name:str={{ default_name }} #} uses variable from context."""
        template = Template(
            "{% load includecontents %}"
            '{% includecontents "typed_defaults/test_variable_default.html" %}{% endincludecontents %}'
        )

        context = Context({"default_name": "John Doe"})
        output = template.render(context)
        assert "Name: John Doe" in output

    def test_filter_expression_default(self):
        """Test that defaults can use Django filter expressions."""
        template = Template(
            "{% load includecontents %}"
            '{% includecontents "typed_defaults/test_filter_default.html" %}{% endincludecontents %}'
        )

        context = Context({"prefix": ""})  # Empty prefix should use filter default
        output = template.render(context)
        assert "Title: Mr." in output

    def test_override_default_with_provided_value(self):
        """Test that provided values override defaults."""
        template = Template(
            "{% load includecontents %}"
            '{% includecontents "typed_defaults/test_string_default.html" with title="Custom Title" %}{% endincludecontents %}'
        )

        context = Context({})
        output = template.render(context)
        assert "Title: Custom Title" in output
        assert "Default Title" not in output

    def test_optional_without_default(self):
        """Test that optional props without defaults are None when not provided."""
        template = Template(
            "{% load includecontents %}"
            '{% includecontents "test_coercion/test_optional_no_default.html" %}{% endincludecontents %}'
        )

        context = Context({})
        output = template.render(context)
        assert "No subtitle" in output

    def test_required_without_default_raises_error(self):
        """Test that required props without defaults raise error when missing."""
        template = Template(
            "{% load includecontents %}"
            '{% includecontents "typed_defaults/test_required_no_default.html" %}{% endincludecontents %}'
        )

        context = Context({})
        with pytest.raises(
            TemplateSyntaxError, match='Missing required attribute "title"'
        ):
            template.render(context)

    def test_multiple_defaults(self):
        """Test multiple props with different default types."""
        template = Template(
            "{% load includecontents %}"
            '{% includecontents "typed_defaults/test_multiple_defaults.html" %}{% endincludecontents %}'
        )

        context = Context({})
        output = template.render(context)
        assert "Title: Welcome" in output
        assert "Count: 5" in output
        assert "Active: True" in output
        assert "Role: guest" in output

    def test_mixed_defaults_and_provided(self):
        """Test mixing defaults with provided values."""
        template = Template(
            "{% load includecontents %}"
            '{% includecontents "typed_defaults/test_multiple_defaults.html" with count=15 active=false %}{% endincludecontents %}'
        )

        context = Context({})
        output = template.render(context)
        assert "Title: Welcome" in output  # Default used
        assert "Count: 15" in output  # Provided value used
        assert "Active: False" in output  # Provided value used
        assert "Role: guest" in output  # Default used


class TestDefaultTypes:
    """Test different ways defaults can be specified."""

    def test_quoted_string_default(self):
        """Test string defaults with quotes."""
        template = Template(
            "{% load includecontents %}"
            '{% includecontents "typed_defaults/test_quoted_string_default.html" %}{% endincludecontents %}'
        )

        context = Context({})
        output = template.render(context)
        assert 'Message: "Hello World"' in output

    def test_numeric_defaults(self):
        """Test various numeric default formats."""
        template = Template(
            "{% load includecontents %}"
            '{% includecontents "typed_defaults/test_numeric_defaults.html" %}{% endincludecontents %}'
        )

        context = Context({})
        output = template.render(context)
        assert "Int: 42" in output
        assert "Float: 3.14" in output
        assert "Negative: -10" in output

    def test_complex_variable_defaults(self):
        """Test defaults using complex variable expressions."""
        template = Template(
            "{% load includecontents %}"
            '{% includecontents "typed_defaults/test_complex_variable_defaults.html" %}{% endincludecontents %}'
        )

        context = Context({"user": {"name": "Alice"}, "settings": {"theme": "dark"}})
        output = template.render(context)
        assert "User: Alice" in output
        assert "Theme: dark" in output
