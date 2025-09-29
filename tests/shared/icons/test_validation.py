"""
Test icon configuration validation to ensure duplicate component names are caught.
"""

import pytest
from django.test import override_settings

from includecontents.icons.builder import get_sprite_settings
from includecontents.icons.exceptions import IconConfigurationError


def test_duplicate_component_names_raises_error():
    """Test that duplicate component names in configuration raise ValueError."""
    duplicate_config = {
        "icons": [
            "mdi:home",
            ("home", "tabler:house"),  # Duplicate component name 'home'
        ]
    }

    with override_settings(INCLUDECONTENTS_ICONS=duplicate_config):
        with pytest.raises(
            IconConfigurationError, match="Duplicate component name 'home'"
        ):
            get_sprite_settings()


def test_duplicate_custom_names_raises_error():
    """Test that duplicate custom component names raise ValueError."""
    duplicate_config = {
        "icons": [
            ("custom-home", "mdi:home"),
            ("custom-home", "tabler:house"),  # Duplicate custom name
        ]
    }

    with override_settings(INCLUDECONTENTS_ICONS=duplicate_config):
        with pytest.raises(
            IconConfigurationError, match="Duplicate component name 'custom-home'"
        ):
            get_sprite_settings()


def test_mixed_duplicates_raises_error():
    """Test that duplicates between automatic and custom names are caught."""
    duplicate_config = {
        "icons": [
            "mdi:home",  # Creates component name 'home'
            "tabler:user",
            ("home", "lucide:house"),  # Custom name conflicts with automatic 'home'
        ]
    }

    with override_settings(INCLUDECONTENTS_ICONS=duplicate_config):
        with pytest.raises(
            IconConfigurationError, match="Duplicate component name 'home'"
        ):
            get_sprite_settings()


def test_valid_configuration_passes():
    """Test that valid configuration without duplicates works fine."""
    valid_config = {
        "icons": [
            "mdi:home",
            "tabler:user",
            ("custom-house", "lucide:house"),
            "icons/logo.svg",
            ("brand", "icons/brand.svg"),
        ]
    }

    with override_settings(INCLUDECONTENTS_ICONS=valid_config):
        settings = get_sprite_settings()
        assert settings["icons"] == valid_config["icons"]


def test_empty_configuration_passes():
    """Test that empty icon configuration works fine."""
    empty_config = {"icons": []}

    with override_settings(INCLUDECONTENTS_ICONS=empty_config):
        settings = get_sprite_settings()
        assert settings["icons"] == []


def test_no_configuration_passes():
    """Test that missing icon configuration works fine."""
    with override_settings(INCLUDECONTENTS_ICONS={}):
        settings = get_sprite_settings()
        assert settings["icons"] == []  # Default value


def test_file_path_conflicts():
    """Test that file paths with same base name create conflicts."""
    duplicate_config = {
        "icons": [
            "icons/home.svg",  # Creates component name 'home'
            "logos/home.svg",  # Also creates component name 'home'
        ]
    }

    with override_settings(INCLUDECONTENTS_ICONS=duplicate_config):
        with pytest.raises(
            IconConfigurationError, match="Duplicate component name 'home'"
        ):
            get_sprite_settings()


def test_file_path_custom_name_no_conflict():
    """Test that file paths with custom names avoid conflicts."""
    valid_config = {
        "icons": [
            ("nav-home", "icons/home.svg"),
            ("logo-home", "logos/home.svg"),
        ]
    }

    with override_settings(INCLUDECONTENTS_ICONS=valid_config):
        settings = get_sprite_settings()
        assert settings["icons"] == valid_config["icons"]
