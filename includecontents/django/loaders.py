import django.template.loaders.app_directories
import django.template.loaders.base
import django.template.loaders.cached
import django.template.loaders.filesystem
from django.template import TemplateDoesNotExist

from .base import Template


class CustomTemplateMixin(django.template.loaders.base.Loader):
    def get_template(self, template_name, skip=None):
        """
        Call self.get_template_sources() and return a Template object for
        the first template matching template_name. If skip is provided, ignore
        template origins in skip. This is used to avoid recursion during
        template extending.
        """
        tried = []

        for origin in self.get_template_sources(template_name):
            if skip is not None and origin in skip:
                tried.append((origin, "Skipped to avoid recursion"))
                continue

            try:
                contents = self.get_contents(origin)  # type: ignore
            except TemplateDoesNotExist:
                tried.append((origin, "Source does not exist"))
                continue
            else:
                return Template(
                    contents,
                    origin,
                    origin.template_name,  # type: ignore
                    self.engine,
                )

        raise TemplateDoesNotExist(template_name, tried=tried)


class FilesystemLoader(
    CustomTemplateMixin, django.template.loaders.filesystem.Loader
): ...


class AppDirectoriesLoader(
    CustomTemplateMixin, django.template.loaders.app_directories.Loader
): ...


class CachedLoader(CustomTemplateMixin, django.template.loaders.cached.Loader): ...
