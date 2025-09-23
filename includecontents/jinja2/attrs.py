"""Jinja2 wrapper around the shared attribute container."""

from __future__ import annotations

from includecontents.shared.attrs import BaseAttrs


class Attrs(BaseAttrs):
    """Collect HTML attributes emitted by component templates."""

    def __init__(self) -> None:
        super().__init__()

    def __str__(self) -> str:
        parts = []
        for key, value in self.all_attrs():
            if value is None:
                continue
            if value is True:
                parts.append(key)
            else:
                parts.append(f'{key}="{value}"')
        return " ".join(parts)


__all__ = ["Attrs"]
