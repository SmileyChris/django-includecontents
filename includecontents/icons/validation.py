"""
Icon validation and parsing utilities.
"""

import re
from typing import List, Tuple


def validate_icon_name(icon_name: str) -> bool:
    """
    Validate that an icon name follows the expected format.

    Args:
        icon_name: Icon name to validate (e.g., "mdi:home", "icons/my-icon.svg")

    Returns:
        True if valid, False otherwise
    """
    if not icon_name or not isinstance(icon_name, str):
        return False

    # Check for local SVG file path (no colon, ends with .svg, or contains /)
    if ":" not in icon_name:
        # This should be a local file path
        if icon_name.endswith(".svg") or "/" in icon_name:
            # Validate it's a safe path
            return bool(
                icon_name.strip()
                and not any(char in icon_name for char in ["<", ">", '"', "'", ".."])
            )
        else:
            # Invalid: no colon and doesn't look like a file path
            return False

    # Must contain exactly one colon for prefixed icons
    if icon_name.count(":") != 1:
        return False

    prefix, name = icon_name.split(":", 1)

    # Prefix and name must be non-empty
    if not prefix or not name:
        return False

    # For Iconify icons, allow letters, numbers, hyphens, underscores
    valid_chars = re.compile(r"^[a-zA-Z0-9_-]+$")

    return bool(valid_chars.match(prefix) and valid_chars.match(name))


def parse_icon_names(icon_list: List[str]) -> Tuple[List[str], List[str]]:
    """
    Parse a list of icon names and separate valid from invalid ones.

    Args:
        icon_list: List of icon names to parse

    Returns:
        Tuple of (valid_icons, invalid_icons)
    """
    valid_icons = []
    invalid_icons = []

    for icon_name in icon_list:
        if validate_icon_name(icon_name):
            valid_icons.append(icon_name)
        else:
            invalid_icons.append(icon_name)

    return valid_icons, invalid_icons


def extract_icon_prefixes(icon_names: List[str]) -> List[str]:
    """
    Extract unique prefixes from a list of icon names.

    Args:
        icon_names: List of icon names

    Returns:
        List of unique prefixes, sorted alphabetically
    """
    prefixes = set()

    for icon_name in icon_names:
        if validate_icon_name(icon_name):
            prefix = icon_name.split(":", 1)[0]
            prefixes.add(prefix)

    return sorted(prefixes)


def group_icons_by_prefix(icon_names: List[str]) -> dict:
    """
    Group icon names by their prefix.

    Args:
        icon_names: List of icon names

    Returns:
        Dictionary mapping prefixes to lists of icon names (without prefix)
    """
    groups = {}

    for icon_name in icon_names:
        if validate_icon_name(icon_name):
            prefix, name = icon_name.split(":", 1)
            if prefix not in groups:
                groups[prefix] = []
            groups[prefix].append(name)

    return groups
