from __future__ import annotations

from textwrap import dedent
from typing import Any, Iterable, Mapping

from jinja2 import DictLoader, Environment

from includecontents.jinja2.extension import IncludeContentsExtension




level_template = "        {{{{ record(component='level{level}', level={level}, payload=contents.default|trim) }}}}\n        {{{{ contents }}}}\n    "

DEFAULT_COMPONENTS: dict[str, str] = {
    "complex-component": """
        {% set inner_group = attrs._nested_attrs.get('inner') %}
        {% set inner_data = inner_group._nested_attrs.get('data') if inner_group else None %}
        {{ record(
            component="complex-component",
            attrs=attrs._attrs,
            inner=inner_group._attrs if inner_group else {},
            inner_data=inner_data._attrs if inner_data else {},
            class_value=attrs._attrs.get('class', ''),
        ) }}
        <div>{{ contents }}</div>
    """,
    "simple-button": """
        {# props variant=primary,secondary size=small,large #}
        {{ record(component="simple-button", variant=variant, size=size, text=contents.default|trim) }}
        <button class="btn-{{ variant }} btn-{{ size }}">{{ contents }}</button>
    """,
    "container": """
        {% for name, value in contents.items() %}
            {{ record(component="container", slot=name, value=value|trim) }}
        {% endfor %}
        {{ record(component="container", slot=None, value=contents.default|trim) }}
        <div>{{ contents }}</div>
    """,
    "section": """
        {# props name #}
        {{ record(component="section", name=name, body=contents.default|trim) }}
        <section>{{ contents }}</section>
    """,
}

for i in range(1, 11):
    DEFAULT_COMPONENTS[f"level{i}"] = level_template.format(level=i)



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
        extensions=[IncludeContentsExtension, "jinja2.ext.do"],
        autoescape=False,
    )

    captures: list[dict[str, Any]] = []

    def record(**payload: Any) -> str:
        captures.append(payload)
        return ""

    env.globals.setdefault("record", record)

    rendered = env.get_template("page.html").render(**(dict(context or {})))
    return rendered, captures


def _captures_for(captures: Iterable[dict[str, Any]], component: str) -> list[dict[str, Any]]:
    return [entry for entry in captures if entry.get("component") == component]


class TestNestedComponentScenarios:
    def test_deeply_nested_components_emit_all_levels(self) -> None:
        _, captures = render_template(
            """
            <include:level1>
                <include:level2>
                    <include:level3>
                        <include:level4>
                            <include:level5>
                                <include:level6>
                                    <include:level7>
                                        <include:level8>
                                            <include:level9>
                                                <include:level10>Done</include:level10>
                                            </include:level9>
                                        </include:level8>
                                    </include:level7>
                                </include:level6>
                            </include:level5>
                        </include:level4>
                    </include:level3>
                </include:level2>
            </include:level1>
            """
        )

        levels = {entry["level"] for entry in _captures_for(captures, "level10")}
        assert levels == {10}
        all_levels = sorted(entry["level"] for entry in captures if entry.get("level"))
        assert all_levels == list(range(1, 11))

    def test_many_sibling_components_record_individual_data(self) -> None:
        template_parts = [
            f'<include:section name="section-{i}">Content {i}</include:section>' for i in range(20)
        ]
        _, captures = render_template("\n".join(template_parts))

        sections = _captures_for(captures, "section")
        assert len(sections) == 20
        assert sections[0]["body"] == "Content 0"
        assert sections[-1]["name"] == "section-19"


class TestAttributeAndContentComplexity:
    def test_complex_attribute_normalization(self) -> None:
        _, captures = render_template(
            """
            <include:complex-component
                class="btn primary"
                data-role="cta"
                inner.class="inner"
                inner.data-id="nested-42"
            >Payload</include:complex-component>
            """
        )

        [data] = _captures_for(captures, "complex-component")
        assert data["attrs"]["class"] == "btn primary"
        assert data["inner"] == {"class": "inner"}
        assert data["inner_data"] == {"id": "nested-42"}

    def test_many_named_content_blocks(self) -> None:
        blocks = []
        for i in range(5):
            blocks.append(
                f"<content:slot-{i}>Value {i}</content:slot-{i}>"
            )
        _, captures = render_template(
            f"""
            <include:container>
                {' '.join(blocks)}
            </include:container>
            """
        )

        container_entries = _captures_for(captures, "container")
        slots = {entry["slot"]: entry["value"] for entry in container_entries if entry["slot"] is not None}
        assert slots["slot-0"] == "Value 0"
        assert slots["slot-4"] == "Value 4"


class TestRenderingScenarios:
    def test_simple_button_render(self) -> None:
        rendered, captures = render_template(
            """
            <include:simple-button variant="primary" size="large">Click</include:simple-button>
            """
        )

        data = _captures_for(captures, "simple-button")[0]
        assert data["variant"] == "primary"
        assert data["size"] == "large"
        assert data["text"] == "Click"
        assert "btn-primary" in rendered

    def test_nested_button_in_container(self) -> None:
        rendered, captures = render_template(
            """
            <include:container>
                <include:simple-button variant="secondary" size="small">Press</include:simple-button>
            </include:container>
            """
        )

        container_entries = _captures_for(captures, "container")
        default_entry = next(entry for entry in container_entries if entry["slot"] is None)
        button = _captures_for(captures, "simple-button")[0]
        assert "Press" in default_entry["value"]
        assert button["variant"] == "secondary"
        assert "btn-secondary" in rendered
