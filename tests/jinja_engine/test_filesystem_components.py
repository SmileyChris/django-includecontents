"""Test Jinja2 components using filesystem templates."""

from __future__ import annotations

from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from includecontents.jinja2 import IncludeContentsExtension

# Path to test templates directory
TEMPLATES_DIR = Path(__file__).parent.parent / "templates"


def create_filesystem_jinja_env() -> Environment:
    """Create a Jinja environment with filesystem loader for testing."""
    loader = FileSystemLoader(TEMPLATES_DIR)
    return Environment(loader=loader, extensions=[IncludeContentsExtension])


def test_subdirectory_component_filesystem():
    """Test that subdirectory components work with filesystem templates."""
    env = create_filesystem_jinja_env()
    template = env.from_string('<include:inside:cat />')
    rendered = template.render()
    assert rendered.strip() == "Meow"


def test_multiple_subdirectory_components():
    """Test multiple calls to subdirectory components."""
    env = create_filesystem_jinja_env()
    template = env.from_string('''
    <div>
        First cat: <include:inside:cat />
        Second cat: <include:inside:cat />
    </div>
    ''')
    rendered = template.render()
    assert rendered.count("Meow") == 2


def test_regular_component_filesystem():
    """Test that regular components work with filesystem templates."""
    env = create_filesystem_jinja_env()
    template = env.from_string('<include:container>Hello World</include:container>')
    rendered = template.render()
    assert 'class="container"' in rendered
    assert "Hello World" in rendered


def test_mixed_regular_and_subdirectory_filesystem():
    """Test mixing regular and subdirectory components from filesystem."""
    env = create_filesystem_jinja_env()
    template = env.from_string('''
    <include:container>
        The cat says: <include:inside:cat />
    </include:container>
    ''')
    rendered = template.render()
    assert 'class="container"' in rendered
    assert "Meow" in rendered