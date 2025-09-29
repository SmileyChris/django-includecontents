from __future__ import annotations

from ._helpers import captures_for, first_capture, render_component


class TestHTMLContentBehaviour:
    def test_named_slots_are_captured(self) -> None:
        rendered, captures = render_component(
            """
            <include:card-with-footer title="Test Card">
                <p>Main content</p>
                <content:footer>Footer content</content:footer>
                <content:sidebar>Sidebar</content:sidebar>
            </include:card-with-footer>
            """,
            use=["card-with-footer"],
        )

        data = first_capture(captures, "card-with-footer")
        assert data["title"] == "Test Card"
        assert data["default"].strip() == "<p>Main content</p>"
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
            """,
            use=["card"],
        )

        data = first_capture(captures, "card")
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
            """,
            use=["outer-card", "inner-card"],
        )

        outer = first_capture(captures, "outer-card")
        inner = first_capture(captures, "inner-card")
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
            """,
            use=["card-with-footer"],
        )

        data = first_capture(captures, "card-with-footer")
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
            use=["card"],
            context={
                "items": [
                    {"title": "One", "body": "Body one"},
                    {"title": "Two", "body": "Body two"},
                ]
            },
        )

        cards = captures_for(captures, "card")
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
            use=["card"],
            context={"show_footer": False},
        )

        data = first_capture(captures, "card")
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
                                        Deep value
                                    </include:level4>
                                </content:section3>
                            </include:level3>
                        </content:section2>
                    </include:level2>
                </content:section1>
            </include:level1>
            """,
            use=["level1", "level2", "level3", "level4"],
        )

        deepest = first_capture(captures, "level4")
        assert deepest["payload"] == "Deep value"

    def test_content_blocks_can_use_props(self) -> None:
        _, captures = render_component(
            """
            <include:card-with-props title="Props" variant="primary" size="lg">
                <content:body>
                    Using Props and primary
                </content:body>
            </include:card-with-props>
            """,
            use=["card-with-props"],
        )

        data = first_capture(captures, "card-with-props")
        assert data["variant"] == "primary"
        assert data["size"] == "lg"
        assert "Using Props and primary" in data["body"]

    def test_content_blocks_respect_component_attrs(self) -> None:
        _, captures = render_component(
            """
            <include:flexible-card class="custom-card" data-role="banner" title="Flexible">
                <content:header>Header text</content:header>
                Body copy
            </include:flexible-card>
            """,
            use=["flexible-card"],
        )

        data = first_capture(captures, "flexible-card")
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
            """,
            use=["card"],
        )

        data = first_capture(captures, "card")
        assert data["newstyle"] == "Last"

    def test_content_block_outside_component_renders_plainly(self) -> None:
        rendered, captures = render_component(
            "<content:note>Loose content</content:note>"
        )
        assert rendered.strip() == "Loose content"
        assert captures == []

    def test_empty_content_name_keeps_as_text(self) -> None:
        rendered, captures = render_component(
            "<include:card title='Blank'><content:>Empty</content:></include:card>",
            use=["card"],
        )
        data = first_capture(captures, "card")
        assert data["default"] == "<content:>Empty</content:>"
        assert "<content:>Empty</content:>" in rendered
