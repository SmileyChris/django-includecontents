"""
Symbol conversion and miscellaneous utilities for icon handling.
"""

import re
from typing import Dict, List, Tuple, Union

IconDefinition = Union[str, Tuple[str, str]]


def normalize_icon_definition(icon_def: IconDefinition) -> Tuple[str, str]:
    """
    Normalize an icon definition to (component_name, icon_name) tuple.

    Args:
        icon_def: Either a string "mdi:home" or "icons/home.svg" or tuple ("home", "mdi:home")

    Returns:
        Tuple of (component_name, icon_name)

    Examples:
        normalize_icon_definition("mdi:home") -> ("home", "mdi:home")
        normalize_icon_definition("icons/home.svg") -> ("home", "icons/home.svg")
        normalize_icon_definition(("home", "mdi:home")) -> ("home", "mdi:home")
        normalize_icon_definition(("house", "icons/home.svg")) -> ("house", "icons/home.svg")
    """
    if isinstance(icon_def, tuple):
        if len(icon_def) != 2:
            raise ValueError(f"Icon tuple must have exactly 2 elements: {icon_def}")

        component_name, icon_name = icon_def

        if not isinstance(component_name, str) or not isinstance(icon_name, str):
            raise ValueError(f"Both elements of icon tuple must be strings: {icon_def}")

        if not component_name.strip() or not icon_name.strip():
            raise ValueError(f"Icon tuple elements cannot be empty: {icon_def}")

        return component_name.strip(), icon_name.strip()

    elif isinstance(icon_def, str):
        icon_name = icon_def.strip()

        if not validate_icon_name(icon_name):
            raise ValueError(f"Invalid icon name: {icon_name}")

        # Extract component name from icon name
        if ":" in icon_name:
            # Prefixed icon: use part after colon
            _, component_name = icon_name.split(":", 1)
        else:
            # Local file path: extract filename without extension
            import os

            component_name = os.path.splitext(os.path.basename(icon_name))[0]

        return component_name, icon_name

    else:
        raise ValueError(f"Icon definition must be string or tuple: {icon_def}")


def parse_icon_definitions(icon_defs: List[IconDefinition]) -> Dict[str, str]:
    """
    Parse a list of icon definitions into a mapping of component names to icon names.

    Args:
        icon_defs: List of icon definitions (strings or tuples)

    Returns:
        Dictionary mapping component names to icon names

    Raises:
        ValueError: If there are duplicate component names or invalid definitions
    """
    component_map = {}

    for icon_def in icon_defs:
        try:
            component_name, icon_name = normalize_icon_definition(icon_def)

            # Check for duplicate component names
            if component_name in component_map:
                raise ValueError(
                    f"Duplicate component name '{component_name}': "
                    f"'{component_map[component_name]}' and '{icon_name}'"
                )

            component_map[component_name] = icon_name

        except ValueError as e:
            raise ValueError(f"Invalid icon definition {icon_def}: {e}")

    return component_map


def get_icon_names_from_definitions(icon_defs: List[IconDefinition]) -> List[str]:
    """
    Extract all unique icon names from icon definitions.

    Args:
        icon_defs: List of icon definitions

    Returns:
        List of unique icon names for building sprites
    """
    icon_names = set()

    for icon_def in icon_defs:
        try:
            _, icon_name = normalize_icon_definition(icon_def)
            icon_names.add(icon_name)
        except ValueError:
            # Skip invalid definitions
            continue

    return sorted(icon_names)


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


def sanitize_html_attributes(attrs: dict) -> dict:
    """
    Sanitize HTML attributes for safe inclusion in templates.

    Args:
        attrs: Dictionary of attribute names to values

    Returns:
        Dictionary of sanitized attributes
    """
    sanitized = {}

    for key, value in attrs.items():
        # Skip None, False, or empty string values
        if value in (None, False, ""):
            continue

        # Convert True to empty string (boolean attribute)
        if value is True:
            sanitized[key] = ""
        else:
            # Convert to string and escape quotes
            str_value = str(value)
            sanitized[key] = str_value.replace('"', "&quot;")

    return sanitized


def build_html_attributes(attrs: dict) -> str:
    """
    Build HTML attributes string from a dictionary.

    Args:
        attrs: Dictionary of attribute names to values

    Returns:
        HTML attributes string (e.g., 'class="foo" id="bar"')
    """
    sanitized = sanitize_html_attributes(attrs)

    attr_parts = []
    for key, value in sanitized.items():
        if value == "":
            # Boolean attribute
            attr_parts.append(key)
        else:
            attr_parts.append(f'{key}="{value}"')

    return " ".join(attr_parts)


def merge_css_classes(*class_lists) -> str:
    """
    Merge multiple CSS class lists into a single space-separated string.

    Args:
        *class_lists: Variable number of class lists (strings or iterables)

    Returns:
        Space-separated string of unique CSS classes
    """
    all_classes = set()

    for class_list in class_lists:
        if not class_list:
            continue

        if isinstance(class_list, str):
            classes = class_list.split()
        else:
            classes = list(class_list)

        for cls in classes:
            if cls and isinstance(cls, str):
                all_classes.add(cls.strip())

    return " ".join(sorted(all_classes))


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
