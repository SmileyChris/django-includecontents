from django.template.loader import render_to_string


def test_attrs_spread_basic():
    """Test basic ...attrs spreading from parent to child component."""
    result = render_to_string("test_attrs_spread/basic.html")
    assert 'class="card"' in result
    assert 'id="parent-id"' in result
    assert 'data-value="123"' in result
    assert "Card content" in result


def test_attrs_spread_with_props():
    """Test ...attrs spreading with component props filtering."""
    result = render_to_string("test_attrs_spread/with_props.html")
    # title should be used as prop, not in attrs
    assert "<h2>My Title</h2>" in result
    # These should be in attrs
    assert 'class="custom-card"' in result
    assert 'data-id="456"' in result


def test_attrs_spread_precedence():
    """Test that local attrs take precedence over spread attrs."""
    result = render_to_string("test_attrs_spread/precedence.html")
    # Local class should override spread class
    assert 'class="local-class"' in result
    assert 'class="parent-class"' not in result
    # Other attrs from parent should still be there
    assert 'id="parent-id"' in result


def test_attrs_spread_nested():
    """Test ...attrs spreading in nested components."""
    result = render_to_string("test_attrs_spread/nested.html")
    # Attrs should flow through multiple levels
    assert 'data-root="true"' in result
    assert 'class="leaf-component"' in result


def test_attrs_spread_group():
    """Test ...attrs.group spreading."""
    result = render_to_string("test_attrs_spread/group.html")
    # The button should only get button.* attrs
    assert '<button type="submit" class="btn btn-primary">' in result
    # The form should get the data-form attr
    assert '<form data-form="true">' in result


def test_attrs_spread_empty():
    """Test ...attrs spreading when parent has no attrs."""
    result = render_to_string("test_attrs_spread/empty.html")
    # Should render without errors
    assert "No attrs content" in result
    # Should not have any extra attributes
    assert 'class=""' not in result
    assert 'id=""' not in result
