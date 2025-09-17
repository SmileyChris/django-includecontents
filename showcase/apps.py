from django.apps import AppConfig


class ShowcaseConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "showcase"
    verbose_name = "Component Showcase"

    def ready(self) -> None:
        """Wire up auto-refresh of the registry in dev."""

        self._register_autoreload()

    def _register_autoreload(self) -> None:
        """Force registry discovery when component files change during development."""

        from django.conf import settings

        if getattr(self, "_autoreload_registered", False):
            return

        if not getattr(settings, "DEBUG", False):
            return

        try:
            from django.utils.autoreload import autoreload_started
        except ImportError:  # pragma: no cover - Django < 3.2 fallback
            return

        from pathlib import Path

        from django.apps import apps as django_apps

        from .registry import registry

        component_dirs: set[Path] = set()

        for template_conf in getattr(settings, "TEMPLATES", []):
            for directory in template_conf.get("DIRS", []):
                components_path = Path(directory) / "components"
                if components_path.exists():
                    component_dirs.add(components_path)

        for app_config in django_apps.get_app_configs():
            components_path = Path(app_config.path) / "templates" / "components"
            if components_path.exists():
                component_dirs.add(components_path)

        if not component_dirs:
            return

        def watch_component_dirs(sender, **kwargs):  # type: ignore[override]
            watch_dir = getattr(sender, "watch_dir", None)
            for directory in component_dirs:
                if watch_dir is not None:
                    watch_dir(str(directory), "**/*")
                else:  # pragma: no cover - legacy reloader fallback
                    for path in directory.rglob("*"):
                        sender.extra_files.add(str(path))

        def refresh_registry(sender, **kwargs):  # type: ignore[override]
            registry.discover(force=True)

        autoreload_started.connect(
            watch_component_dirs, dispatch_uid="showcase-watch-components"
        )
        autoreload_started.connect(
            refresh_registry, dispatch_uid="showcase-refresh-registry"
        )

        self._autoreload_registered = True
