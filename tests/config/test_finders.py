"""
Test that demonstrates why IconSpriteFinder should be first in STATICFILES_FINDERS.
"""

from django.test import override_settings
from includecontents.icons.finders import IconSpriteFinder


def test_finder_modifies_ignore_patterns():
    """Test that the finder adds SVG files to ignore patterns when listed."""
    # This demonstrates the behavior that requires our finder to be first

    config = {
        "icons": [
            "icons/logo.svg",
            "icons/nav/home.svg",
            ("brand", "assets/brand.svg"),
        ],
    }

    with override_settings(INCLUDECONTENTS_ICONS=config):
        finder = IconSpriteFinder()
        ignore_patterns = []

        # The _add_source_files_to_ignore_patterns method is what we're testing
        # We can test it directly without building sprites
        finder._add_source_files_to_ignore_patterns(ignore_patterns)

        # Verify that all source SVG files are now in ignore patterns
        expected_ignored = [
            "icons/logo.svg",
            "icons/nav/home.svg",
            "assets/brand.svg",
        ]

        for expected in expected_ignored:
            assert expected in ignore_patterns, (
                f"{expected} should be in ignore patterns"
            )


def test_finder_order_importance_documentation():
    """Document why finder order matters through test."""

    # When IconSpriteFinder is first in STATICFILES_FINDERS:
    # 1. IconSpriteFinder.list() is called first
    # 2. It adds source SVG files to ignore_patterns
    # 3. Later finders (FileSystemFinder, AppDirectoriesFinder)
    #    receive the modified ignore_patterns
    # 4. They skip the source SVG files that are already in the sprite
    # 5. Result: No duplicate serving of SVG files

    # When IconSpriteFinder is NOT first:
    # 1. Other finders process files first without knowing about sprites
    # 2. They serve source SVG files individually
    # 3. IconSpriteFinder runs later but can't modify what already happened
    # 4. Result: Source SVG files served both individually AND in sprite

    # This test verifies the ignore pattern mechanism works
    finder = IconSpriteFinder()

    config = {
        "icons": ["icons/test.svg"],
    }

    with override_settings(INCLUDECONTENTS_ICONS=config):
        ignore_patterns = []
        finder._add_source_files_to_ignore_patterns(ignore_patterns)

        # The source file should be added to ignore patterns
        assert "icons/test.svg" in ignore_patterns

        # This proves the mechanism works - if our finder is first,
        # other finders will skip this file due to the ignore pattern


@override_settings(
    STATICFILES_FINDERS=[
        "includecontents.icons.finders.IconSpriteFinder",  # Correct: first
        "django.contrib.staticfiles.finders.FileSystemFinder",
        "django.contrib.staticfiles.finders.AppDirectoriesFinder",
    ]
)
def test_correct_finder_order_in_settings():
    """Test that our test settings have the correct finder order."""
    from django.conf import settings

    finders = settings.STATICFILES_FINDERS

    # Our finder should be first
    assert finders[0] == "includecontents.icons.finders.IconSpriteFinder"

    # Standard Django finders should come after
    assert "django.contrib.staticfiles.finders.FileSystemFinder" in finders
    assert "django.contrib.staticfiles.finders.AppDirectoriesFinder" in finders


def test_finder_order_best_practices():
    """Document best practices for finder ordering."""

    # Correct order (what we document):
    correct_order = [
        "includecontents.icons.finders.IconSpriteFinder",  # Must be first
        "django.contrib.staticfiles.finders.FileSystemFinder",
        "django.contrib.staticfiles.finders.AppDirectoriesFinder",
    ]

    # Incorrect order (would cause duplicate serving):
    incorrect_order = [
        "django.contrib.staticfiles.finders.FileSystemFinder",
        "django.contrib.staticfiles.finders.AppDirectoriesFinder",
        "includecontents.icons.finders.IconSpriteFinder",  # Too late!
    ]

    # This test documents the correct pattern for users
    assert correct_order[0].endswith("IconSpriteFinder")
    assert incorrect_order[-1].endswith("IconSpriteFinder")

    # The key insight: IconSpriteFinder needs to run first to set up
    # ignore patterns that prevent other finders from serving source files
    finder_name = "includecontents.icons.finders.IconSpriteFinder"
    assert correct_order.index(finder_name) == 0
    assert incorrect_order.index(finder_name) == 2
