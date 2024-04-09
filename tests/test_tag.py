from django.template.loader import render_to_string


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
