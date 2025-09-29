"""
HTML and attribute utilities for icon rendering.
"""

from typing import Iterable, Union

try:
    from django.utils.html import conditional_escape
except ImportError:
    # Fallback for environments without Django
    def conditional_escape(value):
        return str(value).replace('"', "&quot;")


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
            # Convert to string and escape for HTML safety
            sanitized[key] = conditional_escape(str(value))

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


def merge_css_classes(*class_lists: Union[str, Iterable[str]]) -> str:
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
