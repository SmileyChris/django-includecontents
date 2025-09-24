from __future__ import annotations

from textwrap import dedent
from typing import Any, Mapping

from jinja2 import DictLoader, Environment

from includecontents.jinja2.extension import IncludeContentsExtension


DEFAULT_COMPONENTS: dict[str, str] = {
    "card-with-footer": """
        {# props title #}
        {{ record(
            component="card-with-footer",
            title=title,
            default=contents.default|trim,
            footer=contents.footer|trim,
            sidebar=contents.sidebar|trim,
        ) }}
        <card title="{{ title }}">
            <main>{{ contents }}</main>
            <footer>{{ contents.footer }}</footer>
            <aside>{{ contents.sidebar }}</aside>
        </card>
    """,
    "card": """
        {# props title="" #}
        {{ record(
            component="card",
            title=title|default(""),
            default=contents.default|trim,
            oldstyle=contents.oldstyle|trim,
            newstyle=contents.newstyle|trim,
        ) }}
        <card title="{{ title|default("") }}">{{ contents }}</card>
    """,
    "outer-card": """
        {# props title #}
        {{ record(
            component="outer-card",
            title=title,
            main=contents.main|trim,
            footer=contents.footer|trim,
        ) }}
        <outer>{{ contents.main }}</outer>
        <outer-footer>{{ contents.footer }}</outer-footer>
    """,
    "inner-card": """
        {# props title #}
        {{ record(
            component="inner-card",
            title=title,
            body=contents.default|trim,
            footer=contents.footer|trim,
        ) }}
        <inner>{{ contents }}</inner>
    """,
    "card-with-props": """
        {# props title, variant, size #}
        {{ record(
            component="card-with-props",
            title=title,
            variant=variant,
            size=size,
            body=contents.body|trim,
        ) }}
        <card>{{ contents.body }}</card>
    """,
    "flexible-card": """
        {# props title="" #}
        {% set data_group = attrs._nested_attrs.get('data') %}
        {{ record(
            component="flexible-card",
            title=title|default(""),
            attrs=attrs._attrs,
            data_attrs=data_group._attrs if data_group else {},
            default=contents.default|trim,
            header=contents.header|trim,
        ) }}
        <card>{{ contents }}</card>
    """,
    "level1": """
        {{ record(component="level1", section1=contents.section1|trim) }}
        {{ contents.section1 }}
    """,
    "level2": """
        {{ record(component="level2", section2=contents.section2|trim) }}
        {{ contents.section2 }}
    """,
    "level3": """
        {{ record(component="level3", section3=contents.section3|trim) }}
        {{ contents.section3 }}
    """,
    "level4": """
        {{ record(component="level4", section4=contents.section4|trim) }}
        {{ contents.section4 }}
    """,
}


def _normalize(components: Mapping[str, str]) -> dict[str, str]:
    return {
        f"components/{name}.html": dedent(template).strip()
        for name, template in components.items()
    }


def render_component(
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


def _by_component(captures: list[dict[str, Any]], component: str) -> dict[str, Any]:
    for entry in captures:
        if entry.get("component") == component:
            return entry
    raise AssertionError(f"No capture for component {component!r}")


class TestHTMLContentBehaviour:
    def test_named_slots_are_captured(self) -> None:
        rendered, captures = render_component(
            """
            <include:card-with-footer title="Test Card">
                <p>Main content</p>
                <content:footer>Footer content</content:footer>
                <content:sidebar>Sidebar</content:sidebar>
            </include:card-with-footer>
            """
        )

        data = _by_component(captures, "card-with-footer")
        assert data["title"] == "Test Card"
        assert "Main content" in data["default"]
        assert data["footer"] == "Footer content"
        assert data["sidebar"] == "Sidebar"
        assert "<footer>Footer content</footer>" in rendered

    def test_old_and_new_content_syntax_mix(self) -> None:
        _, captures = render_component(
            """
            <include:card title="Mixed">
                Body text
                {% contents "oldstyle" %}Old style{% endcontents %}
                <content:newstyle>New style</content:newstyle>
            </include:card>
            """
        )

        data = _by_component(captures, "card")
        assert data["title"] == "Mixed"
        assert data["default"] == "Body text"
        assert data["oldstyle"] == "Old style"
        assert data["newstyle"] == "New style"

    def test_nested_components_preserve_named_content(self) -> None:
        _, captures = render_component(
            """
            <include:outer-card title="Outer">
                <content:main>
                    <include:inner-card title="Inner">
                        Inner body
                        <content:footer>Inner footer</content:footer>
                    </include:inner-card>
                </content:main>
                <content:footer>Outer footer</content:footer>
            </include:outer-card>
            """
        )

        outer = _by_component(captures, "outer-card")
        inner = _by_component(captures, "inner-card")
        assert "Inner body" in inner["body"]
        assert inner["footer"] == "Inner footer"
        assert "Inner body" in outer["main"]
        assert outer["footer"] == "Outer footer"

    def test_duplicate_named_blocks_last_wins(self) -> None:
        _, captures = render_component(
            """
            <include:card-with-footer title="Duplicates">
                <p>Original</p>
                <content:footer>First footer</content:footer>
                <content:footer>Second footer</content:footer>
            </include:card-with-footer>
            """
        )

        data = _by_component(captures, "card-with-footer")
        assert data["footer"] == "Second footer"

    def test_content_blocks_render_per_loop_iteration(self) -> None:
        _, captures = render_component(
            """
            {% for item in items %}
                <include:card title="{{ item.title }}">
                    {{ item.body }}
                    <content:newstyle>Item {{ loop.index }}</content:newstyle>
                </include:card>
            {% endfor %}
            """,
            context={"items": [{"title": "One", "body": "Body one"}, {"title": "Two", "body": "Body two"}]},
        )

        cards = [entry for entry in captures if entry.get("component") == "card"]
        assert [card["title"] for card in cards] == ["One", "Two"]
        assert [card["default"] for card in cards] == ["Body one", "Body two"]
        assert [card["newstyle"] for card in cards] == ["Item 1", "Item 2"]

    def test_missing_conditional_block_becomes_empty(self) -> None:
        _, captures = render_component(
            """
            <include:card title="Conditional">
                Always here
                {% if show_footer %}
                    <content:newstyle>Shown</content:newstyle>
                {% endif %}
            </include:card>
            """,
            context={"show_footer": False},
        )

        data = _by_component(captures, "card")
        assert data["newstyle"] == ""

    def test_deeply_nested_content_blocks(self) -> None:
        _, captures = render_component(
            """
            <include:level1>
                <content:section1>
                    <include:level2>
                        <content:section2>
                            <include:level3>
                                <content:section3>
                                    <include:level4>
                                        <content:section4>Deep value</content:section4>
                                    </include:level4>
                                </content:section3>
                            </include:level3>
                        </content:section2>
                    </include:level2>
                </content:section1>
            </include:level1>
            """
        )

        deepest = _by_component(captures, "level4")
        assert deepest["section4"] == "Deep value"

    def test_content_blocks_can_use_props(self) -> None:
        _, captures = render_component(
            """
            <include:card-with-props title="Props" variant="primary" size="lg">
                <content:body>Using Props and primary</content:body>
            </include:card-with-props>
            """
        )

        data = _by_component(captures, "card-with-props")
        assert data["variant"] == "primary"
        assert data["size"] == "lg"
        assert data["body"] == "Using Props and primary"


    def test_content_blocks_respect_component_attrs(self) -> None:
        _, captures = render_component(
            """
            <include:flexible-card class="custom-card" data-role="banner" title="Flexible">
                <content:header>Header text</content:header>
                Body copy
            </include:flexible-card>
            """
        )

        data = _by_component(captures, "flexible-card")
        assert data["attrs"] == {"class": "custom-card"}
        assert data["data_attrs"] == {"role": "banner"}
        assert data["header"] == "Header text"
        assert data["default"] == "Body copy"

class TestContentBlockEdgeCases:
    def test_duplicate_blocks_last_value_used(self) -> None:
        _, captures = render_component(
            """
            <include:card>
                Content
                <content:newstyle>First</content:newstyle>
                <content:newstyle>Last</content:newstyle>
            </include:card>
            """
        )

        data = _by_component(captures, "card")
        assert data["newstyle"] == "Last"

    def test_content_block_outside_component_renders_plainly(self) -> None:
        rendered, captures = render_component("<content:note>Loose content</content:note>")
        assert rendered.strip() == "Loose content"
        assert captures == []

    def test_empty_content_name_keeps_as_text(self) -> None:
        rendered, captures = render_component(
            "<include:card title='Blank'><content:>Empty</content:></include:card>"
        )
        data = _by_component(captures, "card")
        assert data["default"] == '<content:>Empty</content:>'
        assert '<content:>Empty</content:>' in rendered
