from __future__ import annotations

from types import SimpleNamespace

import pytest

from ._helpers import first_capture, render_component


class TestAttributeHandling:
    """Integration tests for attribute handling in the Jinja engine."""

    def test_basic_attrs_spread(self) -> None:
        output, captures = render_component(
            """
            <include:card title="Hello" class="primary" id="card-1" data-role="{{ role }}">
              Body text
            </include:card>
            """,
            use=["card"],
            context={"role": "featured"},
        )

        payload = first_capture(captures, "card")
        attrs = payload["attrs"]

        assert payload["title"] == "Hello"
        assert payload["default"].strip() == "Body text"
        assert 'class="primary card"' in str(attrs)
        assert attrs._attrs["id"] == "card-1"
        assert attrs.dataRole == "featured"
        assert output.strip()

    def test_class_append_syntax(self) -> None:
        _, captures = render_component(
            '<include:card-extend title="Append" class="user-class" />',
            use=["card-extend"],
        )

        attrs = first_capture(captures, "card-extend")["attrs"]
        assert 'class="user-class card-extend"' in str(attrs)
        assert "title" not in attrs._attrs

    def test_class_prepend_syntax(self) -> None:
        _, captures = render_component(
            '<include:card-prepend title="Prepend" class="user-class" />',
            use=["card-prepend"],
        )

        attrs = first_capture(captures, "card-prepend")["attrs"]
        assert 'class="card-prepend user-class"' in str(attrs)

    @pytest.mark.parametrize("is_active, expected_flag", [(True, True), (False, False)])
    def test_class_negation_syntax(self, is_active: bool, expected_flag: bool) -> None:
        _, captures = render_component(
            '<include:card-conditional title="Toggle" class:active="{{ is_active }}" />',
            use=["card-conditional"],
            context={"is_active": is_active},
        )

        attrs = first_capture(captures, "card-conditional")["attrs"]
        class_group = getattr(attrs, "class")
        assert class_group.active is expected_flag
        # Check that "card" is present in the class string (with or without "active")
        class_str = str(attrs)
        assert "card" in class_str
        if expected_flag:
            assert "active" in class_str
        else:
            assert "active" not in class_str

    def test_javascript_event_attributes(self) -> None:
        _, captures = render_component(
            """
            <include:button
                text="Click"
                variant="primary"
                @click="handleClick()"
                v-on:submit="onSubmit"
                x-on:click="toggle()"
                :class="{ 'active': true }"
            />
            """,
            use=["button"],
        )

        attrs = first_capture(captures, "button")["attrs"]
        assert attrs._attrs["@click"] == "handleClick()"
        assert attrs._attrs["v-on:submit"] == "onSubmit"
        assert attrs._attrs["x-on:click"] == "toggle()"
        # Hard-coded strings are no longer escaped
        assert attrs._attrs[":class"] == "{ 'active': true }"

    def test_javascript_event_modifiers(self) -> None:
        _, captures = render_component(
            """
            <include:button
                text="Click"
                variant="primary"
                @click.stop.prevent="handleClick()"
                @keyup.enter="handleEnter()"
            />
            """,
            use=["button"],
        )

        attrs = first_capture(captures, "button")["attrs"]
        assert attrs._attrs["@click.stop.prevent"] == "handleClick()"
        assert attrs._attrs["@keyup.enter"] == "handleEnter()"

    def test_template_variables_in_attributes(self) -> None:
        _, captures = render_component(
            '<include:button variant="primary" data-value="{{ count|default(0) }}" data-label="{{ label|upper }}" />',
            use=["button"],
            context={"count": 5, "label": "items"},
        )

        attrs = first_capture(captures, "button")["attrs"]
        assert attrs.dataValue == 5
        assert attrs.dataLabel == "ITEMS"

    def test_attributes_support_filters_and_callables(self) -> None:
        value = SimpleNamespace(text="hello")

        def get_size() -> int:
            return 42

        value.get_size = get_size  # type: ignore[attr-defined]

        _, captures = render_component(
            '<include:button-props text="{{ value.text|upper }}" size="{{ value.get_size() }}" />',
            use=["button-props"],
            context={"value": value},
        )

        payload = first_capture(captures, "button-props")
        assert payload["text"] == "HELLO"
        assert payload["size"] == 42

    def test_nested_attributes(self) -> None:
        _, captures = render_component(
            '<include:nested-attrs class="outer" inner.class="inner" inner.data-value="{{ inner_value }}" />',
            use=["nested-attrs"],
            context={"inner_value": "42"},
        )

        attrs = first_capture(captures, "nested-attrs")["attrs"]
        inner = getattr(attrs, "inner")
        assert 'class="outer"' in str(attrs)
        assert inner._attrs["class"] == "inner"
        assert inner.dataValue == "42"

    def test_attrs_group_syntax(self) -> None:
        _, captures = render_component(
            """
            <include:form-with-button
                button.type="submit"
                button.class="btn btn-primary"
                data-form="true"
            />
            """,
            use=["form-with-button"],
        )

        attrs = first_capture(captures, "form-with-button")["attrs"]
        button_group = getattr(attrs, "button")
        assert button_group._attrs == {"type": "submit", "class": "btn btn-primary"}
        assert attrs.dataForm == "true"

    def test_self_closing_with_attributes(self) -> None:
        _, captures = render_component(
            '<include:button variant="primary" class="btn" @click="test()" />',
            use=["button"],
        )

        attrs = first_capture(captures, "button")["attrs"]
        assert attrs._attrs["class"] == "btn"
        assert attrs._attrs["@click"] == "test()"

    def test_attribute_escaping(self) -> None:
        _, captures = render_component(
            '<include:button variant="primary" test="2>1" another="3>2" />',
            use=["button"],
        )

        attrs = first_capture(captures, "button")["attrs"]
        # Hard-coded strings are no longer escaped
        assert 'test="2>1"' in str(attrs)
        assert 'another="3>2"' in str(attrs)

    def test_hardcoded_string_attributes(self) -> None:
        _, captures = render_component(
            '<include:button variant="primary" test="Don\'t worry" another=\'Say "hello"\' />',
            use=["button"],
        )

        attrs = first_capture(captures, "button")["attrs"]
        assert 'test="Don\'t worry"' in str(attrs)
        assert 'another="Say "hello""' in str(attrs)

    def test_variable_content_escaping(self) -> None:
        _, captures = render_component(
            '<include:button variant="primary" test="{{ quote_var }}" another="{{ apostrophe_var }}" />',
            use=["button"],
            context={"quote_var": 'Say "hello"', "apostrophe_var": "Don't worry"},
        )

        attrs = first_capture(captures, "button")["attrs"]
        # In Jinja2, template variables are processed by Jinja2's template engine
        # Since the test environment doesn't have autoescape enabled, variables come through unescaped
        assert 'test="Say "hello""' in str(attrs)
        assert 'another="Don\'t worry"' in str(attrs)

    def test_conditional_css_classes_from_attributes(self) -> None:
        output, captures = render_component(
            """
            <include:body_text alignment="center" size="large">
              <p>{{ text }}</p>
            </include:body_text>
            """,
            use=["body_text"],
            context={"text": "A long paragraph of text goes here."},
        )

        payload = first_capture(captures, "body_text")
        assert payload["alignment"] == "center"
        assert payload["size"] == "large"
        assert '<div class="body text-center body-large">' in output
        assert "A long paragraph of text goes here." in output


class TestAttributePrecedence:
    """Tests covering precedence rules for merged attributes."""

    def test_local_attrs_precedence(self) -> None:
        _, captures = render_component(
            '<include:simple-card class="local" id="outer">Content</include:simple-card>',
            use=["simple-card"],
        )

        attrs = first_capture(captures, "simple-card")["attrs"]
        assert attrs._attrs["class"] == "local"
        assert attrs._attrs["id"] == "outer"

    def test_nested_attrs_precedence(self) -> None:
        _, captures = render_component(
            """
            <include:nested-component
                data-root="true"
                inner.class="leaf"
                inner.data-source="custom"
            >Content</include:nested-component>
            """,
            use=["nested-component"],
        )

        payload = first_capture(captures, "nested-component")
        attrs = payload["attrs"]
        inner = getattr(attrs, "inner")

        assert attrs.dataRoot == "true"
        assert inner._attrs["class"] == "leaf"
        assert inner.dataSource == "custom"
        assert payload["contents"].default.strip() == "Content"
