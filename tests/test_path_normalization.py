"""Test template path normalization fix."""

from dataclasses import dataclass
from pathlib import Path
from django.template import Context
from django.template.loader import render_to_string
import pytest

from includecontents.django.base import Template
from includecontents.props import component, get_props_class, _registry


@pytest.mark.django_db
class TestPathNormalization:
    """Test that template path normalization works correctly."""

    def setup_method(self):
        """Clear the registry before each test."""
        _registry.clear()

    def test_relative_registration_absolute_lookup_success(self):
        """Test that components registered with relative paths are found when looked up with absolute paths."""

        # Register a component with relative path (typical usage)
        @component('components/test-normalize.html')
        @dataclass
        class TestNormalizeProps:
            title: str
            description: str = "Default description"

        # Verify the registration worked
        assert get_props_class('components/test-normalize.html') is TestNormalizeProps

        # Create the component template
        component_content = """
{# props
title:str
description:str=Template default
#}
<div class="card">
    <h2>{{ title }}</h2>
    <p>{{ description }}</p>
</div>
"""

        # Create the test template that uses the component
        test_content = """<include:test-normalize title="Test Title" />"""

        # Write the template files
        template_dir = Path('tests/templates/components')
        template_dir.mkdir(parents=True, exist_ok=True)

        test_dir = Path('tests/templates/test_path_norm')
        test_dir.mkdir(parents=True, exist_ok=True)

        # Component template
        component_file = template_dir / 'test-normalize.html'
        component_file.write_text(component_content)

        # Test template
        test_file = test_dir / 'test.html'
        test_file.write_text(test_content)

        # Test that the component syntax finds the Python props class
        output = render_to_string("test_path_norm/test.html")

        # Should use Python props default, not template default
        assert "Test Title" in output
        assert "Default description" in output  # Python props default
        assert "Template default" not in output  # Should not use template-defined default

    def test_path_lookup_candidates_order(self):
        """Test that the path lookup tries candidates in the correct order."""

        # Register with relative path
        @component('components/priority-test.html')
        @dataclass
        class PriorityTestProps:
            message: str = "Python props used"

        # Create template with different default
        template_content = """
{# props
message:str=Template props used
#}
<div>{{ message }}</div>
"""

        template_dir = Path('tests/templates/components')
        template_dir.mkdir(parents=True, exist_ok=True)
        template_file = template_dir / 'priority-test.html'
        template_file.write_text(template_content)

        # Test that Python props take precedence
        template = Template("""
        {% load includecontents %}
        <include:priority-test />
        """)

        context = Context({})
        output = template.render(context)

        # Should use Python props, showing our path resolution worked
        assert "Python props used" in output
        assert "Template props used" not in output

    def test_fallback_behavior_still_works(self):
        """Test that fallback to template-defined props still works when no Python props are registered."""

        # Don't register any Python props
        # Create template with template-defined props only
        template_content = """
{# props
fallback_message:str="Fallback working"
#}
<div>{{ fallback_message }}</div>
"""

        template_dir = Path('tests/templates/components')
        template_dir.mkdir(parents=True, exist_ok=True)
        template_file = template_dir / 'fallback-test.html'
        template_file.write_text(template_content)

        # Test that template-defined props are used when no Python props exist
        template = Template("""
        {% load includecontents %}
        <include:fallback-test />
        """)

        context = Context({})
        output = template.render(context)

        # Should use template-defined props as fallback
        assert "Fallback working" in output

    def teardown_method(self):
        """Clean up test templates."""
        import shutil

        test_paths = [
            'tests/templates/components/test-normalize.html',
            'tests/templates/components/priority-test.html',
            'tests/templates/components/fallback-test.html',
            'tests/templates/test_path_norm'
        ]

        for test_path in test_paths:
            try:
                path = Path(test_path)
                if path.is_dir():
                    shutil.rmtree(path)
                else:
                    path.unlink()
            except FileNotFoundError:
                pass