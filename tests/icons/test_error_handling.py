"""
Test that icon build failures fail loudly.
"""
import pytest
from unittest.mock import patch
from django.test import override_settings
from django.template import Context

from includecontents.django.base import Template as CustomTemplate
from includecontents.icons.builder import get_or_create_sprite
from includecontents.icons.finders import IconSpriteFinder


def test_invalid_icon_name_fails_loudly():
    """Test that invalid icon names cause loud failures during validation."""
    with override_settings(INCLUDECONTENTS_ICONS={
        'icons': ['invalid-icon-without-prefix'],  # Missing prefix like 'mdi:'
    }):
        with pytest.raises(ValueError) as exc_info:
            get_or_create_sprite()
        
        assert "Invalid INCLUDECONTENTS_ICONS configuration" in str(exc_info.value)
        assert "Invalid icon name" in str(exc_info.value)


def test_nonexistent_local_svg_fails_loudly():
    """Test that nonexistent local SVG files cause loud failures."""
    with override_settings(INCLUDECONTENTS_ICONS={
        'icons': ['icons/does-not-exist.svg'],
    }):
        with pytest.raises(RuntimeError) as exc_info:
            get_or_create_sprite()
        
        assert "Failed to build icon sprite" in str(exc_info.value)
        assert "not found" in str(exc_info.value.__cause__).lower()


@patch('includecontents.icons.builder.fetch_iconify_icons')
def test_iconify_api_failure_fails_loudly(mock_fetch):
    """Test that Iconify API failures cause loud failures."""
    mock_fetch.side_effect = Exception("API connection failed")
    
    with override_settings(INCLUDECONTENTS_ICONS={
        'icons': ['mdi:home'],
    }):
        with pytest.raises(RuntimeError) as exc_info:
            get_or_create_sprite()
        
        assert "Failed to build icon sprite" in str(exc_info.value)
        assert "API connection failed" in str(exc_info.value.__cause__)


def test_template_tag_propagates_build_errors():
    """Test that template tags let build errors bubble up."""
    with override_settings(INCLUDECONTENTS_ICONS={
        'icons': ['invalid-icon-without-prefix'],
    }):
        template_str = '{% icon "home" %}'
        template = CustomTemplate(template_str)
        
        # The template rendering should raise the validation error
        with pytest.raises(ValueError) as exc_info:
            template.render(Context())
        
        assert "Invalid INCLUDECONTENTS_ICONS configuration" in str(exc_info.value)


def test_collectstatic_fails_on_sprite_error():
    """Test that collectstatic fails loudly on sprite generation errors."""
    with override_settings(INCLUDECONTENTS_ICONS={
        'icons': ['invalid-icon-without-prefix'],
    }):
        finder = IconSpriteFinder()
        
        # The list() method should raise an error during collectstatic
        # The validation error gets wrapped in a RuntimeError
        with pytest.raises(RuntimeError) as exc_info:
            list(finder.list([]))
        
        assert "Failed to generate icon sprite during collectstatic" in str(exc_info.value)
        assert "Invalid INCLUDECONTENTS_ICONS configuration" in str(exc_info.value.__cause__)


@patch('includecontents.icons.builder.subprocess.run')
def test_optimization_command_failure_fails_loudly(mock_run):
    """Test that SVG optimization command failures cause loud failures."""
    # Mock a failed optimization command
    mock_run.return_value.returncode = 1
    mock_run.return_value.stdout = "Optimization failed"
    mock_run.return_value.stderr = "Invalid SVG"
    
    with override_settings(INCLUDECONTENTS_ICONS={
        'icons': [],  # Empty icons is valid
        'optimize_command': 'fake-optimizer --input={input} --output={output}',
    }):
        # Empty icons with optimization should still try to optimize the empty sprite
        # Since we have no icons, this won't actually run, so let's test with a direct build
        from includecontents.icons.builder import build_sprite
        
        with patch('includecontents.icons.builder.fetch_iconify_icons') as mock_fetch:
            mock_fetch.return_value = {'home': {'body': '<path/>', 'viewBox': '0 0 24 24'}}
            
            with pytest.raises(Exception) as exc_info:
                build_sprite(
                    ['mdi:home'],
                    optimize_command='fake-optimizer --input={input} --output={output}'
                )
            
            assert "returncode" in str(exc_info.value) or "CalledProcessError" in str(exc_info.type)