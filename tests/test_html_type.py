"""Tests for Html prop type safety and rendering."""

from dataclasses import dataclass

import pytest
from django.template.loader import render_to_string
from django.utils.safestring import SafeString

from includecontents.prop_types import Html
from includecontents.props import validate_props


def test_python_props_html_marked_safe():
    """Html in Python props is marked safe after validation."""

    @dataclass
    class HtmlProps:
        content: Html

    raw = "<b>Bold</b>"
    result = validate_props(HtmlProps, {"content": raw})
    value = result["content"]

    assert isinstance(value, SafeString)
    assert str(value) == raw


@pytest.mark.django_db
def test_template_typed_html_marked_safe():
    """Html typed prop in template is marked safe and not escaped."""
    output = render_to_string(
        "test_html_include.html",
        {},
    )

    # The Html prop is passed as a literal string with tags; it should render unescaped
    assert "<em>Hi</em>" in output
    assert "&lt;em&gt;Hi&lt;/em&gt;" not in output


def test_python_props_list_html_marked_safe():
    """List[Html] in Python props is marked safe item-wise."""

    @dataclass
    class HtmlListProps:
        items: list[Html]

    raw = ["<b>one</b>", "<i>two</i>"]
    result = validate_props(HtmlListProps, {"items": raw})
    items = result["items"]

    assert all(isinstance(v, SafeString) for v in items)
    assert list(map(str, items)) == raw


def test_python_props_optional_list_html():
    """Optional[List[Html]] handles None and list cases."""

    @dataclass
    class OptionalHtmlListProps:
        items: list[Html] | None = None

    # None remains None
    result = validate_props(OptionalHtmlListProps, {})
    assert result["items"] is None

    # List gets items marked safe
    raw = ["<u>a</u>"]
    result = validate_props(OptionalHtmlListProps, {"items": raw})
    assert isinstance(result["items"][0], SafeString)
    assert str(result["items"][0]) == raw[0]


def test_python_props_tuple_and_dict_html():
    """Tuple[Html, int] and Dict[str, Html] mark HTML sub-values safe."""

    @dataclass
    class ComplexProps:
        pair: tuple[Html, int]
        mapping: dict[str, Html]

    raw_pair = ("<em>x</em>", 5)
    raw_map = {"a": "<p>a</p>"}

    result = validate_props(
        ComplexProps,
        {"pair": raw_pair, "mapping": raw_map},
    )

    assert isinstance(result["pair"][0], SafeString)
    assert str(result["pair"][0]) == raw_pair[0]
    assert isinstance(result["mapping"]["a"], SafeString)
    assert str(result["mapping"]["a"]) == raw_map["a"]


@pytest.mark.django_db
def test_template_typed_list_html_marked_safe():
    """list[html] typed prop marks each item safe when provided from context."""
    output = render_to_string(
        "test_html_list_include.html",
        {"items": ["<strong>1</strong>", "<i>2</i>"]},
    )
    assert "<strong>1</strong>" in output
    assert "&lt;strong&gt;1&lt;/strong&gt;" not in output
