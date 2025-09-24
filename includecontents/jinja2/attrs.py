"""Jinja2 wrapper around the shared attribute container."""

from __future__ import annotations

from typing import Any

from includecontents.shared.attrs import BaseAttrs


class Attrs(BaseAttrs):
    """Collect HTML attributes emitted by component templates."""

    def __init__(self) -> None:
        super().__init__()

    # No custom __setitem__ needed - use parent behavior for Django parity

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
