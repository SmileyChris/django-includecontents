"""Jinja2 wrapper around the shared attribute container."""

from __future__ import annotations

from typing import Any

from markupsafe import escape

from includecontents.shared.attrs import BaseAttrs


class Attrs(BaseAttrs):
    """Collect HTML attributes emitted by component templates."""

    def __init__(self) -> None:
        super().__init__()

    def _render_attr(self, key: str, value: Any) -> str:
        """Render a single attribute with selective HTML escaping.

        Escaping behavior:
        - Hard-coded strings: NOT escaped (trusted developer content)
          Example: <include:button text="Don't worry" /> → text="Don't worry"

        - Template variables: ESCAPED (potentially unsafe user content)
          Example: <include:button text="{{ user_input }}" /> → text="Don&#39;t worry"

        This matches Django's conditional escaping behavior where literal strings
        in template syntax are safe but variable content gets escaped.
        """
        # Import _EscapableValue locally to avoid circular imports
        from .extension import _EscapableValue

        if isinstance(value, _EscapableValue):
            # This came from a template expression, so escape it for security
            escaped_value = escape(value.value)
            return f'{key}="{escaped_value}"'
        else:
            # This is a literal string from component syntax, don't escape it
            return f'{key}="{value}"'


__all__ = ["Attrs"]
