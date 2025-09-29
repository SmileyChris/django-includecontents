"""
Tests for SVG cleaning functionality used in sprite generation.
"""

from includecontents.icons.builder import (
    parse_svg_content,
    clean_svg_for_sprite,
    is_drawing_element,
)
from xml.etree import ElementTree as ET


def test_is_drawing_element():
    """Test that is_drawing_element correctly identifies drawing elements."""
    # Test drawing elements
    drawing_elements = ["path", "g", "circle", "rect", "text", "linearGradient"]
    for tag in drawing_elements:
        elem = ET.Element(tag)
        assert is_drawing_element(elem) is True

    # Test non-drawing elements (defs is now considered a drawing element)
    non_drawing_elements = ["metadata", "sodipodi:namedview", "title", "desc"]
    for tag in non_drawing_elements:
        elem = ET.Element(tag)
        assert is_drawing_element(elem) is False

    # Test namespaced drawing elements (should work)
    elem = ET.Element("{http://www.w3.org/2000/svg}path")
    assert is_drawing_element(elem) is True


def test_clean_svg_for_sprite_removes_non_drawing_elements():
    """Test that clean_svg_for_sprite removes non-drawing elements."""
    # Create a root element with mixed children
    root = ET.Element("g")

    # Add drawing elements
    path = ET.SubElement(root, "path")
    path.set("d", "M10 10 L20 20")

    circle = ET.SubElement(root, "circle")
    circle.set("cx", "5")
    circle.set("cy", "5")
    circle.set("r", "3")

    # Add non-drawing elements
    metadata = ET.SubElement(root, "metadata")
    ET.SubElement(metadata, "rdf:RDF")

    namedview = ET.SubElement(root, "sodipodi:namedview")
    namedview.set("inkscape:window-height", "620")

    # Clean the element
    cleaned = clean_svg_for_sprite(root)

    # Check that drawing elements remain
    assert len(cleaned) == 2  # path and circle
    assert cleaned[0].tag == "path"
    assert cleaned[1].tag == "circle"

    # Check that non-drawing elements were removed
    tags = [child.tag for child in cleaned]
    assert "metadata" not in tags
    assert "sodipodi:namedview" not in tags


def test_clean_svg_for_sprite_removes_problematic_attributes():
    """Test that clean_svg_for_sprite removes problematic attributes."""
    elem = ET.Element("path")
    elem.set("d", "M10 10 L20 20")  # Essential attribute
    elem.set("width", "100")  # Should be removed
    elem.set("height", "100")  # Should be removed
    elem.set("style", "fill: red")  # Should be removed
    elem.set("class", "my-icon")  # Should be removed
    elem.set("id", "icon-1")  # Should be removed
    elem.set("fill", "currentColor")  # Should remain
    elem.set("stroke", "none")  # Should remain

    cleaned = clean_svg_for_sprite(elem)

    # Check that essential attributes remain
    assert cleaned.get("d") == "M10 10 L20 20"
    assert cleaned.get("fill") == "currentColor"
    assert cleaned.get("stroke") == "none"

    # Check that problematic attributes were removed
    assert cleaned.get("width") is None
    assert cleaned.get("height") is None
    assert cleaned.get("style") is None
    assert cleaned.get("class") is None
    assert cleaned.get("id") is None


def test_clean_svg_for_sprite_preserves_css_variable_styles():
    """Test that clean_svg_for_sprite preserves style attributes with CSS variables."""
    elem = ET.Element("path")
    elem.set("d", "M10 10 L20 20")
    elem.set("style", "fill: var(--icon-color)")  # Should be preserved
    elem.set("fill", "currentColor")

    cleaned = clean_svg_for_sprite(elem)

    # Check that CSS variable style is preserved
    assert cleaned.get("style") == "fill: var(--icon-color)"
    assert cleaned.get("d") == "M10 10 L20 20"
    assert cleaned.get("fill") == "currentColor"

    # Test with multiple CSS variables
    elem2 = ET.Element("g")
    elem2.set(
        "style", "transform: var(--icon-transform, none); fill: var(--icon-primary)"
    )

    cleaned2 = clean_svg_for_sprite(elem2)
    assert (
        cleaned2.get("style")
        == "transform: var(--icon-transform, none); fill: var(--icon-primary)"
    )

    # Test that regular styles without CSS variables are removed
    elem3 = ET.Element("circle")
    elem3.set("style", "fill: red; stroke: blue")  # Should be removed (no CSS vars)
    elem3.set("r", "10")

    cleaned3 = clean_svg_for_sprite(elem3)
    # Style without CSS variables is removed
    assert cleaned3.get("style") is None
    assert cleaned3.get("r") == "10"

    # Test mixed styles (CSS vars and regular)
    elem4 = ET.Element("rect")
    elem4.set(
        "style", "fill: var(--icon-bg); stroke: blue; transform: var(--icon-transform)"
    )
    elem4.set("width", "20")
    elem4.set("height", "20")

    cleaned4 = clean_svg_for_sprite(elem4)
    # Mixed styles with CSS variables should be preserved entirely
    assert (
        cleaned4.get("style")
        == "fill: var(--icon-bg); stroke: blue; transform: var(--icon-transform)"
    )
    # Problematic attributes should still be removed
    assert cleaned4.get("width") is None
    assert cleaned4.get("height") is None


def test_clean_svg_for_sprite_removes_namespaced_attributes():
    """Test that clean_svg_for_sprite removes namespaced attributes."""
    elem = ET.Element("path")
    elem.set("d", "M10 10 L20 20")
    elem.set("inkscape:connector-curvature", "0")
    elem.set("sodipodi:nodetypes", "ccc")
    elem.set("{http://namespace.com}custom", "value")

    cleaned = clean_svg_for_sprite(elem)

    # Check that path data remains
    assert cleaned.get("d") == "M10 10 L20 20"

    # Check that namespaced attributes were removed
    assert len(cleaned.attrib) == 1  # Only 'd' should remain


def test_parse_svg_content_with_metadata():
    """Test parsing SVG content with metadata and non-drawing elements."""
    svg_content = """
    <svg viewBox="0 0 24 24" width="24" height="24" 
         xmlns="http://www.w3.org/2000/svg"
         xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"
         xmlns:cc="http://creativecommons.org/ns#"
         xmlns:dc="http://purl.org/dc/elements/1.1/"
         xmlns:sodipodi="http://sodipodi.sourceforge.net/DTD/sodipodi-0.dtd"
         xmlns:inkscape="http://www.inkscape.org/namespaces/inkscape">
        <metadata id="metadata9">
            <rdf:RDF>
                <cc:Work rdf:about="">
                    <dc:format>image/svg+xml</dc:format>
                </cc:Work>
            </rdf:RDF>
        </metadata>
        <sodipodi:namedview inkscape:window-height="620" />
        <defs id="defs16" />
        <g id="g2161" transform="matrix(6.39,0,0,6.39,-22.6,-7.1)">
            <path id="path1" d="M10 10 L20 20" style="fill:red" />
            <path id="path2" d="M20 10 L10 20" />
        </g>
    </svg>
    """

    result = parse_svg_content(svg_content, "test.svg")

    # Check basic properties
    assert result["viewBox"] == "0 0 24 24"
    assert result["width"] == "24"
    assert result["height"] == "24"

    # Check that body contains only cleaned drawing elements
    body = result["body"]
    assert "<metadata" not in body
    assert "sodipodi:namedview" not in body
    # Note: defs is now kept as it's a drawing element (can contain gradients/filters)

    # Check that paths are present but cleaned (handle namespace prefixes)
    assert "path" in body
    assert 'd="M10 10 L20 20"' in body
    assert 'd="M20 10 L10 20"' in body

    # Check that problematic attributes were removed
    assert "style=" not in body
    assert "id=" not in body

    # Check that transform is preserved on g element
    assert 'transform="matrix(6.39,0,0,6.39,-22.6,-7.1)"' in body


def test_parse_svg_content_simple():
    """Test parsing simple SVG content."""
    svg_content = """
    <svg viewBox="0 0 100 100">
        <circle cx="50" cy="50" r="40" fill="red" />
    </svg>
    """

    result = parse_svg_content(svg_content, "test.svg")

    assert result["viewBox"] == "0 0 100 100"
    assert "circle" in result["body"]
    assert 'cx="50"' in result["body"]
    assert 'cy="50"' in result["body"]
    assert 'r="40"' in result["body"]
    assert 'fill="red"' in result["body"]


def test_parse_svg_content_with_only_non_drawing_elements():
    """Test parsing SVG with only non-drawing elements."""
    svg_content = """
    <svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
        <metadata>
            <title>My Icon</title>
        </metadata>
        <desc>Description</desc>
    </svg>
    """

    result = parse_svg_content(svg_content, "test.svg")

    # Should have empty body since no drawing elements
    # (or may have just empty string if cleaned properly)
    body = result["body"].strip()
    # The body should not contain any metadata, title, or desc elements
    assert "<metadata" not in body
    assert "<title" not in body
    assert "<desc" not in body
    assert result["viewBox"] == "0 0 24 24"


def test_parse_svg_content_preserves_gradients_and_filters():
    """Test that gradients and filters are preserved."""
    svg_content = """
    <svg viewBox="0 0 100 100">
        <defs>
            <linearGradient id="grad1" x1="0%" y1="0%" x2="100%" y2="0%">
                <stop offset="0%" style="stop-color:rgb(255,255,0);stop-opacity:1" />
                <stop offset="100%" style="stop-color:rgb(255,0,0);stop-opacity:1" />
            </linearGradient>
            <filter id="blur1">
                <feGaussianBlur in="SourceGraphic" stdDeviation="5" />
            </filter>
        </defs>
        <circle cx="50" cy="50" r="40" fill="url(#grad1)" filter="url(#blur1)" />
    </svg>
    """

    result = parse_svg_content(svg_content, "test.svg")

    body = result["body"]

    # Check that defs with content is preserved
    assert "defs" in body
    assert "linearGradient" in body
    assert "stop" in body
    assert "filter" in body
    assert "feGaussianBlur" in body

    # Check that circle is preserved with references
    assert "circle" in body
    assert 'fill="url(#grad1)"' in body
    assert 'filter="url(#blur1)"' in body

    # But IDs should be removed from elements
    assert 'id="grad1"' not in body
    assert 'id="blur1"' not in body
