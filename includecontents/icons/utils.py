"""
Backward compatibility module for icon utilities.

This module re-exports all utilities from the reorganized focused modules
to maintain backward compatibility with existing code.
"""

# Re-export everything from focused modules for backward compatibility
from .definitions import (
    Icon,
    IconDefinition,
    get_icon_names_from_definitions,
    normalize_icon_definition,
    parse_icon_definitions,
    parse_icon_definitions_to_icons,
)
from .html import (
    build_html_attributes,
    merge_css_classes,
    sanitize_html_attributes,
)
from .symbols import (
    get_icon_info_from_symbol_id,
    icon_name_to_symbol_id,
    symbol_id_to_icon_name,
)
from .validation import (
    extract_icon_prefixes,
    group_icons_by_prefix,
    parse_icon_names,
    validate_icon_name,
)

# Alias for the most commonly used function
format_attributes = build_html_attributes

__all__ = [
    # Definitions module
    "Icon",
    "IconDefinition",
    "get_icon_names_from_definitions",
    "normalize_icon_definition",
    "parse_icon_definitions",
    "parse_icon_definitions_to_icons",
    # HTML module
    "build_html_attributes",
    "format_attributes",
    "merge_css_classes",
    "sanitize_html_attributes",
    # Symbols module
    "get_icon_info_from_symbol_id",
    "icon_name_to_symbol_id",
    "symbol_id_to_icon_name",
    # Validation module
    "extract_icon_prefixes",
    "group_icons_by_prefix",
    "parse_icon_names",
    "validate_icon_name",
]
