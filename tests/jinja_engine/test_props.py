from __future__ import annotations

import pytest
from jinja2.exceptions import TemplateRuntimeError

from ._helpers import first_capture, render_component


class TestEnumValidation:
    def test_required_enum_missing_raises(self) -> None:
        with pytest.raises(TemplateRuntimeError) as exc:
            render_component("<include:button>Click</include:button>", use=["button"])
        assert "missing required prop 'variant'" in str(exc.value)

    def test_invalid_enum_value_raises(self) -> None:
        with pytest.raises(TemplateRuntimeError) as exc:
            render_component(
                '<include:button variant="invalid">Click</include:button>',
                use=["button"],
            )
        message = str(exc.value)
        assert 'Invalid value "invalid"' in message
        assert 'attribute "variant"' in message

    def test_valid_enum_value_renders(self) -> None:
        _, captures = render_component(
            '<include:button variant="primary">Click</include:button>', use=["button"]
        )
        data = first_capture(captures, "button")
        assert data["variant"] == "primary"

    def test_optional_enum_defaults_empty(self) -> None:
        _, captures = render_component(
            "<include:button-optional>Click</include:button-optional>",
            use=["button-optional"],
        )
        data = first_capture(captures, "button-optional")
        assert not data["variant"]

    def test_optional_enum_accepts_value(self) -> None:
        _, captures = render_component(
            '<include:button-optional variant="dark-mode">Click</include:button-optional>',
            use=["button-optional"],
        )
        data = first_capture(captures, "button-optional")
        assert data["variant"] == "dark-mode"

    def test_multi_value_enum_sets_flags(self) -> None:
        _, captures = render_component(
            '<include:button-multi variant="primary icon">Click</include:button-multi>',
            use=["button-multi"],
        )
        data = first_capture(captures, "button-multi")
        assert data["variant"] == "primary icon"
        assert data["primary_flag"] is True
        assert data["icon_flag"] is True

    def test_multi_value_enum_invalid_value_raises(self) -> None:
        with pytest.raises(TemplateRuntimeError) as exc:
            render_component(
                '<include:button-multi variant="primary invalid">Click</include:button-multi>',
                use=["button-multi"],
            )
        assert 'Invalid value "invalid"' in str(exc.value)

    def test_enum_case_sensitive(self) -> None:
        with pytest.raises(TemplateRuntimeError) as exc:
            render_component(
                '<include:button variant="PRIMARY">Click</include:button>',
                use=["button"],
            )
        assert '"PRIMARY"' in str(exc.value)


class TestSpecialCharacterEnums:
    def test_special_character_value_allowed(self) -> None:
        _, captures = render_component(
            '<include:enum-edge-cases special="@">Content</include:enum-edge-cases>',
            use=["enum-edge-cases"],
        )
        data = first_capture(captures, "enum-edge-cases")
        assert data["special"] == "@"

    def test_invalid_special_character_rejected(self) -> None:
        with pytest.raises(TemplateRuntimeError) as exc:
            render_component(
                '<include:enum-edge-cases special="&">Invalid</include:enum-edge-cases>',
                use=["enum-edge-cases"],
            )
        assert "&" in str(exc.value)

    def test_numeric_enum_value(self) -> None:
        _, captures = render_component(
            '<include:enum-edge-cases numbers="1">Number</include:enum-edge-cases>',
            use=["enum-edge-cases"],
        )
        data = first_capture(captures, "enum-edge-cases")
        assert data["numbers"] == "1"

    def test_single_character_enum(self) -> None:
        _, captures = render_component(
            '<include:enum-edge-cases single="a">Single</include:enum-edge-cases>',
            use=["enum-edge-cases"],
        )
        data = first_capture(captures, "enum-edge-cases")
        assert data["single"] == "a"

    def test_mixed_enum_value(self) -> None:
        _, captures = render_component(
            '<include:enum-edge-cases mixed="test">Mixed</include:enum-edge-cases>',
            use=["enum-edge-cases"],
        )
        data = first_capture(captures, "enum-edge-cases")
        assert data["mixed"] == "test"

    def test_whitespace_enum_accepts_value(self) -> None:
        _, captures = render_component(
            '<include:enum-whitespace variant="b">Whitespace</include:enum-whitespace>',
            use=["enum-whitespace"],
        )
        data = first_capture(captures, "enum-whitespace")
        assert data["variant"] == "b"

    def test_whitespace_enum_rejects_invalid(self) -> None:
        with pytest.raises(TemplateRuntimeError):
            render_component(
                '<include:enum-whitespace variant="z">Bad</include:enum-whitespace>',
                use=["enum-whitespace"],
            )
