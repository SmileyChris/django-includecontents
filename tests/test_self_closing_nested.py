import pytest
from django.template import Context

from includecontents.django.base import Template


def test_self_closing_basic():
    """Test that basic self-closing tags work correctly."""
    output = Template('<include:card title="Self-closing test" />').render(Context())
    assert (
        output
        == """<section class="card">
  <h3 >Self-closing test</h3>
  <div></div>
</section>"""
    )


def test_self_closing_within_nested_components():
    """Test self-closing tags within nested components."""
    output = Template("""
<include:container>
    <h2>Container with self-closing components</h2>
    <include:card title="Card 1" />
    <include:card title="Card 2" />
</include:container>
""").render(Context())

    assert "Card 1" in output
    assert "Card 2" in output
    assert output.count('<section class="card">') == 2


def test_mixed_self_closing_and_content_blocks():
    """Test mixed self-closing and regular components with content blocks."""
    output = Template("""
<include:container>
    <include:card title="Self-closing 1" />
    <include:item>
        <content:info>Content block info</content:info>
    </include:item>
    <include:card title="Self-closing 2" />
</include:container>
""").render(Context())

    assert "Self-closing 1" in output
    assert "Self-closing 2" in output
    assert "Content block info" in output


def test_deeply_nested_with_self_closing():
    """Test deeply nested components with self-closing tags."""
    output = Template("""
<include:container>
    <include:item>
        <content:info>Outer info</content:info>
        <include:card title="Nested self-closing" />
    </include:item>
</include:container>
""").render(Context())

    assert "Outer info" in output
    assert "Nested self-closing" in output


def test_self_closing_with_advanced_attrs():
    """Test self-closing tags with advanced attributes."""
    output = Template(
        '<include:empty-props inner.id="test123" class="my-class" />'
    ).render(Context())
    assert output == 'class="my-class"/id="test123"'


def test_multiple_self_closing_same_component():
    """Test multiple self-closing instances of the same component."""
    template = Template("""
<include:container>
    <content:header>Main Header</content:header>
    <include:card title="First" />
    <include:card title="Second" />
    <include:card title="Third" />
</include:container>
""")
    output = template.render(Context())

    assert "Main Header" in output
    assert "First" in output
    assert "Second" in output
    assert "Third" in output
    assert output.count('<section class="card">') == 3


def test_self_closing_edge_cases():
    """Test edge cases with self-closing tags."""
    # Self-closing with boolean attributes
    output = Template("<include:empty-props disabled />").render(Context())
    assert output == "disabled/"

    # Self-closing with template variables
    output = Template('<include:card title="{{ title }}" />').render(
        Context({"title": "Dynamic Title"})
    )
    assert "Dynamic Title" in output

    # Self-closing with shorthand syntax
    output = Template("<include:card {title} />").render(
        Context({"title": "Shorthand Title"})
    )
    assert "Shorthand Title" in output


def test_self_closing_parsing_consistency():
    """Verify that self-closing tags are parsed consistently."""
    from django.template.base import TokenType

    from includecontents.django.base import Lexer as CustomLexer

    # Test that get_contents_nodelists properly handles self-closing tags
    template_str = '<include:card title="Test" />'
    lexer = CustomLexer(template_str)
    tokens = lexer.tokenize()

    # Find the token that represents the self-closing tag
    for token in tokens:
        if token.token_type == TokenType.BLOCK and "_include:card/" in token.contents:
            # This should be detected as self-closing
            bits = token.split_contents()
            assert len(bits) >= 2
            assert bits[1] == "_include:card/"
            assert bits[1].endswith("/")
            break
    else:
        pytest.fail("Self-closing tag token not found")
