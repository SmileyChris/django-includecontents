"""Jinja2 wrapper around the shared attribute container."""

from __future__ import annotations

from typing import Any

from includecontents.shared.attrs import BaseAttrs


class Attrs(BaseAttrs):
    """Collect HTML attributes emitted by component templates."""

    def __init__(self) -> None:
        super().__init__()

    # No custom _render_attr needed - use default behavior (no escaping)


__all__ = ["Attrs"]
