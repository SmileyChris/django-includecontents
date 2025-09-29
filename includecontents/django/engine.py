from pathlib import Path

import django.template.base
import django.template.engine

from .base import Template


def _replace_django_loaders(loaders):
    """
    Recursively replace Django's standard loaders with includecontents custom loaders.

    This allows compatibility with third-party packages (like django-template-partials)
    that wrap Django's loaders, while ensuring our custom Template class and
    functionality is always used.

    Args:
        loaders: A loader configuration (string, tuple, or list)

    Returns:
        The same structure with Django loaders replaced
    """
    # Mapping of Django loaders to includecontents equivalents
    LOADER_MAPPING = {
        "django.template.loaders.filesystem.Loader": "includecontents.django.loaders.FilesystemLoader",
        "django.template.loaders.app_directories.Loader": "includecontents.django.loaders.AppDirectoriesLoader",
        "django.template.loaders.cached.Loader": "includecontents.django.loaders.CachedLoader",
    }

    if isinstance(loaders, str):
        # Simple string loader - replace if it's a Django loader
        return LOADER_MAPPING.get(loaders, loaders)

    elif isinstance(loaders, (list, tuple)):
        # List of loaders - recursively process each one
        result = [_replace_django_loaders(loader) for loader in loaders]
        return type(loaders)(result)  # Preserve tuple vs list

    elif isinstance(loaders, tuple) and len(loaders) == 2:
        # Tuple format: (loader_class, [wrapped_loaders])
        loader_class, wrapped = loaders
        return (
            LOADER_MAPPING.get(loader_class, loader_class),
            _replace_django_loaders(wrapped),
        )

    # Unknown format, return as-is
    return loaders


class Engine(django.template.Engine):
    app_dirname = Path("templates") / "components"

    def __init__(
        self,
        dirs=None,
        app_dirs=False,
        context_processors=None,
        debug=False,
        loaders=None,
        builtins=None,
        *args,
        **kwargs,
    ):
        # Add all includecontents template tags to builtins so they're automatically available
        if builtins is None:
            builtins = []
        else:
            builtins = list(builtins)

        # Define all includecontents builtin template tag modules in priority order
        includecontents_builtins = [
            "includecontents.templatetags.includecontents",  # Core tags: includecontents, contents, wrapif, attrs
            "includecontents.icons.templatetags.icons",  # Icon tags: icon, icons_inline, icon_sprite_url
        ]

        # Add each builtin module if not already present (prepend to maintain priority)
        for builtin_module in reversed(includecontents_builtins):
            if builtin_module not in builtins:
                builtins = [builtin_module] + builtins

        super().__init__(
            dirs=dirs,
            app_dirs=app_dirs,
            context_processors=context_processors,
            debug=debug,
            loaders=loaders,
            builtins=builtins,
            *args,
            **kwargs,
        )

        # Replace Django's standard loaders with our custom ones
        self.loaders = _replace_django_loaders(self.loaders)

    def from_string(self, template_code):
        """
        Return a compiled Template object for the given template code,
        handling template inheritance recursively.
        """
        return Template(template_code, engine=self)
