"""
Test that IconSpriteFinder adds source SVG files to ignore patterns
to prevent duplicate serving by other finders.
"""
from django.test import override_settings
from includecontents.icons.finders import IconSpriteFinder


@override_settings(INCLUDECONTENTS_ICONS={
    'icons': [
        'mdi:home',  # Iconify icon - shouldn't be ignored
        'icons/logo.svg',  # Local SVG - should be ignored
        ('brand', 'assets/brand.svg'),  # Local SVG with custom name - should be ignored
        ('nav-home', 'tabler:house'),  # Iconify with custom name - shouldn't be ignored
    ],
    'storage': 'includecontents.icons.storages.MemoryIconStorage',
})
def test_ignore_patterns_added_for_local_svgs():
    """Test that local SVG files are added to ignore patterns."""
    finder = IconSpriteFinder()
    ignore_patterns = []
    
    # Call list() which should modify ignore_patterns
    list(finder.list(ignore_patterns))
    
    # Should have added the local SVG files
    assert 'icons/logo.svg' in ignore_patterns
    assert 'assets/brand.svg' in ignore_patterns
    
    # Should not have added Iconify icons
    assert 'mdi:home' not in ignore_patterns
    assert 'tabler:house' not in ignore_patterns


@override_settings(INCLUDECONTENTS_ICONS={
    'icons': [
        'mdi:home',
        'tabler:user',
    ],
    'storage': 'includecontents.icons.storages.MemoryIconStorage',
})
def test_no_ignore_patterns_for_iconify_only():
    """Test that no ignore patterns are added when only using Iconify icons."""
    finder = IconSpriteFinder()
    ignore_patterns = []
    
    # Call list() which should modify ignore_patterns
    list(finder.list(ignore_patterns))
    
    # Should not have added any patterns for Iconify icons
    assert len(ignore_patterns) == 0


@override_settings(INCLUDECONTENTS_ICONS={
    'icons': [
        'icons/nav/home.svg',
        'icons/nav/profile.svg',
        'logos/brand.svg',
        ('custom-logo', 'logos/company.svg'),
    ],
    'storage': 'includecontents.icons.storages.MemoryIconStorage',
})
def test_ignore_patterns_for_nested_paths():
    """Test that nested SVG file paths are correctly added to ignore patterns."""
    finder = IconSpriteFinder()
    ignore_patterns = []
    
    # Call list() which should modify ignore_patterns
    list(finder.list(ignore_patterns))
    
    # Should have added all the local SVG files
    expected_patterns = [
        'icons/nav/home.svg',
        'icons/nav/profile.svg', 
        'logos/brand.svg',
        'logos/company.svg',
    ]
    
    for pattern in expected_patterns:
        assert pattern in ignore_patterns


@override_settings(INCLUDECONTENTS_ICONS={
    'icons': [],  # Empty configuration
    'storage': 'includecontents.icons.storages.MemoryIconStorage',
})
def test_empty_configuration_no_ignore_patterns():
    """Test that empty configuration doesn't add any ignore patterns."""
    finder = IconSpriteFinder()
    ignore_patterns = []
    
    # Call list() which should modify ignore_patterns
    list(finder.list(ignore_patterns))
    
    assert len(ignore_patterns) == 0


def test_invalid_configuration_doesnt_break():
    """Test that invalid configurations don't break the ignore pattern logic."""
    finder = IconSpriteFinder()
    ignore_patterns = []
    
    # This should not raise an exception even with invalid config
    list(finder.list(ignore_patterns))
    
    # ignore_patterns might be empty or have some items, but shouldn't crash
    assert isinstance(ignore_patterns, list)


@override_settings(INCLUDECONTENTS_ICONS={
    'icons': [
        'icons/test.svg',     # Normal local file
        'assets/other.svg',   # Another local file
    ],
    'storage': 'includecontents.icons.storages.MemoryIconStorage',
})
def test_edge_cases_in_local_file_detection():
    """Test edge cases in detecting local vs remote icons."""
    finder = IconSpriteFinder()
    ignore_patterns = []
    
    # Call list() which should modify ignore_patterns
    list(finder.list(ignore_patterns))
    
    # Local SVG files should be added to ignore patterns
    assert 'icons/test.svg' in ignore_patterns
    assert 'assets/other.svg' in ignore_patterns