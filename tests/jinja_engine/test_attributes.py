from __future__ import annotations

from textwrap import dedent
from types import SimpleNamespace
from typing import Any, Mapping

import pytest
from jinja2 import DictLoader, Environment

from includecontents.jinja2.extension import IncludeContentsExtension


def render_component(
    base_template: str,
    *,
    components: Mapping[str, str],
    context: Mapping[str, Any] | None = None,
) -> tuple[str, list[dict[str, Any]]]:
    """Render ``base_template`` and capture component state."""
    templates: dict[str, str] = {"base.html": dedent(base_template).strip()}
    for name, template in components.items():
        templates[f"components/{name}.html"] = dedent(template).strip()

    env = Environment(
        loader=DictLoader(templates),
        extensions=[IncludeContentsExtension, "jinja2.ext.do"],
        autoescape=False,
    )

    captures: list[dict[str, Any]] = []

    def record(**payload: Any) -> str:
        captures.append(payload)
        return ""

    env.globals.setdefault("record", record)

    rendered = env.get_template("base.html").render(**(dict(context or {})))
    return rendered, captures


class TestAttributeHandling:
    """Integration tests for attribute handling in the Jinja engine."""

    def test_basic_attrs_spread(self) -> None:
        output, captures = render_component(
            """
            <include:card title="Hello" class="primary" id="card-1" data_role="{{ role }}">
              Body text
            </include:card>
            """,
            components={
                "card": """
                    {# props title #}
                    {% do attrs.__setitem__('class', '& card') %}
                    {{ record(attrs=attrs, contents=contents, title=title) }}
                """
            },
            context={"role": "featured"},
        )

        payload = captures[0]
        attrs = payload["attrs"]

        assert payload["title"] == "Hello"
        assert payload["contents"].stripped == "Body text"
        assert 'class="primary card"' in str(attrs)
        assert attrs._attrs["id"] == "card-1"
        assert getattr(attrs, "data").role == "featured"
        assert output.strip() == ""

    def test_class_append_syntax(self) -> None:
        _, captures = render_component(
            '<include:card-extend title="Append" class="user-class" />',
            components={
                "card-extend": """
                    {# props title #}
                    {% do attrs.__setitem__('class', '& card-extend') %}
                    {{ record(attrs=attrs) }}
                """
            },
        )

        attrs = captures[0]["attrs"]
        assert 'class="user-class card-extend"' in str(attrs)
        assert "title" not in attrs._attrs

    def test_class_prepend_syntax(self) -> None:
        _, captures = render_component(
            '<include:card-prepend title="Prepend" class="user-class" />',
            components={
                "card-prepend": """
                    {# props title #}
                    {% do attrs.__setitem__('class', 'card-prepend &') %}
                    {{ record(attrs=attrs) }}
                """
            },
        )

        attrs = captures[0]["attrs"]
        assert 'class="card-prepend user-class"' in str(attrs)

    @pytest.mark.parametrize("is_active, expected_flag", [(True, True), (False, False)])
    def test_class_negation_syntax(self, is_active: bool, expected_flag: bool) -> None:
        _, captures = render_component(
            '<include:card-conditional title="Toggle" class:active="{{ is_active }}" />',
            components={
                "card-conditional": """
                    {# props title #}
                    {% do attrs.__setitem__('class', '& card') %}
                    {{ record(attrs=attrs) }}
                """
            },
            context={"is_active": is_active},
        )

        attrs = captures[0]["attrs"]
        class_group = getattr(attrs, "class")
        assert class_group.active is expected_flag
        assert 'class="card"' in str(attrs)

    def test_javascript_event_attributes(self) -> None:
        _, captures = render_component(
            """
            <include:button
                text="Click"
                @click="handleClick()"
                v-on:submit="onSubmit"
                x-on:click="toggle()"
                :class="{ 'active': true }"
            />
            """,
            components={
                "button": """
                    {# props text #}
                    {{ record(attrs=attrs) }}
                """
            },
        )

        attrs = captures[0]["attrs"]
        assert attrs._attrs["@click"] == "handleClick()"
        assert attrs._attrs["v-on:submit"] == "onSubmit"
        assert attrs._attrs["x-on:click"] == "toggle()"
        assert attrs._attrs[":class"] == "{ &#x27;active&#x27;: true }"

    def test_javascript_event_modifiers(self) -> None:
        _, captures = render_component(
            """
            <include:button
                text="Click"
                @click.stop.prevent="handleClick()"
                @keyup.enter="handleEnter()"
            />
            """,
            components={
                "button": """
                    {# props text #}
                    {{ record(attrs=attrs) }}
                """
            },
        )

        attrs = captures[0]["attrs"]
        assert attrs._attrs["@click.stop.prevent"] == "handleClick()"
        assert attrs._attrs["@keyup.enter"] == "handleEnter()"

    def test_template_variables_in_attributes(self) -> None:
        _, captures = render_component(
            '<include:button data_value="{{ count|default(0) }}" data_label="{{ label|upper }}" />',
            components={
                "button": """
                    {{ record(attrs=attrs) }}
                """
            },
            context={"count": 5, "label": "items"},
        )

        attrs = captures[0]["attrs"]
        data_group = getattr(attrs, "data")
        assert data_group.value == 5
        assert data_group.label == "ITEMS"

    def test_attributes_support_filters_and_callables(self) -> None:
        value = SimpleNamespace(text="hello")

        def get_size() -> int:
            return 42

        value.get_size = get_size  # type: ignore[attr-defined]

        _, captures = render_component(
            '<include:button-props text="{{ value.text|upper }}" size="{{ value.get_size() }}" />',
            components={
                "button-props": """
                    {# props text, size #}
                    {{ record(text=text, size=size) }}
                """
            },
            context={"value": value},
        )

        payload = captures[0]
        assert payload["text"] == "HELLO"
        assert payload["size"] == 42

    def test_nested_attributes(self) -> None:
        _, captures = render_component(
            '<include:nested-attrs class="outer" inner.class="inner" inner.data_value="{{ inner_value }}" />',
            components={
                "nested-attrs": """
                    {{ record(attrs=attrs) }}
                """
            },
            context={"inner_value": "42"},
        )

        attrs = captures[0]["attrs"]
        inner = getattr(attrs, "inner")
        assert 'class="outer"' in str(attrs)
        assert inner._attrs["class"] == "inner"
        assert getattr(inner, "data").value == "42"

    def test_attrs_group_syntax(self) -> None:
        _, captures = render_component(
            """
            <include:form-with-button
                button.type="submit"
                button.class="btn btn-primary"
                data_form="true"
            />
            """,
            components={
                "form-with-button": """
                    {{ record(attrs=attrs) }}
                """
            },
        )

        attrs = captures[0]["attrs"]
        button_group = getattr(attrs, "button")
        assert button_group._attrs == {"type": "submit", "class": "btn btn-primary"}
        assert getattr(attrs, "data").form == "true"

    def test_self_closing_with_attributes(self) -> None:
        _, captures = render_component(
            '<include:button class="btn" @click="test()" />',
            components={
                "button": """
                    {{ record(attrs=attrs) }}
                """
            },
        )

        attrs = captures[0]["attrs"]
        assert attrs._attrs["class"] == "btn"
        assert attrs._attrs["@click"] == "test()"

    def test_attribute_escaping(self) -> None:
        _, captures = render_component(
            '<include:button test="2>1" another="3>2" />',
            components={
                "button": """
                    {{ record(attrs=attrs) }}
                """
            },
        )

        attrs = captures[0]["attrs"]
        assert 'test="2&gt;1"' in str(attrs)
        assert 'another="3&gt;2"' in str(attrs)

    def test_conditional_css_classes_from_attributes(self) -> None:
        output, captures = render_component(
            """
            <include:body_text alignment="center" size="large">
              <p>{{ text }}</p>
            </include:body_text>
            """,
            components={
                "body_text": """
                    {# props alignment, size #}
                    <div class="body{% if alignment %} text-{{ alignment }}{% endif %}{% if size %} body-{{ size }}{% endif %}">
                      {{ contents }}
                    </div>
                    {{ record(alignment=alignment, size=size, rendered_output=output) }}
                """
            },
            context={"text": "A long paragraph of text goes here."},
        )

        payload = captures[0]
        assert payload["alignment"] == "center"
        assert payload["size"] == "large"
        assert '<div class="body text-center body-large">' in output
        assert '<p>A long paragraph of text goes here.</p>' in output


class TestAttributePrecedence:
    """Tests covering precedence rules for merged attributes."""

    def test_local_attrs_precedence(self) -> None:
        _, captures = render_component(
            '<include:card class="local" id="outer">Content</include:card>',
            components={
                "card": """
                    {% if 'class' not in attrs._attrs %}
                        {% do attrs.__setitem__('class', 'component-default') %}
                    {% endif %}
                    {{ record(attrs=attrs, contents=contents) }}
                """
            },
        )

        attrs = captures[0]["attrs"]
        assert attrs._attrs["class"] == "local"
        assert attrs._attrs["id"] == "outer"

    def test_nested_attrs_precedence(self) -> None:
        _, captures = render_component(
            """
            <include:nested-component
                data_root="true"
                inner.class="leaf"
                inner.data_source="custom"
            >Content</include:nested-component>
            """,
            components={
                "nested-component": """
                    {% set inner_group = attrs._nested_attrs.get('inner') %}
                    {% if not inner_group or 'class' not in inner_group._attrs %}
                        {% do attrs.__setitem__('inner.class', 'default-inner') %}
                    {% endif %}
                    {{ record(attrs=attrs, contents=contents) }}
                """
            },
        )

        payload = captures[0]
        attrs = payload["attrs"]
        inner = getattr(attrs, "inner")

        assert getattr(attrs, "data").root == "true"
        assert inner._attrs["class"] == "leaf"
        assert getattr(inner, "data").source == "custom"
        assert payload["contents"].stripped == "Content"
