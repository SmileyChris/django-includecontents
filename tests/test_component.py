import re

import pytest
from django.template import Context, TemplateSyntaxError
from django.template.loader import render_to_string
from django.test import override_settings

from includecontents.django.base import Template


def test_basic():
    assert render_to_string("test_component/index.html") == (
        """<main>
  <section class="card">
  <h3 >hello</h3>
  <div>some content</div>
</section>
</main>
"""
    )


@override_settings(DEBUG=True)
def test_debug_mode():
    render_to_string("test_component/index.html")


def test_attrs():
    assert render_to_string("test_component/attrs.html") == (
        """<main>
  <section class="mycard" id="topcard" x-data>
  <h3 class="large">hello</h3>
  <div>
    some content
  </div>
</section>
</main>
"""
    )


def test_missing_attr():
    with pytest.raises(
        TemplateSyntaxError,
        match='Missing required attribute "title" in <include:card>',
    ):
        render_to_string("test_component/missing_attr.html")


def test_missing_closing_tag():
    with pytest.raises(
        TemplateSyntaxError,
        match=re.compile(r"Unclosed tag.*<include:card>.*</include:card>"),
    ):
        render_to_string("test_component/missing_closing_tag.html")


def test_extend_class():
    assert render_to_string("test_component/extend_class.html") == (
        """<main>
  <section class="mycard card lg">
  <h3 >hello</h3>
  <div>
    some content
  </div>
</section>
</main>
"""
    )

    assert render_to_string("test_component/extend_class.html", {"red": True}) == (
        """<main>
  <section class="mycard card lg">
  <h3 class="text-red">hello</h3>
  <div>
    some content
  </div>
</section>
</main>
"""
    )


def test_empty_props():
    output = Template(
        "Attrs: <include:empty-props id='1' hello></include:empty-props>"
    ).render(Context())
    assert output == 'Attrs: id="1" hello/'


def test_only_advanced_props():
    output = Template(
        "Attrs: <include:empty-props inner.id='1'></include:empty-props>"
    ).render(Context())
    assert output == 'Attrs: /id="1"'


def test_nested_attrs():
    output = Template(
        "<include:nested-attrs inner.class='2' class='1'></include:nested-attrs>"
    ).render(Context())
    assert (
        output
        == """\
<div class="1 main"></div>
<div class="2 inner"></div>"""
    )


def test_self_closing():
    output = Template("Attrs: <include:empty-props hello />").render(Context())
    assert output == "Attrs: hello/"


def test_kebab_props():
    output = Template(
        "Attrs: "
        '<include:empty-props x-data="{foo: bar}" inner.hx-swap="innerHTML">'
        "</include:empty-props>"
    ).render(Context())
    assert output == 'Attrs: x-data="{foo: bar}"/hx-swap="innerHTML"'


def test_safe_constants():
    output = Template(
        """<include:escape-props test="2>1" another="3>2"></include:escape-props>"""
    ).render(Context())
    assert output == 'test="2>1" another="3>2"'


def test_safe_constants_fallback():
    output = Template("""<include:escape-props></include:escape-props>""").render(
        Context()
    )
    assert output == 'test="5>4"'


def test_escape_variables():
    output = Template(
        """<include:escape-props test=somevar another="3>2"></include:escape-props>"""
    ).render(Context({"somevar": '2>1"'}))
    assert output == 'test="2&gt;1&quot;" another="3>2"'


def test_subdir():
    output = Template("<include:inside:cat />").render(Context())
    assert output == "Meow"


def test_template_caching(mocker):
    template = Template("""
{% for i in '12345'|make_list %}
    <include:empty-props i={i} />
{% endfor %}
""")
    context = Context()
    context.bind_template(template)
    spy = mocker.spy(template.engine, "select_template")

    template.render(context)
    assert spy.call_count == 1


def test_context_passthrough():
    output = Template("""<include:context food="fries" />""").render(
        Context({"food": "fries"})
    )
    assert output == "fries"
    output = Template("""<include:context food={food} />""").render(
        Context({"food": "sushi"})
    )
    assert output == "sushi"
    output = Template("""<include:context />""").render(Context({"food": "pizza"}))
    assert output == ""


def test_shorthand_attrs():
    output = Template("""<include:context {food} />""").render(
        Context({"food": "pizza"})
    )
    assert output == "pizza"


def test_shorthand_required_attrs():
    output = Template("""<include:card {title} />""").render(
        Context({"title": "hello"})
    )
    assert (
        output
        == """\
<section class="card">
  <h3 >hello</h3>
  <div></div>
</section>"""
    )


def test_multi():
    output = render_to_string("test_component/multi.html")
    assert output == (
        """<main>
  <section class="card">
  <h3 >hello</h3>
  <div>Title</div>
</section>
  
    <section class="card">
  <h3 >1</h3>
  <div>loop 1</div>
</section>
  
    <section class="card">
  <h3 >2</h3>
  <div>loop 2</div>
</section>
  
    <section class="card">
  <h3 >3</h3>
  <div>loop 3</div>
</section>
  
</main>
"""
    )


def test_new_attr_syntax():
    output = render_to_string(
        "test_component/new_attr_syntax.html", {"myTitle": "Hello World"}
    )
    assert output == (
        """<main>
  <section class="mycard">
  <h3 >Hello World</h3>
  <div>
    content with new syntax
  </div>
</section>
  <section class="mycard">
  <h3 >hello world</h3>
  <div>
    content with new syntax unquoted
  </div>
</section>
  <section class="mycard">
  <h3 >Hello World</h3>
  <div>
    content with old syntax
  </div>
</section>
</main>
"""
    )


def test_html_content_syntax():
    """Test the new <content:name> HTML syntax for named content blocks."""
    output = render_to_string("test_component/html_content.html")
    assert output == (
        """<main>
  <section class="card">
  <h3>Test Card</h3>
  <div class="content">
    <p>Main content</p>
    
    
  </div>
  
  <footer class="footer">Footer content</footer>
  
  
  <aside class="sidebar">Sidebar content</aside>
  
</section>
</main>"""
    )


def test_mixed_content_syntax():
    """Test mixing old {% contents %} and new <content:name> syntax."""
    output = render_to_string("test_component/mixed_content.html")
    assert output == (
        """<main>
  <section class="card">
  <h3>Mixed Syntax</h3>
  <div class="content">
    <p>Main content</p>
    
    
  </div>
  
  <div class="oldstyle">Old style content</div>
  
  
  <div class="newstyle">New style content</div>
  
</section>
</main>"""
    )


def test_html_content_empty():
    """Test HTML content syntax with empty named blocks."""
    output = Template(
        """<include:card-with-footer title="Empty">
  <p>Just main content</p>
</include:card-with-footer>"""
    ).render(Context())
    assert output == (
        """<section class="card">
  <h3>Empty</h3>
  <div class="content">
  <p>Just main content</p>
</div>
  
  
</section>"""
    )


def test_html_content_only_named():
    """Test HTML content syntax with only named blocks and no main content."""
    output = Template(
        """<include:card-with-footer title="Only Named">
  <content:footer>Just footer</content:footer>
</include:card-with-footer>"""
    ).render(Context())
    assert output == (
        """<section class="card">
  <h3>Only Named</h3>
  <div class="content"></div>
  
  <footer class="footer">Just footer</footer>
  
  
</section>"""
    )


def test_html_content_with_variables():
    """Test HTML content syntax with template variables."""
    output = Template(
        """<include:card-with-footer title="Variables">
  <p>Hello {{ name }}!</p>
  <content:footer>Copyright {{ year }}</content:footer>
</include:card-with-footer>"""
    ).render(Context({"name": "World", "year": 2024}))
    assert output == (
        """<section class="card">
  <h3>Variables</h3>
  <div class="content">
  <p>Hello World!</p>
  
</div>
  
  <footer class="footer">Copyright 2024</footer>
  
  
</section>"""
    )


def test_html_content_multiline():
    """Test HTML content syntax with multiline content."""
    output = Template(
        """<include:card-with-footer title="Multiline">
  <content:footer>
    <p>Line 1</p>
    <p>Line 2</p>
  </content:footer>
</include:card-with-footer>"""
    ).render(Context())
    assert output == (
        """<section class="card">
  <h3>Multiline</h3>
  <div class="content"></div>
  
  <footer class="footer">
    <p>Line 1</p>
    <p>Line 2</p>
  </footer>
  
  
</section>"""
    )


def test_class_negation():
    """Test class: attribute with negation using 'not' syntax."""
    # Test with disabled=True (should NOT include 'active' class)
    output = render_to_string("test_component/class_negation.html", {"disabled": True})
    assert output == (
        """<main>
  <section class="mycard card">
  <h3 >hello</h3>
  <div>
    some content
  </div>
</section>
</main>"""
    )

    # Test with disabled=False (should include 'active' class)
    output = render_to_string("test_component/class_negation.html", {"disabled": False})
    assert output == (
        """<main>
  <section class="mycard card active">
  <h3 >hello</h3>
  <div>
    some content
  </div>
</section>
</main>"""
    )


def test_class_append():
    """Test class attribute appending with '& ' syntax."""
    output = Template(
        """<include:card-extend title="Append Test" class="user-class" />"""
    ).render(Context())
    assert output == (
        """<section class="user-class card">
  <h3 >Append Test</h3>
  <div></div>
</section>"""
    )


def test_class_prepend():
    """Test class attribute prepending with ' &' syntax."""
    output = Template(
        """<include:card-prepend title="Prepend Test" class="user-class" />"""
    ).render(Context())
    assert output == (
        """<section class="card-base user-class">
  <h3>Prepend Test</h3>
  <div></div>
</section>"""
    )
