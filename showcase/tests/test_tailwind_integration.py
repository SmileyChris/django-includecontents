"""
Basic tests for Tailwind design token integration.
"""

import pytest
from pathlib import Path
from ..parsers import CSSThemeParser, TailwindConfigParser


class TestCSSThemeParser:
    """Test CSS @theme directive parsing."""

    def test_basic_theme_parsing(self):
        """Test parsing basic @theme block."""
        parser = CSSThemeParser()
        css_content = """
        @theme {
          --color-primary: #3b82f6;
          --spacing-md: 1rem;
        }
        """

        tokens = parser.parse(css_content)

        assert len(tokens) == 2
        assert any('primary' in t.path for t in tokens)
        assert any(t.value == '#3b82f6' for t in tokens)


class TestTailwindConfigParser:
    """Test Tailwind config file parsing."""

    def test_basic_config_parsing(self):
        """Test parsing module.exports config."""
        parser = TailwindConfigParser()
        js_content = """
        module.exports = {
          theme: {
            colors: {
              primary: '#3b82f6'
            }
          }
        }
        """

        tokens = parser.parse(js_content)

        assert len(tokens) >= 1
        assert any(t.value == '#3b82f6' for t in tokens)


def test_integration_workflow():
    """Test basic integration workflow."""
    # Test that both parsers can be imported and instantiated
    css_parser = CSSThemeParser()
    js_parser = TailwindConfigParser()

    assert css_parser is not None
    assert js_parser is not None

    # Test basic parsing
    css_tokens = css_parser.parse('@theme { --test: #000; }')
    js_tokens = js_parser.parse('module.exports = { theme: { colors: { test: "#fff" } } }')

    assert len(css_tokens) >= 1
    assert len(js_tokens) >= 1