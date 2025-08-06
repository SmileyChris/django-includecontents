"""
Integration test showing complete icon system functionality:
- Duplicate validation prevents configuration errors
- Configurable storage path works with finder and template tags
- Static file integration works seamlessly
"""
import pytest  
from unittest.mock import patch
from django.test import override_settings
from django.template import Context

from includecontents.django.base import Template as CustomTemplate
from includecontents.icons.builder import get_sprite_settings
from includecontents.icons.finders import IconSpriteFinder


def mock_iconify_fetch():
    """Mock function for iconify API calls."""
    def mock_fetch_fn(prefix, icon_names, api_base):
        icons = {}
        for name in icon_names:
            if name == 'home':
                icons[name] = {'body': '<path d="M10 10"/>', 'viewBox': '0 0 24 24'}
            elif name == 'user':
                icons[name] = {'body': '<circle cx="12" cy="12" r="3"/>', 'viewBox': '0 0 24 24'}
        return icons
    return mock_fetch_fn


def test_duplicate_validation_prevents_bad_config():
    """Test that duplicate component names are caught at settings level."""
    bad_config = {
        'icons': [
            'mdi:home',          # Creates component 'home'
            ('home', 'tabler:house'),  # Duplicate!
        ]
    }
    
    with override_settings(INCLUDECONTENTS_ICONS=bad_config):
        with pytest.raises(ValueError, match="Duplicate component name 'home'"):
            get_sprite_settings()


@override_settings(INCLUDECONTENTS_ICONS={
    'icons': [
        ('nav-home', 'mdi:home'),
        ('nav-user', 'tabler:user'),
        ('logo', 'icons/brand.svg'),
    ],
    'storage': 'includecontents.icons.storages.MemoryIconStorage',
    'storage_options': {'location': 'app-sprites/'},
})
@patch('includecontents.icons.builder.fetch_iconify_icons')
def test_complete_integration_with_custom_path(mock_fetch):
    """Test complete system integration with custom storage path."""
    mock_fetch.side_effect = mock_iconify_fetch()
    
    # 1. Settings validation should pass (no duplicates)
    settings = get_sprite_settings()
    assert settings['storage_options']['location'] == 'app-sprites/'
    
    # 2. Finder should work with custom path
    finder = IconSpriteFinder()
    prefix = finder._get_sprite_path_prefix()
    assert prefix == 'app-sprites/'
    
    # Should recognize sprite paths with custom prefix
    assert finder._is_sprite_path('app-sprites/sprite-abc123.svg') == True
    assert finder._is_sprite_path('icons/sprite-abc123.svg') == False
    
    # 3. Template tags should generate correct URLs
    template_str = '''
    <icon:nav-home class="nav-icon" />
    <icon:nav-user class="user-avatar" />
    '''
    template = CustomTemplate(template_str)
    result = template.render(Context())
    
    # Should use custom path prefix in URLs
    assert '/static/app-sprites/sprite-' in result
    assert '/static/icons/sprite-' not in result
    
    # Should use component names as symbol IDs
    assert '#nav-home"' in result
    assert '#nav-user"' in result
    
    # Should not contain the actual icon names as symbol IDs
    assert '#mdi-home"' not in result
    assert '#tabler-user"' not in result


@override_settings(INCLUDECONTENTS_ICONS={
    'icons': [
        'mdi:home',
        'tabler:user', 
        ('custom-star', 'lucide:star'),
    ],
    'storage': 'includecontents.icons.storages.MemoryIconStorage',
    'storage_options': {},  # No custom location - should use default
})
@patch('includecontents.icons.builder.fetch_iconify_icons')
def test_default_path_behavior(mock_fetch):
    """Test that default behavior still works when no custom path specified."""
    def mock_fetch_all(prefix, icon_names, api_base):
        icons = {}
        for name in icon_names:
            if name in ['home', 'user', 'star']:
                icons[name] = {'body': '<path d="test"/>', 'viewBox': '0 0 24 24'}
        return icons
        
    mock_fetch.side_effect = mock_fetch_all
    
    # Should use default 'icons/' prefix
    finder = IconSpriteFinder()
    prefix = finder._get_sprite_path_prefix()
    assert prefix == 'icons/'
    
    # Template should use default path
    template_str = '<icon:home /> <icon:custom-star />'
    template = CustomTemplate(template_str)
    result = template.render(Context())
    
    assert '/static/icons/sprite-' in result
    assert '#home"' in result
    assert '#custom-star"' in result  # Custom name used as symbol ID


def test_edge_cases_in_configuration():
    """Test edge cases in icon configuration."""
    
    # Empty location should fallback to default
    config1 = {
        'icons': [('test', 'mdi:home')],
        'storage_options': {'location': ''}
    }
    
    with override_settings(INCLUDECONTENTS_ICONS=config1):
        finder = IconSpriteFinder()
        assert finder._get_sprite_path_prefix() == 'icons/'
    
    # Whitespace-only location should fallback to default  
    config2 = {
        'icons': [('test', 'mdi:home')],
        'storage_options': {'location': '   '}
    }
    
    with override_settings(INCLUDECONTENTS_ICONS=config2):
        finder = IconSpriteFinder()
        assert finder._get_sprite_path_prefix() == 'icons/'
    
    # Path without trailing slash should get normalized
    config3 = {
        'icons': [('test', 'mdi:home')],
        'storage_options': {'location': 'assets/icons'}
    }
    
    with override_settings(INCLUDECONTENTS_ICONS=config3):
        finder = IconSpriteFinder()
        assert finder._get_sprite_path_prefix() == 'assets/icons/'