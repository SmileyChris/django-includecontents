import django.template.loaders.app_directories
import django.template.loaders.base
import django.template.loaders.cached
import django.template.loaders.filesystem
from django.template import TemplateDoesNotExist

from .base import Template


def _enhance_component_template_error(exc, template_name):
    """
    Enhance TemplateDoesNotExist errors for component templates with helpful suggestions.
    """
    # Extract component name from template path
    component_path = template_name.replace("components/", "").replace(".html", "")
    component_tag = f"<include:{component_path.replace('/', ':')}>"

    # Build enhanced error message
    error_lines = [
        f"Component template not found: {component_tag}",
        "",
        "Looked for:",
        f"  - {template_name}",
        "",
        "Suggestions:",
        f"  1. Create template: templates/{template_name}",
        "  2. Check TEMPLATES['DIRS'] setting includes your templates directory",
        "  3. Verify component name matches file path",
        "  4. Ensure template is in templates/components/ directory",
        "",
        "For app-based components:",
        f"  5. Create in app: <app>/templates/{template_name}",
        "  6. Ensure app is in INSTALLED_APPS",
    ]

    enhanced_message = "\n".join(error_lines)

    # Use the error enhancement utility if available
    try:
        from .errors import enhance_error

        enhance_error(exc, enhanced_message)
    except ImportError:
        # Fallback - modify args directly
        if exc.args:
            exc.args = (f"{exc.args[0]}\n\n{enhanced_message}",) + exc.args[1:]
        else:
            exc.args = (enhanced_message,)


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

        # Check if this is a component template and enhance error message
        original_exc = TemplateDoesNotExist(template_name, tried=tried)
        if isinstance(template_name, str) and template_name.startswith("components/"):
            # Create enhanced exception with original as cause
            enhanced_exc = TemplateDoesNotExist(template_name, tried=tried)
            _enhance_component_template_error(enhanced_exc, template_name)
            enhanced_exc.__cause__ = original_exc
            raise enhanced_exc
        else:
            raise original_exc


class FilesystemLoader(
    CustomTemplateMixin, django.template.loaders.filesystem.Loader
): ...


class AppDirectoriesLoader(
    CustomTemplateMixin, django.template.loaders.app_directories.Loader
): ...


class CachedLoader(CustomTemplateMixin, django.template.loaders.cached.Loader): ...
