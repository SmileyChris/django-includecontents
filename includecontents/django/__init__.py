import django.template.backends.django
from django.conf import settings

from .engine import Engine


class DjangoTemplates(django.template.backends.django.DjangoTemplates):
    def __init__(self, params):
        # Copy parent init code.
        params = params.copy()
        options = params["OPTIONS"].copy()
        options.setdefault("autoescape", True)
        options.setdefault("debug", settings.DEBUG)
        options.setdefault("file_charset", "utf-8")
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
