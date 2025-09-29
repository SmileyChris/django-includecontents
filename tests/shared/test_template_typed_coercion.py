"""
Tests for type coercion in template-typed props.
Ensures that {# props #} syntax coerces values the same way as @component decorated classes.
"""

from dataclasses import dataclass
from typing import List

import pytest
from django.template import Context, Template

from includecontents.shared.validation import validate_props


@pytest.mark.django_db
class TestTemplateTypedCoercion:
    """Test that template-typed props coerce values correctly."""

    def test_int_coercion_from_string(self):
        """Test that {# props count:int #} coerces string to int."""
        # The test template has: {# props count:int #}
        template = Template(
            "{% load includecontents %}"
            '{% includecontents "test_coercion/test_int_coerce.html" with count="25" %}{% endincludecontents %}'
        )

        context = Context({})
        output = template.render(context)
        # The value should be coerced to int, not remain as string
        assert "Count is 25" in output

    def test_bool_coercion_from_string(self):
        """Test that {# props active:bool #} coerces string to bool."""
        # Test various true values
        for true_val in ["true", "True", "1", "yes", "on"]:
            template = Template(
                "{% load includecontents %}"
                f'{{% includecontents "test_coercion/test_bool_coerce.html" with active="{true_val}" %}}{{% endincludecontents %}}'
            )

            context = Context({})
            output = template.render(context)
            assert "Active is True" in output, f"Failed for value: {true_val}"

        # Test various false values
        for false_val in ["false", "False", "0", "no", "off"]:
            template = Template(
                "{% load includecontents %}"
                f'{{% includecontents "test_coercion/test_bool_coerce.html" with active="{false_val}" %}}{{% endincludecontents %}}'
            )

            context = Context({})
            output = template.render(context)
            # print(f"DEBUG: For {false_val}, got output: {repr(output)}")
            assert "Active is False" in output, f"Failed for value: {false_val}"

    def test_float_coercion_from_string(self):
        """Test that {# props rating:float #} coerces string to float."""
        template = Template(
            "{% load includecontents %}"
            '{% includecontents "test_coercion/test_float_coerce.html" with rating="4.5" %}{% endincludecontents %}'
        )

        context = Context({})
        output = template.render(context)
        assert "Rating: 4.5" in output

    def test_list_str_coercion_from_comma_separated(self):
        """Test that {# props tags:list[str] #} splits comma-separated strings."""
        template = Template(
            "{% load includecontents %}"
            '{% includecontents "test_coercion/test_list_str_coerce.html" with tags="python, django, web" %}{% endincludecontents %}'
        )

        context = Context({})
        output = template.render(context)
        assert "python,django,web" in output

    def test_list_int_coercion_from_comma_separated(self):
        """Test that {# props numbers:list[int] #} splits and coerces to integers."""
        template = Template(
            "{% load includecontents %}"
            '{% includecontents "test_coercion/test_list_int_coerce.html" with numbers="1, 2, 3, 4, 5" %}{% endincludecontents %}'
        )

        context = Context({})
        output = template.render(context)
        # Should render as integers, not strings with spaces
        assert "1,2,3,4,5" in output

    def test_optional_int_coercion(self):
        """Test that optional types still coerce when provided."""
        # Test with value provided
        template = Template(
            "{% load includecontents %}"
            '{% includecontents "test_coercion/test_optional_int.html" with max_items="10" %}{% endincludecontents %}'
        )

        context = Context({})
        output = template.render(context)
        assert "Max: 10" in output

        # Test without value (should use None/empty)
        template = Template(
            "{% load includecontents %}"
            '{% includecontents "test_coercion/test_optional_int.html" %}{% endincludecontents %}'
        )

        context = Context({})
        output = template.render(context)
        assert "No max" in output


class TestCoercionParity:
    """Test that both Python props and template-typed props coerce identically."""

    def test_python_props_coercion_baseline(self):
        """Establish baseline for Python props coercion."""

        @dataclass
        class TestProps:
            count: int
            active: bool
            rating: float
            tags: List[str]
            numbers: List[int]

        # Test coercion from strings
        result = validate_props(
            TestProps,
            {
                "count": "25",
                "active": "true",
                "rating": "4.5",
                "tags": "python, django, web",
                "numbers": "1, 2, 3",
            },
        )

        assert result["count"] == 25
        assert result["active"] is True
        assert result["rating"] == 4.5
        assert result["tags"] == ["python", "django", "web"]
        assert result["numbers"] == [1, 2, 3]
        assert all(isinstance(n, int) for n in result["numbers"])

    def test_coerce_value_function_directly(self):
        """Test the coerce_value function directly."""
        from typing import Optional

        from includecontents.shared.typed_props import coerce_value

        # Test int coercion
        assert coerce_value("25", int) == 25
        assert coerce_value(25, int) == 25

        # Test bool coercion
        assert coerce_value("true", bool) is True
        assert coerce_value("false", bool) is False
        assert coerce_value("1", bool) is True
        assert coerce_value("0", bool) is False

        # Test float coercion
        assert coerce_value("4.5", float) == 4.5
        assert coerce_value(4.5, float) == 4.5

        # Test list[str] coercion
        assert coerce_value("a, b, c", List[str]) == ["a", "b", "c"]
        assert coerce_value(["a", "b"], List[str]) == ["a", "b"]

        # Test list[int] coercion
        assert coerce_value("1, 2, 3", List[int]) == [1, 2, 3]
        assert coerce_value([1, 2], List[int]) == [1, 2]

        # Test Optional types
        assert coerce_value(None, Optional[int]) is None
        assert coerce_value("25", Optional[int]) == 25

        # Test that None is preserved
        assert coerce_value(None, int) is None
        assert coerce_value(None, List[int]) is None
