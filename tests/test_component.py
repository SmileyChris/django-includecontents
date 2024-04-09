import re

import pytest
from django.template import TemplateSyntaxError
from django.template.loader import render_to_string


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


def test_attrs():
    assert render_to_string("test_component/attrs.html") == (
        """<main>
  <section id="topcard" class="mycard">
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
