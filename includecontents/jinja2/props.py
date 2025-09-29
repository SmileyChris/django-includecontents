"""Jinja2 adapter for the shared props registry."""

from __future__ import annotations

from typing import Callable, Optional, Tuple

from jinja2 import Environment

from includecontents.shared.props import PropSpec, PropsRegistry


def create_props_registry(environment: Environment) -> PropsRegistry[str]:
    """Return a shared props registry wired to the Jinja environment loader."""

    def load_source(template_name: str) -> Tuple[str, Optional[Callable[[], bool]]]:
        loader = environment.loader
        if loader is None:
            return "", None
        try:
            source, _, uptodate = loader.get_source(environment, template_name)
        except Exception:  # pragma: no cover - loader errors
            return "", None
        return source, uptodate

    return PropsRegistry(load_source)


__all__ = ["create_props_registry", "PropSpec"]
