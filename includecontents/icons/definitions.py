"""
Icon definition parsing and normalization utilities.
"""

import os
from dataclasses import dataclass
from typing import Dict, List, Tuple, Union

from .validation import validate_icon_name

IconDefinition = Union[str, Tuple[str, str]]


@dataclass(frozen=True)
class Icon:
    """Internal representation of an icon definition."""

    component_name: str  # The name used in templates (e.g., "home")
    icon_source: str  # The icon source (e.g., "mdi:home" or "icons/home.svg")

    @classmethod
    def from_definition(cls, definition: IconDefinition) -> "Icon":
        """Create an Icon from various definition formats."""
        component_name, icon_source = normalize_icon_definition(definition)
        return cls(component_name=component_name, icon_source=icon_source)


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
    icons = []

    for icon_def in icon_defs:
        try:
            icon = Icon.from_definition(icon_def)

            # Check for duplicate component names
            if icon.component_name in component_map:
                raise ValueError(
                    f"Duplicate component name '{icon.component_name}': "
                    f"'{component_map[icon.component_name]}' and '{icon.icon_source}'"
                )

            component_map[icon.component_name] = icon.icon_source
            icons.append(icon)

        except ValueError as e:
            raise ValueError(f"Invalid icon definition {icon_def}: {e}")

    return component_map


def parse_icon_definitions_to_icons(icon_defs: List[IconDefinition]) -> List[Icon]:
    """
    Parse a list of icon definitions into Icon objects.

    Args:
        icon_defs: List of icon definitions (strings or tuples)

    Returns:
        List of Icon objects

    Raises:
        ValueError: If there are duplicate component names or invalid definitions
    """
    icons = []
    seen_names = set()

    for icon_def in icon_defs:
        try:
            icon = Icon.from_definition(icon_def)

            # Check for duplicate component names
            if icon.component_name in seen_names:
                # Find the existing icon with this name for better error message
                existing = next(
                    i for i in icons if i.component_name == icon.component_name
                )
                raise ValueError(
                    f"Duplicate component name '{icon.component_name}': "
                    f"'{existing.icon_source}' and '{icon.icon_source}'"
                )

            seen_names.add(icon.component_name)
            icons.append(icon)

        except ValueError as e:
            raise ValueError(f"Invalid icon definition {icon_def}: {e}")

    return icons


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
