from django.template.loader import render_to_string


def test_basic():
    assert render_to_string("multiline.html") == "anon\n"


def test_multiline_closing_tag():
    result = render_to_string("multiline_closing_tag.html")
    assert '<div class="item">' in result
    assert "Test content" in result


def test_multiline_content_closing_tag():
    result = render_to_string("multiline_content_closing_tag.html")
    assert '<div class="card">' in result
    assert '<div class="card-title">Test Title</div>' in result
    assert '<div class="card-body">' in result
    assert 'Main content' in result
