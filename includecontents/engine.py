from pathlib import Path

import django.template.base
import django.template.engine

from .base import Template


class Engine(django.template.Engine):
    app_dirname = Path("templates") / "components"

    def from_string(self, template_code):
        """
        Return a compiled Template object for the given template code,
        handling template inheritance recursively.
        """
        return Template(template_code, engine=self)

    def get_template(self, template_name):
        """
        Return a compiled Template object for the given template name,
        handling template inheritance recursively.
        """
        template, origin = self.find_template(template_name)
        if isinstance(template, django.template.base.Template):
            return Template(template.source, origin, template_name, engine=self)
        if not hasattr(template, "render"):
            # template needs to be compiled
            template = Template(template, origin, template_name, engine=self)
        return template
