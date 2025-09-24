from __future__ import annotations

from textwrap import dedent
from typing import Any, Mapping

import pytest
from jinja2 import DictLoader, Environment, TemplateRuntimeError

from includecontents.jinja2.extension import IncludeContentsExtension


DEFAULT_COMPONENTS: dict[str, str] = {
    "button": """
        {# props variant=primary,secondary,danger #}
        {{ record(component="button", variant=variant) }}
        <button class="btn-{{ variant }}">{{ contents }}</button>
    """,
    "button-optional": """
        {# props variant=,primary,secondary,dark-mode,icon-only #}
        {{ record(component="button-optional", variant=variant) }}
        <button>{{ contents }}</button>
    """,
    "button-multi": """
        {# props variant=primary,secondary,accent,icon,large #}
        {{ record(
            component="button-multi",
            variant=variant,
            primary_flag=variantPrimary,
            icon_flag=variantIcon,
        ) }}
        <button>{{ contents }}</button>
    """,
    "enum-edge-cases": """
        {# props status=,pending,complete,failed special=,@,#,$,% single=,a numbers=,1,2,3 mixed=,test,other #}
        {{ record(
            component="enum-edge-cases",
            status=status,
            special=special,
            single=single,
            numbers=numbers,
            mixed=mixed,
        ) }}
        <div>{{ contents }}</div>
    """,

    "enum-whitespace": """
        {# props variant=,a,b,c #}
        {{ record(component="enum-whitespace", variant=variant) }}
        <div>{{ contents }}</div>
    """,
}


def _normalize(components: Mapping[str, str]) -> dict[str, str]:
    return {
        f"components/{name}.html": dedent(template).strip()
        for name, template in components.items()
    }


def render_template(
    template_source: str,
    *,
    components: Mapping[str, str] | None = None,
    context: Mapping[str, Any] | None = None,
) -> tuple[str, list[dict[str, Any]]]:
    templates = {"page.html": dedent(template_source).strip()}
    component_templates = _normalize(DEFAULT_COMPONENTS)
    if components:
        component_templates.update(_normalize(components))
    templates.update(component_templates)

    env = Environment(
        loader=DictLoader(templates),
        extensions=[IncludeContentsExtension],
        autoescape=False,
    )

    captures: list[dict[str, Any]] = []

    def record(**payload: Any) -> str:
        captures.append(payload)
        return ""

    env.globals.setdefault("record", record)

    rendered = env.get_template("page.html").render(**(dict(context or {})))
    return rendered, captures


def _capture_for(captures: list[dict[str, Any]], component: str) -> dict[str, Any]:
    for entry in captures:
        if entry.get("component") == component:
            return entry
    raise AssertionError(f"No capture recorded for component {component!r}")


class TestEnumValidation:
    def test_required_enum_missing_raises(self) -> None:
        with pytest.raises(TemplateRuntimeError) as exc:
            render_template('<include:button>Click</include:button>')
        assert "missing required prop 'variant'" in str(exc.value)

    def test_invalid_enum_value_raises(self) -> None:
        with pytest.raises(TemplateRuntimeError) as exc:
            render_template('<include:button variant="invalid">Click</include:button>')
        message = str(exc.value)
        assert 'Invalid value "invalid"' in message
        assert 'attribute "variant"' in message

    def test_valid_enum_value_renders(self) -> None:
        _, captures = render_template('<include:button variant="primary">Click</include:button>')
        data = _capture_for(captures, "button")
        assert data["variant"] == "primary"

    def test_optional_enum_defaults_empty(self) -> None:
        _, captures = render_template('<include:button-optional>Click</include:button-optional>')
        data = _capture_for(captures, "button-optional")
        assert not data["variant"]

    def test_optional_enum_accepts_value(self) -> None:
        _, captures = render_template('<include:button-optional variant="dark-mode">Click</include:button-optional>')
        data = _capture_for(captures, "button-optional")
        assert data["variant"] == "dark-mode"

    def test_multi_value_enum_sets_flags(self) -> None:
        _, captures = render_template('<include:button-multi variant="primary icon">Click</include:button-multi>')
        data = _capture_for(captures, "button-multi")
        assert data["variant"] == "primary icon"
        assert data["primary_flag"] is True
        assert data["icon_flag"] is True

    def test_multi_value_enum_invalid_value_raises(self) -> None:
        with pytest.raises(TemplateRuntimeError) as exc:
            render_template('<include:button-multi variant="primary invalid">Click</include:button-multi>')
        assert 'Invalid value "invalid"' in str(exc.value)

    def test_enum_case_sensitive(self) -> None:
        with pytest.raises(TemplateRuntimeError) as exc:
            render_template('<include:button variant="PRIMARY">Click</include:button>')
        assert '"PRIMARY"' in str(exc.value)


class TestSpecialCharacterEnums:
    def test_special_character_value_allowed(self) -> None:
        _, captures = render_template('<include:enum-edge-cases special="@">Content</include:enum-edge-cases>')
        data = _capture_for(captures, "enum-edge-cases")
        assert data["special"] == "@"

    def test_invalid_special_character_rejected(self) -> None:
        with pytest.raises(TemplateRuntimeError) as exc:
            render_template('<include:enum-edge-cases special="&">Invalid</include:enum-edge-cases>')
        assert '&' in str(exc.value)

    def test_numeric_enum_value(self) -> None:
        _, captures = render_template('<include:enum-edge-cases numbers="1">Number</include:enum-edge-cases>')
        data = _capture_for(captures, "enum-edge-cases")
        assert data["numbers"] == "1"

    def test_single_character_enum(self) -> None:
        _, captures = render_template('<include:enum-edge-cases single="a">Single</include:enum-edge-cases>')
        data = _capture_for(captures, "enum-edge-cases")
        assert data["single"] == "a"

    def test_mixed_enum_value(self) -> None:
        _, captures = render_template('<include:enum-edge-cases mixed="test">Mixed</include:enum-edge-cases>')
        data = _capture_for(captures, "enum-edge-cases")
        assert data["mixed"] == "test"

    def test_whitespace_enum_accepts_value(self) -> None:
        _, captures = render_template('<include:enum-whitespace variant="b">Whitespace</include:enum-whitespace>')
        data = _capture_for(captures, "enum-whitespace")
        assert data["variant"] == "b"

    def test_whitespace_enum_rejects_invalid(self) -> None:
        with pytest.raises(TemplateRuntimeError):
            render_template('<include:enum-whitespace variant="z">Bad</include:enum-whitespace>')
