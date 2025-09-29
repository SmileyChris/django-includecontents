"""
Template tags for icon sprites: {% icons_inline %} and {% icon %}.
"""

from django import template
from django.template.base import FilterExpression
from django.templatetags.static import static
from django.utils.safestring import mark_safe

from ..builder import (
    get_or_create_sprite,
    get_sprite_hash,
    get_sprite_settings,
    get_sprite_filename,
)
from ..utils import parse_icon_definitions, format_attributes

# Import Attrs from the main templatetags module
try:
    from ...templatetags.includecontents import Attrs
except ImportError:
    # Fallback if the main module is not available
    Attrs = None

register = template.Library()


def get_sprite_url(sprite_hash):
    """Get static URL for sprite file using configured storage location."""
    sprite_filename = get_sprite_filename(sprite_hash)
    sprite_settings = get_sprite_settings()
    storage_options = sprite_settings.get("storage_options", {})
    location = storage_options.get("location", "icons/")

    # Handle empty location - fallback to default
    if not location or not location.strip():
        location = "icons/"
    elif not location.endswith("/"):
        location += "/"

    return static(f"{location}{sprite_filename}")


class IconNode(template.Node):
    """
    Template node for rendering individual icons using SVG <use> syntax.

    Handles <icon:name> syntax by converting it to SVG output.
    """

    def __init__(self, icon_name: str, attributes: dict, as_var: str = None):
        self.icon_name = icon_name
        self.attributes = attributes
        self.as_var = as_var

    def _get_actual_icon_name(self, sprite_settings):
        """Get the actual icon name from component name using the icon definitions."""
        icon_definitions = sprite_settings.get("icons", [])

        try:
            component_map = parse_icon_definitions(icon_definitions)
            actual_icon_name = component_map.get(self.icon_name)

            if not actual_icon_name:
                # Check if this icon exists in the configured icons list
                from ..utils import get_icon_names_from_definitions

                configured_icons = get_icon_names_from_definitions(icon_definitions)

                if self.icon_name not in configured_icons:
                    return None

                # Use icon name directly
                actual_icon_name = self.icon_name

            return actual_icon_name

        except ValueError:
            # If parsing fails, assume icon doesn't exist
            return None

    def _extract_context_attrs(self, context):
        """Extract attributes from context if using component-style syntax."""
        svg_attrs = {}
        use_attrs = {}

        context_attrs = context.get("attrs")
        if context_attrs and Attrs and isinstance(context_attrs, Attrs):
            # Get main attributes for the SVG element
            svg_attrs.update(dict(context_attrs.all_attrs()))

            # Get nested attributes for the USE element
            if hasattr(context_attrs, "use"):
                use_attrs.update(dict(context_attrs.use.all_attrs()))

        return svg_attrs, use_attrs

    def _process_tag_attributes(self, context, svg_attrs, use_attrs):
        """Process tag-level attributes and handle special cases."""
        cache_bust = None

        for key, value in self.attributes.items():
            if isinstance(value, FilterExpression):
                resolved_value = value.resolve(context)
            else:
                resolved_value = value

            # Skip None, False, or empty string values
            if resolved_value in (None, False, ""):
                continue

            # Handle special cache-busting parameter
            if key == "cache_bust":
                # If cache_bust is True (boolean attribute), use current timestamp
                if resolved_value is True:
                    import time

                    cache_bust = f"_={int(time.time())}"
                else:
                    cache_bust = resolved_value
                continue

            # Handle dot notation for nested attributes
            if "." in key and key.startswith("use."):
                # This is a USE element attribute
                use_key = key[4:]  # Remove "use." prefix
                use_attrs[use_key] = resolved_value
            else:
                # This is an SVG element attribute
                svg_attrs[key] = resolved_value

        return cache_bust

    def _build_sprite_url(self, sprite_hash, cache_bust):
        """Build the sprite URL with optional cache busting."""
        sprite_url = get_sprite_url(sprite_hash)

        if cache_bust:
            # Add query parameter for cache busting
            separator = "&" if "?" in sprite_url else "?"
            sprite_url = f"{sprite_url}{separator}{cache_bust}"

        return sprite_url

    def render(self, context):
        """Render the icon as SVG with <use> element, supporting attrs.use pattern."""
        if not self.icon_name:
            return ""

        # Get sprite settings and find the actual icon name
        sprite_settings = get_sprite_settings()
        actual_icon_name = self._get_actual_icon_name(sprite_settings)

        if not actual_icon_name:
            # Icon doesn't exist, handle as_var or return empty
            if self.as_var:
                context[self.as_var] = ""
            return ""

        # Get sprite hash (efficient, doesn't build sprite)
        sprite_hash = get_sprite_hash()

        if not sprite_hash:
            return ""

        # Use component name directly as symbol ID
        # The sprite builder now uses component names as symbol IDs
        symbol_id = self.icon_name

        # Extract attributes from context (component-style usage)
        svg_attrs, use_attrs = self._extract_context_attrs(context)

        # Process tag-level attributes (they take precedence)
        cache_bust = self._process_tag_attributes(context, svg_attrs, use_attrs)

        # Format attribute strings
        svg_attrs_str = format_attributes(svg_attrs)
        use_attrs_str = format_attributes(use_attrs)

        # Add spaces if attributes exist
        svg_attrs_str = " " + svg_attrs_str if svg_attrs_str else ""
        use_attrs_str = " " + use_attrs_str if use_attrs_str else ""

        # Build sprite URL with cache busting if needed
        sprite_url = self._build_sprite_url(sprite_hash, cache_bust)
        href = f"{sprite_url}#{symbol_id}"

        # Generate SVG with <use> element and separate attribute control
        svg = f'<svg{svg_attrs_str}><use{use_attrs_str} href="{href}"></use></svg>'

        # Handle as_var - store in context instead of rendering
        if self.as_var:
            context[self.as_var] = mark_safe(svg)
            return ""

        return mark_safe(svg)


@register.simple_tag
def icons_inline():
    """
    Render the full sprite inline in HTML.

    Usage:
        {% load icons %}
        {% icons_inline %}

    This will output the complete SVG sprite sheet with all symbols.
    With the static file finder, this is mainly useful for performance optimization
    when you want to avoid an extra HTTP request.

    Returns:
        Inline SVG sprite sheet
    """
    # Get or create the sprite
    sprite_hash, sprite_content = get_or_create_sprite()

    if not sprite_hash:
        return ""

    return mark_safe(sprite_content)


@register.simple_tag
def icon_sprite_url():
    """
    Get the URL to the sprite file using Django's static file system.

    Usage:
        {% load icons %}
        {% icon_sprite_url %}

    Returns:
        URL to sprite file
    """
    sprite_hash = get_sprite_hash()

    if not sprite_hash:
        return ""

    return get_sprite_url(sprite_hash)


@register.tag
def icon(parser, token):
    """
    Render an individual icon using SVG <use> reference.

    This tag is called by the custom engine when it encounters <icon:name> syntax.

    Usage:
        {% icon "home" class="w-6 h-6" %}
        {% icon "user-plus" use.class="fill-current" %}
        {% icon "home" class="w-6 h-6" as my_icon %}

    Args:
        parser: Template parser
        token: Template token

    Returns:
        IconNode instance
    """
    bits = token.split_contents()

    if len(bits) < 2:
        raise template.TemplateSyntaxError(
            f"{bits[0]} tag requires at least one argument: the icon name"
        )

    # Check for 'as variable_name' at the end
    as_var = None
    if len(bits) >= 4 and bits[-2] == "as":
        as_var = bits[-1]
        bits = bits[:-2]  # Remove 'as variable_name' from processing

    # First argument is the icon name
    # Parse remaining arguments as attributes, supporting dot notation
    attributes = {}

    for bit in bits[2:]:
        if "=" in bit:
            key, value = bit.split("=", 1)
            # Store the attribute key as-is (including dots like "use.class")
            # The IconNode will handle the dot notation during rendering
            attributes[key] = parser.compile_filter(value)
        else:
            # Boolean attribute
            attributes[bit] = parser.compile_filter("True")

    # Extract icon name from the token
    # For basic string literals like "home", remove quotes
    icon_name_token = bits[1]
    if (icon_name_token.startswith('"') and icon_name_token.endswith('"')) or (
        icon_name_token.startswith("'") and icon_name_token.endswith("'")
    ):
        icon_name = icon_name_token[1:-1]
    else:
        # For now, we need the icon name to be a literal string
        # In the future, we could support dynamic icon names
        icon_name = icon_name_token

    return IconNode(icon_name, attributes, as_var)
