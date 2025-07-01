import pytest
from django.template import engines
from django.test import override_settings

from includecontents.django import DjangoTemplates


class TestLoaderReplacement:
    def test_simple_loader_replacement(self):
        """Test that simple loader strings are replaced correctly."""
        engine = DjangoTemplates({
            "NAME": "test",
            "DIRS": [],
            "APP_DIRS": False,
            "OPTIONS": {
                "loaders": [
                    "django.template.loaders.filesystem.Loader",
                    "django.template.loaders.app_directories.Loader",
                ]
            }
        })

        # Check that loaders were replaced
        loaders = engine.engine.loaders
        assert len(loaders) == 2
        assert loaders[0] == "includecontents.django.loaders.FilesystemLoader"
        assert loaders[1] == "includecontents.django.loaders.AppDirectoriesLoader"

    def test_cached_loader_replacement(self):
        """Test that cached loader with child loaders is replaced correctly."""
        engine = DjangoTemplates({
            "NAME": "test",
            "DIRS": [],
            "APP_DIRS": False,
            "OPTIONS": {
                "loaders": [(
                    "django.template.loaders.cached.Loader", [
                        "django.template.loaders.filesystem.Loader",
                        "django.template.loaders.app_directories.Loader",
                    ]
                )]
            }
        })

        # Check that cached loader was replaced
        loaders = engine.engine.loaders
        assert len(loaders) == 1
        
        # The loader should be a tuple (loader_name, child_loaders)
        assert isinstance(loaders[0], tuple)
        assert len(loaders[0]) == 2
        
        loader_name, child_loaders = loaders[0]
        assert loader_name == "includecontents.django.loaders.CachedLoader"
        
        # Check that child loaders were also replaced
        assert len(child_loaders) == 2
        assert child_loaders[0] == "includecontents.django.loaders.FilesystemLoader"
        assert child_loaders[1] == "includecontents.django.loaders.AppDirectoriesLoader"

    def test_unknown_loader_preserved(self):
        """Test that unknown loaders are preserved as-is."""
        engine = DjangoTemplates({
            "NAME": "test",
            "DIRS": [],
            "APP_DIRS": False,
            "OPTIONS": {
                "loaders": [
                    "some.custom.Loader",
                    "django.template.loaders.filesystem.Loader",
                ]
            }
        })

        # Check that unknown loader is preserved but known one is replaced
        loaders = engine.engine.loaders
        assert len(loaders) == 2
        assert loaders[0] == "some.custom.Loader"
        assert loaders[1] == "includecontents.django.loaders.FilesystemLoader"

    def test_no_loaders_specified(self):
        """Test that engine works correctly when no loaders are manually specified."""
        engine = DjangoTemplates({
            "NAME": "test",
            "DIRS": [],
            "APP_DIRS": True,
            "OPTIONS": {}
        })

        # Should work without errors and use default includecontents loaders
        assert engine.engine is not None