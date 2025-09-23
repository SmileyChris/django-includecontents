import pytest
from django.template.loader import render_to_string

from includecontents.templatetags.includecontents import Attrs


def test_basic():
    assert render_to_string("test_tag/basic.html") == (
        """<div class="outer">
  <div class="inner" id="">
    inner content
  </div>

</div>
"""
    )


def test_with_attr():
    assert render_to_string("test_tag/with_attr.html", {"inner_id": "hello"}) == (
        """<div class="outer">
  <div class="inner" id="hello">
    inner content
  </div>

</div>
"""
    )


def test_attrs_class():
    attrs = Attrs()
    attrs.update({"test": 1, "me-out": 2})
    # Unknown keys raise KeyError
    with pytest.raises(KeyError):
        attrs["unknown"]
    # Basic lookup works
    assert attrs["test"] == 1
    # Kebab case works
    assert attrs["me-out"] == 2
    # Camel case is converted to kebab case
    assert attrs["meOut"] == 2
    assert attrs["MeOut"] == 2


def test_context():
    assert render_to_string("test_tag/basic.html", {"id": "seen"}) == (
        """<div class="outer">
  <div class="inner" id="seen">
    inner content
  </div>

</div>
"""
    )


def test_context_only():
    assert render_to_string("test_tag/basic_only.html", {"id": "unseen"}) == (
        """<div class="outer">
  <div class="inner" id="">
    inner content
  </div>

</div>
"""
    )
