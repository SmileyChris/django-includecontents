"""Django-specific attrs implementation with HTML escaping."""

from django.utils.html import escape
from django.utils.safestring import SafeString, mark_safe

from includecontents.shared.attrs import BaseAttrs


class Attrs(BaseAttrs):
    """Django-specific attrs with HTML escaping."""

    def __str__(self) -> str:
        """Render attributes as HTML string, marked as safe to prevent double-escaping."""
        result = super().__str__()
        return mark_safe(result)

    def _render_attr(self, key: str, value: any) -> str:
        """Render a single attribute with selective HTML escaping.

        Escaping behavior:
        - Hard-coded strings: NOT escaped (trusted developer content)
          Example: {% includecontents "button.html" text="Don't worry" %} → text="Don't worry"

        - Template variables: ESCAPED (potentially unsafe user content)
          Example: {% includecontents "button.html" text=user_input %} → text="Don&#39;t worry"

        This matches Django's conditional escaping behavior where literal strings
        in template syntax are safe but variable content gets escaped.
        """
        if isinstance(value, SafeString):
            # This is marked as safe (literal string), don't escape it
            return f'{key}="{value}"'
        else:
            # This is potentially unsafe content, escape it
            escaped_value = escape(str(value))
            return f'{key}="{escaped_value}"'


__all__ = ["Attrs"]