"""Context helpers shared between templating engines."""

from __future__ import annotations

from typing import Any, Dict, Iterable, Mapping, Set


class ComponentContext:
    """Manages context isolation for component renders."""

    PRESERVED_KEYS: Set[str] = {
        "request",
        "csrf_token",
        "csrf_input",  # Django's Jinja2 backend provides this
        "user",
        "perms",
        "messages",
        "LANGUAGES",
        "LANGUAGE_CODE",
    }

    @classmethod
    def create_isolated(
        cls,
        parent_vars: Mapping[str, Any],
        component_props: Mapping[str, Any],
        *,
        inherit_parent: bool = False,
    ) -> Dict[str, Any]:
        if inherit_parent:
            isolated = dict(parent_vars)
        else:
            isolated = {
                key: parent_vars[key]
                for key in cls.PRESERVED_KEYS
                if key in parent_vars
            }
        isolated.update(component_props)
        return isolated


class CapturedContents:
    """Container exposing default and named content blocks."""

    def __init__(self, default: str, named: Dict[str, str]) -> None:
        self._default = default
        self._named = dict(named)

    @property
    def default(self) -> str:
        return self._default

    def get(self, name: str | None, default: str = "") -> str:
        if name in (None, "", "default"):
            return self._default if self._default else default
        return self._named.get(name, default)

    def __getattr__(self, name: str) -> str:
        return self._named.get(name, "")

    def __contains__(self, name: str) -> bool:
        return name in self._named

    def keys(self) -> Iterable[str]:
        return self._named.keys()

    def items(self) -> Iterable[tuple[str, str]]:
        return self._named.items()

    @property
    def stripped(self) -> str:
        return self._default.strip()

    def __str__(self) -> str:  # pragma: no cover - implicit use in templates
        return self._default

    def __html__(self) -> str:  # pragma: no cover - for MarkupSafe compatibility
        return self._default


__all__ = ["ComponentContext", "CapturedContents"]
