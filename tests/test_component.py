import re

import pytest
from django.template import TemplateSyntaxError
from django.template.loader import render_to_string


def test_basic():
    assert render_to_string("index.html") == (
        """<main>
  <section class="card">
  <h3>hello</h3>
  <div>some content</div>
</section>
</main>
"""
    )


def test_attrs():
    assert render_to_string("attrs.html") == (
        """<main>
  <section class="mycard">
  <h3>hello</h3>
  <div>some content</div>
</section>
</main>
"""
    )


def test_missing_attr():
    with pytest.raises(
        TemplateSyntaxError, match="Missing required attribute in <Card>: title"
    ):
        render_to_string("missing_attr.html")


def test_missing_closing_tag():
    with pytest.raises(
        TemplateSyntaxError, match=re.compile(r"Unclosed tag.*<Card>.*</Card>")
    ):
        render_to_string("missing_closing_tag.html")
