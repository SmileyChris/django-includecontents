from django.template.loader import render_to_string


def test_basic():
    assert render_to_string("multiline.html") == "anon\n"
