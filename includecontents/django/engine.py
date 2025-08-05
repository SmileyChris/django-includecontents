from pathlib import Path

import django.template.base
import django.template.engine
from django.core.exceptions import ImproperlyConfigured

from .base import Template


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
        if loaders is None:
            loaders = ["includecontents.django.loaders.FilesystemLoader"]
            if app_dirs:
                loaders += ["includecontents.django.loaders.AppDirectoriesLoader"]
            loaders = [("includecontents.django.loaders.CachedLoader", loaders)]
        else:
            if app_dirs:
                raise ImproperlyConfigured(
                    "app_dirs must not be set when loaders is defined."
                )

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
            app_dirs=False,
            context_processors=context_processors,
            debug=debug,
            loaders=loaders,
            builtins=builtins,
            *args,
            **kwargs,
        )
        self.app_dirs = app_dirs

    def from_string(self, template_code):
        """
        Return a compiled Template object for the given template code,
        handling template inheritance recursively.
        """
        return Template(template_code, engine=self)
