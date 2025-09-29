from __future__ import annotations

from ._helpers import captures_for, first_capture, render_component

LEVEL_COMPONENTS = [f"level{i}" for i in range(1, 11)]


class TestNestedComponentScenarios:
    def test_deeply_nested_components_emit_all_levels(self) -> None:
        _, captures = render_component(
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
            """,
            use=LEVEL_COMPONENTS,
        )

        levels = {entry["level"] for entry in captures_for(captures, "level10")}
        assert levels == {10}
        all_levels = sorted(entry["level"] for entry in captures if entry.get("level"))
        assert all_levels == list(range(1, 11))

    def test_many_sibling_components_record_individual_data(self) -> None:
        template_parts = [
            f'<include:section name="section-{i}">Content {i}</include:section>'
            for i in range(20)
        ]
        _, captures = render_component("\n".join(template_parts), use=["section"])

        sections = captures_for(captures, "section")
        assert len(sections) == 20
        assert sections[0]["body"] == "Content 0"
        assert sections[-1]["name"] == "section-19"


class TestAttributeAndContentComplexity:
    def test_complex_attribute_normalization(self) -> None:
        _, captures = render_component(
            """
            <include:complex-component
                class="btn primary"
                data-role="cta"
                inner.class="inner"
                inner.data-id="nested-42"
            >Payload</include:complex-component>
            """,
            use=["complex-component"],
        )

        data = first_capture(captures, "complex-component")
        assert data["attrs"]["class"] == "btn primary"
        assert data["inner"] == {"class": "inner"}
        assert data["inner_data"] == {"id": "nested-42"}

    def test_many_named_content_blocks(self) -> None:
        blocks = [f"<content:slot-{i}>Value {i}</content:slot-{i}>" for i in range(5)]
        _, captures = render_component(
            f"""
            <include:container>
                {" ".join(blocks)}
            </include:container>
            """,
            use=["container"],
        )

        entries = captures_for(captures, "container")
        slots = {
            entry["slot"]: entry["value"]
            for entry in entries
            if entry["slot"] is not None
        }
        assert slots["slot-0"] == "Value 0"
        assert slots["slot-4"] == "Value 4"


class TestRenderingScenarios:
    def test_simple_button_render(self) -> None:
        rendered, captures = render_component(
            """
            <include:simple-button variant="primary" size="large">Click</include:simple-button>
            """,
            use=["simple-button"],
        )

        data = first_capture(captures, "simple-button")
        assert data["variant"] == "primary"
        assert data["size"] == "large"
        assert data["text"] == "Click"
        assert "btn-primary" in rendered

    def test_nested_button_in_container(self) -> None:
        rendered, captures = render_component(
            """
            <include:container>
                <include:simple-button variant="secondary" size="small">Press</include:simple-button>
            </include:container>
            """,
            use=["container", "simple-button"],
        )

        container_entries = captures_for(captures, "container")
        default_entry = next(
            entry for entry in container_entries if entry["slot"] is None
        )
        button = first_capture(captures, "simple-button")
        assert "Press" in default_entry["value"]
        assert button["variant"] == "secondary"
        assert "btn-secondary" in rendered
