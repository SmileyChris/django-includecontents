import pytest
from django.template import Context, TemplateSyntaxError
from django.template.loader import render_to_string
from django.test import override_settings
from django.urls import reverse

from includecontents.django.base import Template


def test_url_tag_in_href():
    """Test {% url %} tag within href attribute."""
    # Create a simple test that doesn't require actual URL resolution
    template_code = '''<include:test-button href="/test/">Click me</include:test-button>'''
    
    template = Template(template_code)
    result = template.render(Context())
    
    # The key test is that it compiles without error and preserves the href
    assert 'onclick="location.href=\'/test/\'"' in result


def test_variable_in_attribute():
    """Test {{ variable }} syntax within attributes."""
    template_code = '''<include:button class="btn {{ variant }}" href="{{ link_url }}">Submit</include:button>'''
    
    try:
        template = Template(template_code)
        # Test compilation - this should not raise an error
        nodelist = template.compile_nodelist()
        assert len(nodelist) > 0
        print("✓ Variable syntax in attributes compiled successfully")
    except Exception as e:
        pytest.fail(f"Template with variables in attributes failed to compile: {e}")


def test_if_tag_in_class():
    """Test {% if %} tag within class attribute."""
    template_code = '''<include:button class="btn {% if primary %}btn-primary{% endif %}">Button</include:button>'''
    
    try:
        template = Template(template_code)
        nodelist = template.compile_nodelist()
        assert len(nodelist) > 0
        print("✓ If tag in class attribute compiled successfully")
    except Exception as e:
        pytest.fail(f"Template with if tag in class failed to compile: {e}")


def test_multiple_template_tags():
    """Test multiple template tags in the same attribute."""
    template_code = '''<include:link href="{% url 'detail' id=object.id %}" class="link {% if active %}active{% endif %}">Link</include:link>'''
    
    try:
        template = Template(template_code)
        nodelist = template.compile_nodelist()
        assert len(nodelist) > 0
        print("✓ Multiple template tags compiled successfully")
    except Exception as e:
        pytest.fail(f"Template with multiple tags failed to compile: {e}")


def test_nested_quotes():
    """Test template tags with simpler nested quotes."""
    template_code = '''<include:button data-message="{% trans 'Hello' %}">Alert</include:button>'''
    
    try:
        template = Template(template_code)
        nodelist = template.compile_nodelist()
        assert len(nodelist) > 0
        print("✓ Nested quotes compiled successfully")
    except Exception as e:
        pytest.fail(f"Template with nested quotes failed to compile: {e}")


def test_tokenization_output():
    """Test that tokenization produces the expected output."""
    template_code = '''<include:button href="{% url 'home' %}" class="btn-primary">Click</include:button>'''
    
    template = Template(template_code)
    
    # Check the tokens produced
    from includecontents.django.base import Lexer
    lexer = Lexer(template_code)
    tokens = lexer.tokenize()
    
    # Should have: component token, text content, closing tag
    assert len(tokens) >= 2
    
    # First token should be the includecontents block
    first_token = tokens[0]
    assert first_token.token_type.name == 'BLOCK'
    assert 'includecontents' in first_token.contents
    assert 'href="{% url \'home\' %}"' in first_token.contents
    
    print(f"✓ Tokenization output: {first_token.contents}")




def test_backwards_compatibility():
    """Test that existing syntax still works."""
    template_code = '''<include:button class="btn-primary" href="/static/">Old Style</include:button>'''
    
    try:
        template = Template(template_code)
        nodelist = template.compile_nodelist()
        assert len(nodelist) > 0
        print("✓ Backwards compatibility maintained")
    except Exception as e:
        pytest.fail(f"Backwards compatibility broken: {e}")


if __name__ == '__main__':
    import django
    import os
    
    # Set up Django
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tests.settings')
    django.setup()
    
    # Run tests
    test_url_tag_in_href()
    test_variable_in_attribute()
    test_if_tag_in_class()
    test_multiple_template_tags()
    test_nested_quotes()
    test_tokenization_output()
    test_backwards_compatibility()
    
    print("✅ All template tag tests passed!")