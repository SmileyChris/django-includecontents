"""Shared helpers for enum-style component props."""

from __future__ import annotations

import difflib
from typing import Any, Optional, Sequence, Tuple


def parse_enum_definition(default: Any) -> Tuple[Tuple[str, ...], bool]:
    """Return (allowed_values, required) for a props default string.

    The convention matches the Django implementation: comma-separated values
    indicate an enum; a leading empty item (",value") means the prop is optional.
    """

    if not isinstance(default, str):
        return (), False
    if "," not in default:
        return (), False

    # Allow simple comma-separated lists; whitespace trims are handled here.
    raw_parts = [part.strip() for part in default.split(",")]
    # If every part was empty we treat it as non-enum.
    if all(part == "" for part in raw_parts):
        return (), False

    allowed = tuple(part for part in raw_parts if part)
    required = bool(raw_parts and raw_parts[0])
    return allowed, required


def normalize_enum_values(value: Any) -> list[str]:
    """Normalize incoming values into a list of individual enum tokens."""

    if value in (None, "", False):
        return []
    if isinstance(value, (list, tuple, set)):
        tokens: list[str] = []
        for item in value:
            tokens.extend(str(item).split())
        return [token for token in tokens if token]
    return [token for token in str(value).split() if token]


def build_enum_flag_key(prop_name: str, enum_value: str) -> Optional[str]:
    """Build the camelCase flag key used for boolean helpers (e.g. variantPrimary)."""

    if not enum_value:
        return None
    parts = enum_value.split("-")
    camel_value = parts[0] + "".join(part.capitalize() for part in parts[1:])
    if not camel_value:
        return None
    return f"{prop_name}{camel_value[0].upper()}{camel_value[1:]}"


def suggest_enum_value(
    invalid_value: str, allowed_values: Sequence[str]
) -> Optional[str]:
    """Suggest the closest valid enum value based on string similarity."""

    if not allowed_values or not invalid_value:
        return None

    invalid_lower = invalid_value.lower()
    for value in allowed_values:
        if value.lower() == invalid_lower:
            return value

    matches = difflib.get_close_matches(
        invalid_lower,
        [value.lower() for value in allowed_values],
        n=1,
        cutoff=0.3,
    )
    if matches:
        match_lower = matches[0]
        for value in allowed_values:
            if value.lower() == match_lower:
                return value
    return None


__all__ = [
    "parse_enum_definition",
    "normalize_enum_values",
    "build_enum_flag_key",
    "suggest_enum_value",
]
