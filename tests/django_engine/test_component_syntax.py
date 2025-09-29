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


def test_hardcoded_string_attributes():
    output = Template(
        """<include:escape-props test="Don't worry" another='Say "hello"'></include:escape-props>"""
    ).render(Context())
    assert output == 'test="Don\'t worry" another="Say "hello""'


def test_variable_content_escaping():
    output = Template(
        """<include:escape-props test=quote_var another=apostrophe_var></include:escape-props>"""
    ).render(Context({"quote_var": 'Say "hello"', "apostrophe_var": "Don't worry"}))
    assert output == 'test="Say &quot;hello&quot;" another="Don&#x27;t worry"'


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


def test_javascript_event_attributes():
    """Test various JavaScript framework event attributes like @click, v-on:, x-on:, and :bind."""
    # Test single @click attribute
    output = Template("""<include:empty-props @click="handleClick()" />""").render(
        Context()
    )
    assert output == '@click="handleClick()"/'

    # Test Vue.js v-on: syntax with colons (needs special handling)
    output = Template("""<include:empty-props v-on:submit="onSubmit" />""").render(
        Context()
    )
    assert output == 'v-on:submit="onSubmit"/'

    # Test Alpine.js x-on: syntax
    output = Template("""<include:empty-props x-on:click="open = !open" />""").render(
        Context()
    )
    assert output == 'x-on:click="open = !open"/'

    # Test Alpine.js :bind shorthand
    output = Template(
        """<include:empty-props :class="{ 'active': isActive }" />"""
    ).render(Context())
    assert output == ":class=\"{ 'active': isActive }\"/"

    # Test combined attributes
    output = Template(
        """<include:empty-props @click="handleClick()" :disabled="isDisabled" v-model="value" />"""
    ).render(Context())
    assert output == '@click="handleClick()" :disabled="isDisabled" v-model="value"/'

    # Test with inner attributes
    output = Template(
        """<include:empty-props @click="outerClick()" inner.@click="innerClick()" inner.:disabled="isDisabled" />"""
    ).render(Context())
    assert (
        output == '@click="outerClick()"/@click="innerClick()" :disabled="isDisabled"'
    )

    # Test Vue.js event modifiers like @click.stop
    output = Template("""<include:empty-props @click.stop="handleClick()" />""").render(
        Context()
    )
    assert output == '@click.stop="handleClick()"/'

    # Test multiple Vue.js event modifiers
    output = Template(
        """<include:empty-props @click.stop.prevent="handleClick()" />"""
    ).render(Context())
    assert output == '@click.stop.prevent="handleClick()"/'

    # Test Vue.js keyup modifiers
    output = Template(
        """<include:empty-props @keyup.enter="handleEnter()" />"""
    ).render(Context())
    assert output == '@keyup.enter="handleEnter()"/'


def test_template_variables_in_component_attributes():
    """Test template variable support in component attributes."""
    # Test 1: Simple variable (works)
    output = Template('<include:empty-props data-id="{{ myid }}" />').render(
        Context({"myid": "123"})
    )
    assert output == 'data-id="123"/'

    # Test 2: Variable with filter (works)
    output = Template('<include:empty-props data-count="{{ count|add:1 }}" />').render(
        Context({"count": 5})
    )
    assert output == 'data-count="6"/'

    # Test 3: Filter with single quotes (works when entire value is template var)
    output = Template(
        """<include:empty-props title="{{ name|default:'Untitled' }}" />"""
    ).render(Context({"name": ""}))
    assert output == 'title="Untitled"/'

    # Test 4: yesno filter (works when entire value is template var)
    output = Template(
        """<include:empty-props active="{{ is_active|yesno:'true,false' }}" />"""
    ).render(Context({"is_active": True}))
    assert output == 'active="true"/'


def test_mixed_content_in_attributes():
    """Test mixed static text and template variables in attributes."""
    # Test 1: Mixed content with variable
    output = Template("""<include:empty-props class="btn {{ variant }}" />""").render(
        Context({"variant": "primary"})
    )
    assert output == 'class="btn primary"/'

    # Test 2: Mixed content with multiple variables
    output = Template(
        """<include:empty-props data-info="Count: {{ count }} of {{ total }}" />"""
    ).render(Context({"count": 5, "total": 10}))
    assert output == 'data-info="Count: 5 of 10"/'

    # Test 3: Mixed content with filter
    output = Template(
        """<include:empty-props class="btn btn-{{ size|default:'medium' }}" />"""
    ).render(Context({"size": "large"}))
    assert output == 'class="btn btn-large"/'

    # Test 4: URL-like pattern
    output = Template(
        """<include:empty-props href="/products/{{ product_id }}/" />"""
    ).render(Context({"product_id": 123}))
    assert output == 'href="/products/123/"/'

    # Test 5: Block tags in mixed content (should now work!)
    output = Template(
        """<include:empty-props class="btn {% if active %}active{% endif %}" />"""
    ).render(Context({"active": True}))
    assert output == 'class="btn active"/'

    # Test 6: For loop in attribute
    output = Template(
        """<include:empty-props data-items="{% for i in items %}{{ i }}{% if not forloop.last %},{% endif %}{% endfor %}" />"""
    ).render(Context({"items": ["a", "b", "c"]}))
    assert output == 'data-items="a,b,c"/'
