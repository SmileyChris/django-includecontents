"""Test Jinja2 components using filesystem templates."""

from __future__ import annotations

from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from includecontents.jinja2 import IncludeContentsExtension

# Path to test templates directory
TEMPLATES_DIR = Path(__file__).parent.parent / "templates"
TEMPLATES_DIR2 = Path(__file__).parent.parent / "templates2"


def create_filesystem_jinja_env() -> Environment:
    """Create a Jinja environment with filesystem loader for testing."""
    loader = FileSystemLoader(TEMPLATES_DIR)
    return Environment(loader=loader, extensions=[IncludeContentsExtension])


def create_multi_dir_jinja_env() -> Environment:
    """Create a Jinja environment with multiple template directories."""
    loader = FileSystemLoader([str(TEMPLATES_DIR), str(TEMPLATES_DIR2)])
    return Environment(loader=loader, extensions=[IncludeContentsExtension])


def test_subdirectory_component_filesystem():
    """Test that subdirectory components work with filesystem templates."""
    env = create_filesystem_jinja_env()
    template = env.from_string("<include:inside:cat />")
    rendered = template.render()
    assert rendered.strip() == "Meow"


def test_multiple_subdirectory_components():
    """Test multiple calls to subdirectory components."""
    env = create_filesystem_jinja_env()
    template = env.from_string("""
    <div>
        First cat: <include:inside:cat />
        Second cat: <include:inside:cat />
    </div>
    """)
    rendered = template.render()
    assert rendered.count("Meow") == 2


def test_regular_component_filesystem():
    """Test that regular components work with filesystem templates."""
    env = create_filesystem_jinja_env()
    template = env.from_string("<include:container>Hello World</include:container>")
    rendered = template.render()
    assert 'class="container"' in rendered
    assert "Hello World" in rendered


def test_mixed_regular_and_subdirectory_filesystem():
    """Test mixing regular and subdirectory components from filesystem."""
    env = create_filesystem_jinja_env()
    template = env.from_string("""
    <include:container>
        The cat says: <include:inside:cat />
    </include:container>
    """)
    rendered = template.render()
    assert 'class="container"' in rendered
    assert "Meow" in rendered


def test_multiple_template_directories():
    """Test that components can be resolved from multiple template directories."""
    env = create_multi_dir_jinja_env()

    # Test component from first directory (templates/components/container.html)
    template1 = env.from_string(
        "<include:container>Content from first dir</include:container>"
    )
    rendered1 = template1.render()
    assert 'class="container"' in rendered1
    assert "Content from first dir" in rendered1

    # Test component from second directory (templates2/components/cms/card.html)
    template2 = env.from_string(
        '<include:cms:card title="Test Card">Card content</include:cms:card>'
    )
    rendered2 = template2.render()
    assert 'class="cms-card' in rendered2
    assert "Test Card" in rendered2
    assert "Card content" in rendered2


def test_fallback_component_resolution():
    """Test that components fall back to other directories when not found in first."""
    env = create_multi_dir_jinja_env()

    # Component exists only in first directory
    template = env.from_string(
        "<include:fallback-component>Fallback test</include:fallback-component>"
    )
    rendered = template.render()
    assert 'class="fallback-component"' in rendered
    assert "Fallback: Fallback test" in rendered


def test_namespaced_component_resolution():
    """Test that namespaced components (cms:card) resolve to components/cms/card.html."""
    env = create_multi_dir_jinja_env()

    # Test cms:card resolves to components/cms/card.html
    template = env.from_string(
        '<include:cms:card title="CMS Card" variant="primary">CMS content</include:cms:card>'
    )
    rendered = template.render()

    # Check that it used the cms/card.html template
    assert 'class="cms-card cms-card--primary"' in rendered
    assert "CMS Card" in rendered
    assert "CMS content" in rendered


def test_namespaced_component_with_props():
    """Test that namespaced components work correctly with props."""
    env = create_multi_dir_jinja_env()

    # Test with different props
    template = env.from_string(
        '<include:cms:card variant="secondary">Secondary card</include:cms:card>'
    )
    rendered = template.render()

    # Should use default title and provided variant
    assert "Default Card" in rendered  # Default prop value
    assert "cms-card--secondary" in rendered  # Provided variant
    assert "Secondary card" in rendered


def test_basic_content_rendering():
    """Test that basic content rendering works with filesystem components."""
    env = create_filesystem_jinja_env()

    template = env.from_string("<include:content-test>incoming</include:content-test>")
    rendered = template.render()

    assert rendered.strip() == "<p>Testing: incoming</p>\n<p>Missing: </p>"
