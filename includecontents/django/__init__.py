from typing import Dict, Any, List, Union, Tuple

import django.template.backends.django
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

from .engine import Engine


# Mapping of standard Django loaders to their includecontents equivalents
LOADER_MAPPING = {
    "django.template.loaders.filesystem.Loader": "includecontents.django.loaders.FilesystemLoader",
    "django.template.loaders.app_directories.Loader": "includecontents.django.loaders.AppDirectoriesLoader",
    "django.template.loaders.cached.Loader": "includecontents.django.loaders.CachedLoader",
}


class DjangoTemplates(django.template.backends.django.DjangoTemplates):
    def __init__(self, params: Dict[str, Any]) -> None:
        # Copy parent init code.
        params = params.copy()
        options = params["OPTIONS"].copy()
        
        # Check for conflicting options
        if "cached_loader_unless_debug" in options and "loaders" in options:
            raise ImproperlyConfigured(
                "Cannot specify both 'cached_loader_unless_debug' and 'loaders' options. "
                "Use 'loaders' for manual configuration or 'cached_loader_unless_debug' for automatic configuration."
            )
        
        # Handle cached_loader_unless_debug option
        cached_loader_unless_debug = options.pop("cached_loader_unless_debug", None)
        if cached_loader_unless_debug:
            # Configure loaders based on DEBUG setting
            if getattr(settings, "DEBUG", False):
                # Use non-cached loaders in debug mode
                options["loaders"] = [
                    "includecontents.django.loaders.FilesystemLoader",
                    "includecontents.django.loaders.AppDirectoriesLoader",
                ]
            else:
                # Use cached loader in production
                options["loaders"] = [(
                    "includecontents.django.loaders.CachedLoader",
                    [
                        "includecontents.django.loaders.FilesystemLoader",
                        "includecontents.django.loaders.AppDirectoriesLoader",
                    ]
                )]
        elif "loaders" in options:
            # Replace standard loaders with includecontents loaders if manually specified
            options["loaders"] = self._replace_loaders(options["loaders"])
        
        options.setdefault("autoescape", True)
        options.setdefault("debug", settings.DEBUG)
        options.setdefault("file_charset", "utf-8")
        
        # Update params with modified options before calling super
        params["OPTIONS"] = options
        super().__init__(params)
        options["libraries"] = self.engine.libraries
        # Add the includecontents template tag to the builtins list.
        if "builtins" in options:
            builtins = options["builtins"].copy()
        else:
            builtins = []
        if "includecontents.templatetags.includecontents" not in builtins:
            builtins = ["includecontents.templatetags.includecontents"] + builtins
        options["builtins"] = builtins
        self.engine = Engine(self.dirs, self.app_dirs, **options)
    
    def _replace_loaders(self, loaders: List[Union[str, Tuple[str, List]]]) -> List[Union[str, Tuple[str, List]]]:
        """Replace standard Django loaders with their includecontents equivalents."""
        replaced_loaders = []
        
        for loader in loaders:
            if isinstance(loader, str):
                # Simple loader string
                replaced_loaders.append(LOADER_MAPPING.get(loader, loader))
            elif isinstance(loader, (list, tuple)) and len(loader) == 2:
                # Cached loader or similar: (loader_class, child_loaders)
                loader_class, child_loaders = loader
                replaced_loader_class = LOADER_MAPPING.get(loader_class, loader_class)
                replaced_child_loaders = self._replace_loaders(child_loaders)
                replaced_loaders.append((replaced_loader_class, replaced_child_loaders))
            else:
                # Unknown format, keep as is
                replaced_loaders.append(loader)
        
        return replaced_loaders
