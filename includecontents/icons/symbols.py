"""
SVG symbol ID conversion utilities.
"""

import re
from .validation import validate_icon_name


def icon_name_to_symbol_id(icon_name: str) -> str:
    """
    Convert an icon name to a valid SVG symbol ID.

    Args:
        icon_name: Icon name (e.g., "mdi:home", "icons/my-icon.svg")

    Returns:
        Valid symbol ID (e.g., "mdi-home", "icons-my-icon-svg")
    """
    # Replace : with - and sanitize other characters for valid HTML IDs
    symbol_id = icon_name.replace(":", "-")

    # Replace invalid characters with hyphens
    symbol_id = re.sub(r"[^a-zA-Z0-9\-_]", "-", symbol_id)

    # Collapse multiple hyphens
    symbol_id = re.sub(r"-+", "-", symbol_id)

    # Remove leading/trailing hyphens
    symbol_id = symbol_id.strip("-")

    return symbol_id


def symbol_id_to_icon_name(symbol_id: str) -> str:
    """
    Convert a symbol ID back to an icon name.

    Args:
        symbol_id: Symbol ID (e.g., "mdi-home", "tabler-calendar-check")

    Returns:
        Icon name (e.g., "mdi:home", "tabler:calendar-check")
    """
    # Find the first hyphen to split prefix from name
    parts = symbol_id.split("-", 1)
    if len(parts) == 2:
        return f"{parts[0]}:{parts[1]}"
    return symbol_id


def get_icon_info_from_symbol_id(symbol_id: str) -> dict:
    """
    Extract icon information from a symbol ID.

    Args:
        symbol_id: SVG symbol ID (e.g., "mdi-home")

    Returns:
        Dictionary with icon information
    """
    icon_name = symbol_id_to_icon_name(symbol_id)

    if ":" in icon_name:
        prefix, name = icon_name.split(":", 1)
    else:
        prefix, name = "", icon_name

    return {
        "full_name": icon_name,
        "prefix": prefix,
        "name": name,
        "symbol_id": symbol_id,
        "is_valid": validate_icon_name(icon_name),
    }
