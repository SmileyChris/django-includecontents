"""
Integration tests for icons that hit the real Iconify API.
These tests are skipped by default to avoid external dependencies.

To run these tests:
1. Remove the skip decorator or use pytest -rs
2. Run with: pytest tests/test_icons_integration.py -v

To run all tests EXCEPT integration tests:
pytest -m "not integration"
"""

import os
import pytest
from django.test import TestCase

from includecontents.icons.builder import fetch_iconify_icons, build_sprite


# Skip these tests unless explicitly enabled via environment variable
skip_integration = os.environ.get("TEST_ICONIFY_API", "").lower() not in (
    "1",
    "true",
    "yes",
)


@pytest.mark.integration
@pytest.mark.skipif(
    skip_integration, reason="Set TEST_ICONIFY_API=1 to run integration tests"
)
class TestIconifyAPIIntegration(TestCase):
    """Test actual Iconify API integration."""

    def test_fetch_real_mdi_icons(self):
        """Test fetching real Material Design Icons from Iconify API."""
        icon_data = fetch_iconify_icons(
            prefix="mdi",
            icon_names=["home", "account", "cog"],  # 'cog' is the settings icon in MDI
            api_base="https://api.iconify.design",
        )

        # Should return data for all requested icons
        self.assertEqual(len(icon_data), 3)
        self.assertIn("home", icon_data)
        self.assertIn("account", icon_data)
        self.assertIn("cog", icon_data)

        # Check home icon has expected structure
        home_data = icon_data["home"]
        self.assertIn("body", home_data)
        self.assertIn("viewBox", home_data)
        self.assertIn("width", home_data)
        self.assertIn("height", home_data)

        # MDI icons should have standard 24x24 viewBox
        self.assertEqual(home_data["viewBox"], "0 0 24 24")
        self.assertEqual(home_data["width"], 24)
        self.assertEqual(home_data["height"], 24)

        # Body should contain SVG path data
        self.assertIn("<path", home_data["body"])

    def test_fetch_multiple_icon_sets(self):
        """Test fetching icons from different icon sets."""
        # Test Tabler icons
        tabler_data = fetch_iconify_icons(
            prefix="tabler",
            icon_names=["user", "calendar", "star"],
            api_base="https://api.iconify.design",
        )

        self.assertEqual(len(tabler_data), 3)
        self.assertIn("user", tabler_data)

        # Test Lucide icons
        lucide_data = fetch_iconify_icons(
            prefix="lucide",
            icon_names=["settings", "search", "star"],
            api_base="https://api.iconify.design",
        )

        self.assertEqual(len(lucide_data), 3)
        self.assertIn("search", lucide_data)

    def test_build_sprite_with_real_icons(self):
        """Test building a complete sprite with real Iconify icons."""
        icons = [
            "mdi:home",
            "mdi:account-circle",
            "tabler:settings-2",  # Tabler uses settings-2
            "lucide:star",
            "heroicons:bell",  # Heroicons v2 doesn't use -solid suffix
        ]

        sprite = build_sprite(icons)

        # Should generate valid SVG sprite
        self.assertIn('<svg style="display:none">', sprite)
        self.assertIn("</svg>", sprite)

        # Should contain symbols for each icon
        self.assertIn('<symbol id="mdi-home"', sprite)
        self.assertIn('<symbol id="mdi-account-circle"', sprite)
        self.assertIn('<symbol id="tabler-settings-2"', sprite)
        self.assertIn('<symbol id="lucide-star"', sprite)
        self.assertIn('<symbol id="heroicons-bell"', sprite)

        # Each symbol should have viewBox
        self.assertIn('viewBox="0 0 24 24"', sprite)

        # Should contain actual path data
        self.assertIn("<path", sprite)

    def test_invalid_icon_handling(self):
        """Test handling of non-existent icons from API."""
        icon_data = fetch_iconify_icons(
            prefix="mdi",
            icon_names=["home", "this-icon-does-not-exist-12345"],
            api_base="https://api.iconify.design",
        )

        # Should still return valid icons
        self.assertIn("home", icon_data)
        # But not the invalid one
        self.assertNotIn("this-icon-does-not-exist-12345", icon_data)

    def test_api_response_caching(self):
        """Test that multiple requests for same icons are efficient."""
        # This tests our local caching, not API caching
        icons = ["mdi:home", "mdi:account"]

        # Build sprite twice
        sprite1 = build_sprite(icons)
        sprite2 = build_sprite(icons)

        # Should generate identical sprites
        self.assertEqual(sprite1, sprite2)

        # Both should be valid
        self.assertIn('<symbol id="mdi-home"', sprite1)
        self.assertIn('<symbol id="mdi-account"', sprite1)


@pytest.mark.integration
@pytest.mark.skipif(
    skip_integration, reason="Set TEST_ICONIFY_API=1 to run integration tests"
)
class TestRealWorldIconUsage(TestCase):
    """Test real-world usage patterns with actual API."""

    def test_common_icon_set_combination(self):
        """Test a realistic combination of different icon sets."""
        # Common pattern: mix of different icon sets for different purposes
        icons = [
            # Navigation icons from Material Design
            "mdi:home",
            "mdi:menu",
            "mdi:close",
            # UI icons from Tabler
            "tabler:search",
            "tabler:settings-2",
            "tabler:user",
            # Actions from Lucide
            "lucide:save",
            "lucide:edit",
            "lucide:trash-2",
            # Social icons from Simple Icons
            "simple-icons:github",
            "simple-icons:twitter",
        ]

        sprite = build_sprite(icons)

        # Verify all icons are included
        for icon in icons:
            symbol_id = icon.replace(":", "-")
            self.assertIn(f'<symbol id="{symbol_id}"', sprite)

        # Should be a reasonably sized sprite
        self.assertGreater(len(sprite), 1000)  # Has content
        self.assertLess(len(sprite), 50000)  # Not too huge

    def test_performance_with_many_icons(self):
        """Test performance with a larger set of icons."""
        import time

        # Build a larger icon set
        icons = []
        for i in range(20):
            icons.extend(
                [
                    f"mdi:numeric-{i % 10}-circle",
                    "tabler:arrow-up",
                    "lucide:chevron-right",
                ]
            )

        start_time = time.time()
        sprite = build_sprite(icons)
        build_time = time.time() - start_time

        # Should complete in reasonable time even with many icons
        self.assertLess(build_time, 10.0)  # 10 seconds max

        # Should generate valid sprite
        self.assertIn('<svg style="display:none">', sprite)
        self.assertTrue(sprite.count("<symbol") > 0)


# Run these tests with:
# pytest tests/test_icons_integration.py -m integration -v
# or to run without the skip:
# pytest tests/test_icons_integration.py -m integration --no-skip -v
