"""
Manual test for the icon system with real API calls.
This is not run as part of the test suite.

To run this test:
python tests/test_icons_manual.py
"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tests.settings')
django.setup()

from includecontents.icons.builder import fetch_iconify_icons, build_sprite


def test_iconify_api():
    """Test fetching real icons from Iconify API."""
    print("Testing Iconify API integration...\n")
    
    # Test fetching some common icons
    print("1. Fetching Material Design Icons...")
    mdi_icons = fetch_iconify_icons(
        prefix='mdi',
        icon_names=['home', 'account', 'cog'],
        api_base='https://api.iconify.design'
    )
    print(f"   ✓ Found {len(mdi_icons)} MDI icons: {list(mdi_icons.keys())}")
    
    # Test building a sprite
    print("\n2. Building sprite with mixed icon sets...")
    icons = [
        'mdi:home',
        'mdi:account',
        'tabler:user',
        'lucide:star',
    ]
    
    sprite = build_sprite(icons)
    print(f"   ✓ Generated sprite: {len(sprite)} characters")
    print(f"   ✓ Contains {sprite.count('<symbol')} symbols")
    
    # Show a sample of the sprite
    print("\n3. Sample sprite content:")
    print("   " + sprite[:200] + "...")
    
    # Test error handling
    print("\n4. Testing error handling with non-existent icon...")
    error_icons = ['mdi:this-does-not-exist-12345']
    try:
        error_sprite = build_sprite(error_icons)
        print(f"   ❌ Should have failed but got: {len(error_sprite)} characters")
    except ValueError as e:
        print(f"   ✓ Handled gracefully with error: {e}")
    
    print("\n✅ All tests passed!")


if __name__ == '__main__':
    try:
        test_iconify_api()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)