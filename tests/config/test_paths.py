"""
Test that icon finder and template tags respect configurable storage location.
"""
import pytest
from unittest.mock import patch
from django.test import override_settings
from django.template import Context

from includecontents.django.base import Template as CustomTemplate
from includecontents.icons.finders import IconSpriteFinder


def mock_iconify_fetch():
    """Mock function that handles iconify fetches for tests."""
    def mock_fetch_fn(prefix, icon_names, api_base):
        if prefix == 'mdi':
            return {'home': {'body': '<path d="M10 10"/>', 'viewBox': '0 0 24 24'}}
        return {}
    return mock_fetch_fn


@override_settings(INCLUDECONTENTS_ICONS={
    'icons': [('home', 'mdi:home')],
    'storage': 'includecontents.icons.storages.MemoryIconStorage',
    'storage_options': {'location': 'custom-sprites/'}
})
@patch('includecontents.icons.builder.fetch_iconify_icons')
def test_custom_path_prefix_in_finder(mock_fetch):
    """Test that finder respects custom storage location."""
    mock_fetch.side_effect = mock_iconify_fetch()
    
    finder = IconSpriteFinder()
    
    # Test _get_sprite_path_prefix
    prefix = finder._get_sprite_path_prefix()
    assert prefix == 'custom-sprites/'
    
    # Test _is_sprite_path
    assert finder._is_sprite_path('custom-sprites/sprite-abc123.svg') == True
    assert finder._is_sprite_path('icons/sprite-abc123.svg') == False
    assert finder._is_sprite_path('custom-sprites/not-sprite.svg') == False


@override_settings(INCLUDECONTENTS_ICONS={
    'icons': [('home', 'mdi:home')],
    'storage': 'includecontents.icons.storages.MemoryIconStorage',
    'storage_options': {'location': 'custom-sprites/'}
})
@patch('includecontents.icons.builder.fetch_iconify_icons')
def test_custom_path_prefix_in_template_tags(mock_fetch):
    """Test that template tags use custom storage location in URLs."""
    mock_fetch.side_effect = mock_iconify_fetch()
    
    template_str = '{% icon "home" class="w-6 h-6" %}'
    template = CustomTemplate(template_str)
    result = template.render(Context())
    
    # Should use custom prefix in URL
    assert '/static/custom-sprites/sprite-' in result
    assert '/static/icons/sprite-' not in result


@override_settings(INCLUDECONTENTS_ICONS={
    'icons': [('home', 'mdi:home')],
    'storage': 'includecontents.icons.storages.MemoryIconStorage',
    'storage_options': {'location': 'assets/icons'}  # No trailing slash
})
@patch('includecontents.icons.builder.fetch_iconify_icons')
def test_path_prefix_without_trailing_slash(mock_fetch):
    """Test that path prefix without trailing slash gets normalized."""
    mock_fetch.side_effect = mock_iconify_fetch()
    
    finder = IconSpriteFinder()
    prefix = finder._get_sprite_path_prefix()
    assert prefix == 'assets/icons/'  # Should add trailing slash
    
    template_str = '{% icon "home" %}'
    template = CustomTemplate(template_str)
    result = template.render(Context())
    
    # Should use normalized prefix with slash
    assert '/static/assets/icons/sprite-' in result


@override_settings(INCLUDECONTENTS_ICONS={
    'icons': [('home', 'mdi:home')],
    'storage': 'includecontents.icons.storages.MemoryIconStorage',
    'storage_options': {}  # No location specified
})
@patch('includecontents.icons.builder.fetch_iconify_icons')
def test_default_path_prefix_when_not_configured(mock_fetch):
    """Test that default 'icons/' is used when no location configured."""
    mock_fetch.side_effect = mock_iconify_fetch()
    
    finder = IconSpriteFinder()
    prefix = finder._get_sprite_path_prefix()
    assert prefix == 'icons/'  # Should use default
    
    template_str = '{% icon "home" %}'
    template = CustomTemplate(template_str)
    result = template.render(Context())
    
    # Should use default prefix
    assert '/static/icons/sprite-' in result


@override_settings(INCLUDECONTENTS_ICONS={
    'icons': [('home', 'mdi:home')],
    'storage': 'includecontents.icons.storages.MemoryIconStorage',
    'storage_options': {'location': ''}  # Empty location
})
@patch('includecontents.icons.builder.fetch_iconify_icons')
def test_empty_path_prefix_falls_back_to_default(mock_fetch):
    """Test that empty location falls back to default."""
    mock_fetch.side_effect = mock_iconify_fetch()
    
    finder = IconSpriteFinder()
    prefix = finder._get_sprite_path_prefix()
    assert prefix == 'icons/'  # Should fallback to default
    
    template_str = '{% icon "home" %}'
    template = CustomTemplate(template_str)
    result = template.render(Context())
    
    # Should use default prefix
    assert '/static/icons/sprite-' in result