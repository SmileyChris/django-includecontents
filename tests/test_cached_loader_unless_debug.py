import pytest
from django.core.exceptions import ImproperlyConfigured
from django.test import override_settings

from includecontents.django import DjangoTemplates


class TestCachedLoaderUnlessDebug:
    @override_settings(DEBUG=True)
    def test_debug_mode_uses_non_cached_loaders(self):
        """Test that non-cached loaders are used when DEBUG=True."""
        engine = DjangoTemplates({
            "NAME": "test",
            "DIRS": [],
            "APP_DIRS": False,
            "OPTIONS": {
                "cached_loader_unless_debug": True
            }
        })

        # Check that non-cached loaders are used
        loaders = engine.engine.loaders
        assert len(loaders) == 2

        # Should have filesystem and app_directories loaders directly
        assert loaders[0] == "includecontents.django.loaders.FilesystemLoader"
        assert loaders[1] == "includecontents.django.loaders.AppDirectoriesLoader"

    @override_settings(DEBUG=False)
    def test_production_mode_uses_cached_loader(self):
        """Test that cached loader is used when DEBUG=False."""
        engine = DjangoTemplates({
            "NAME": "test",
            "DIRS": [],
            "APP_DIRS": False,
            "OPTIONS": {
                "cached_loader_unless_debug": True
            }
        })

        # Check that cached loader is used
        loaders = engine.engine.loaders
        assert len(loaders) == 1

        # Should have cached loader wrapping the other loaders
        assert isinstance(loaders[0], tuple)
        assert len(loaders[0]) == 2
        
        loader_name, child_loaders = loaders[0]
        assert loader_name == "includecontents.django.loaders.CachedLoader"

        # Check child loaders
        assert len(child_loaders) == 2
        assert child_loaders[0] == "includecontents.django.loaders.FilesystemLoader"
        assert child_loaders[1] == "includecontents.django.loaders.AppDirectoriesLoader"

    def test_conflict_with_manual_loaders_raises_error(self):
        """Test that specifying both cached_loader_unless_debug and loaders raises an error."""
        with pytest.raises(ImproperlyConfigured) as exc_info:
            DjangoTemplates({
                "NAME": "test",
                "DIRS": [],
                "APP_DIRS": False,
                "OPTIONS": {
                    "cached_loader_unless_debug": True,
                    "loaders": ["django.template.loaders.filesystem.Loader"]
                }
            })

        assert "Cannot specify both 'cached_loader_unless_debug' and 'loaders'" in str(exc_info.value)

    def test_cached_loader_unless_debug_false_uses_default(self):
        """Test that cached_loader_unless_debug=False doesn't configure loaders."""
        engine = DjangoTemplates({
            "NAME": "test",
            "DIRS": [],
            "APP_DIRS": True,
            "OPTIONS": {
                "cached_loader_unless_debug": False
            }
        })

        # Should use default Django behavior (which includes our custom loaders via APP_DIRS)
        assert engine.engine is not None

    def test_no_cached_loader_option_with_manual_loaders(self):
        """Test that manual loaders work without cached_loader_unless_debug."""
        engine = DjangoTemplates({
            "NAME": "test",
            "DIRS": [],
            "APP_DIRS": False,
            "OPTIONS": {
                "loaders": ["django.template.loaders.filesystem.Loader"]
            }
        })

        # Should have the manually specified loader (replaced with includecontents version)
        loaders = engine.engine.loaders
        assert len(loaders) == 1
        assert loaders[0] == "includecontents.django.loaders.FilesystemLoader"