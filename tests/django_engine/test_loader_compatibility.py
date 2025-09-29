"""
Tests for loader compatibility with third-party packages.

Verifies that the Engine automatically replaces Django's standard loaders
with includecontents custom loaders, even when wrapped by third-party packages
like django-template-partials.
"""

from includecontents.django.engine import Engine, _replace_django_loaders
from includecontents.django.base import Template


class TestLoaderReplacement:
    """Test the _replace_django_loaders function."""

    def test_replaces_filesystem_loader(self):
        """Should replace Django filesystem loader with custom version."""
        result = _replace_django_loaders("django.template.loaders.filesystem.Loader")
        assert result == "includecontents.django.loaders.FilesystemLoader"

    def test_replaces_app_directories_loader(self):
        """Should replace Django app directories loader with custom version."""
        result = _replace_django_loaders(
            "django.template.loaders.app_directories.Loader"
        )
        assert result == "includecontents.django.loaders.AppDirectoriesLoader"

    def test_replaces_cached_loader(self):
        """Should replace Django cached loader with custom version."""
        result = _replace_django_loaders("django.template.loaders.cached.Loader")
        assert result == "includecontents.django.loaders.CachedLoader"

    def test_preserves_third_party_loaders(self):
        """Should preserve third-party loader paths unchanged."""
        result = _replace_django_loaders("template_partials.loader.Loader")
        assert result == "template_partials.loader.Loader"

    def test_replaces_loaders_in_list(self):
        """Should replace Django loaders within a list."""
        loaders = [
            "django.template.loaders.filesystem.Loader",
            "django.template.loaders.app_directories.Loader",
        ]
        result = _replace_django_loaders(loaders)
        assert result == [
            "includecontents.django.loaders.FilesystemLoader",
            "includecontents.django.loaders.AppDirectoriesLoader",
        ]

    def test_replaces_loaders_in_tuple(self):
        """Should replace Django loaders within a tuple and preserve tuple type."""
        loaders = (
            "django.template.loaders.filesystem.Loader",
            "django.template.loaders.app_directories.Loader",
        )
        result = _replace_django_loaders(loaders)
        assert isinstance(result, tuple)
        assert result == (
            "includecontents.django.loaders.FilesystemLoader",
            "includecontents.django.loaders.AppDirectoriesLoader",
        )

    def test_replaces_nested_cached_loader(self):
        """Should replace Django loaders in nested cached loader configuration."""
        loaders = [
            (
                "django.template.loaders.cached.Loader",
                [
                    "django.template.loaders.filesystem.Loader",
                    "django.template.loaders.app_directories.Loader",
                ],
            )
        ]
        result = _replace_django_loaders(loaders)
        assert result == [
            (
                "includecontents.django.loaders.CachedLoader",
                [
                    "includecontents.django.loaders.FilesystemLoader",
                    "includecontents.django.loaders.AppDirectoriesLoader",
                ],
            )
        ]

    def test_preserves_third_party_wrapper_structure(self):
        """Should preserve third-party wrapper loaders while replacing Django loaders."""
        # Simulates django-template-partials' loader structure
        loaders = [
            (
                "template_partials.loader.Loader",
                [
                    (
                        "django.template.loaders.cached.Loader",
                        [
                            "django.template.loaders.filesystem.Loader",
                            "django.template.loaders.app_directories.Loader",
                        ],
                    )
                ],
            )
        ]
        result = _replace_django_loaders(loaders)
        assert result == [
            (
                "template_partials.loader.Loader",
                [
                    (
                        "includecontents.django.loaders.CachedLoader",
                        [
                            "includecontents.django.loaders.FilesystemLoader",
                            "includecontents.django.loaders.AppDirectoriesLoader",
                        ],
                    )
                ],
            )
        ]

    def test_mixed_loaders_list(self):
        """Should handle mixed list of standard strings and nested loaders."""
        loaders = [
            "third_party.loader.CustomLoader",
            (
                "django.template.loaders.cached.Loader",
                ["django.template.loaders.filesystem.Loader"],
            ),
        ]
        result = _replace_django_loaders(loaders)
        assert result == [
            "third_party.loader.CustomLoader",
            (
                "includecontents.django.loaders.CachedLoader",
                ["includecontents.django.loaders.FilesystemLoader"],
            ),
        ]


class TestEngineLoaderIntegration:
    """Test that the Engine correctly integrates loader replacement."""

    def test_engine_with_django_loaders_list(self):
        """Should replace Django loaders when provided as a list."""
        loaders = [
            "django.template.loaders.filesystem.Loader",
            "django.template.loaders.app_directories.Loader",
        ]
        engine = Engine(loaders=loaders)

        # Access the instantiated loaders to verify they're the custom ones
        loader_instances = engine.template_loaders
        assert any(
            "includecontents.django.loaders" in loader.__module__
            for loader in loader_instances
        )

    def test_engine_with_cached_wrapper(self):
        """Should handle cached loader wrapper configuration."""
        loaders = [
            (
                "django.template.loaders.cached.Loader",
                [
                    "django.template.loaders.filesystem.Loader",
                    "django.template.loaders.app_directories.Loader",
                ],
            )
        ]
        engine = Engine(loaders=loaders)

        # Verify the engine was created successfully with custom loaders
        loader_instances = engine.template_loaders
        assert len(loader_instances) > 0

    def test_engine_uses_custom_template_class(self):
        """Should use custom Template class with replaced loaders."""
        loaders = [
            (
                "django.template.loaders.cached.Loader",
                ["django.template.loaders.filesystem.Loader"],
            )
        ]
        engine = Engine(dirs=["/tmp"], loaders=loaders)

        # Create a template from string and verify it's our custom class
        template = engine.from_string("Hello {{ name }}")
        assert isinstance(template, Template)

    def test_simulated_template_partials_config(self):
        """Should transform django-template-partials-like loader configuration."""
        # This simulates what django-template-partials sets up
        loaders = [
            (
                "template_partials.loader.Loader",
                [
                    (
                        "django.template.loaders.cached.Loader",
                        [
                            "django.template.loaders.filesystem.Loader",
                            "django.template.loaders.app_directories.Loader",
                        ],
                    )
                ],
            )
        ]

        # Verify the transformation happens correctly
        result = _replace_django_loaders(loaders)
        expected = [
            (
                "template_partials.loader.Loader",
                [
                    (
                        "includecontents.django.loaders.CachedLoader",
                        [
                            "includecontents.django.loaders.FilesystemLoader",
                            "includecontents.django.loaders.AppDirectoriesLoader",
                        ],
                    )
                ],
            )
        ]
        assert result == expected
