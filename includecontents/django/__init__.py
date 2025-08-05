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
        # The Engine class handles all builtin template tag registration
        self.engine = Engine(self.dirs, self.app_dirs, **options)
