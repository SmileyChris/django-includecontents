"""
Core fetch/build/hashing logic for SVG icon sprites.
"""

import hashlib
import json
import os
import re
from collections import defaultdict
from typing import Dict, List, Optional, Tuple
from urllib.error import URLError
from urllib.parse import urljoin
from urllib.request import urlopen
from xml.etree import ElementTree as ET

from django.conf import settings

from .exceptions import (
    IconNotFoundError,
    IconBuildError,
    IconConfigurationError,
    IconAPIError,
)


# Import Django cache integration for better caching
from .cache import sprite_cache


def find_source_svg(path: str) -> Optional[str]:
    """
    Find a source SVG file using Django's staticfiles finders.

    Uses standard Django staticfiles finders but ensures we get actual
    source SVG files, not generated sprites.

    Args:
        path: Static file path to find

    Returns:
        Absolute path to the found file, or None if not found
    """
    from django.contrib.staticfiles import finders

    # First try standard Django finder
    result = finders.find(path)

    # Handle case where find() returns a list (shouldn't happen but be safe)
    if isinstance(result, list):
        result = result[0] if result else None

    # Verify it's not a generated sprite file
    if result and os.path.basename(result).startswith("sprite-"):
        # This is a generated sprite, look for the actual source
        # by checking finders directly
        for finder in finders.get_finders():
            # Skip our own sprite finder
            if finder.__class__.__name__ == "IconSpriteFinder":
                continue
            try:
                found = finder.find(path, find_all=False)
                if found and not os.path.basename(found).startswith("sprite-"):
                    return found
            except Exception:
                continue
        return None

    return result


def generate_icon_hash(icons: List[str]) -> str:
    """
    Generate a deterministic hash for a list of icons.

    Args:
        icons: List of icon names (e.g., ["mdi:home", "tabler:calendar"])

    Returns:
        First 12 characters of SHA-256 hash
    """
    # Sort icons alphabetically for deterministic ordering
    sorted_icons = sorted(icons)

    # Create newline-separated string
    icon_string = "\n".join(sorted_icons)

    # Generate SHA-256 hash
    hash_obj = hashlib.sha256(icon_string.encode("utf-8"))

    # Return first 12 characters of hex digest
    return hash_obj.hexdigest()[:12]


def is_drawing_element(element):
    """
    Check if an element is an essential SVG drawing element.

    Args:
        element: ElementTree element to check

    Returns:
        True if element should be kept, False otherwise
    """
    # Essential SVG drawing elements
    drawing_elements = {
        "path",
        "g",
        "circle",
        "rect",
        "ellipse",
        "line",
        "polyline",
        "polygon",
        "text",
        "tspan",
        "use",
        "image",
        "clipPath",
        "mask",
        "pattern",
        "defs",
        "linearGradient",
        "radialGradient",
        "stop",
        "filter",
        "feGaussianBlur",
        "feOffset",
        "feBlend",
        "feMerge",
        "feMergeNode",
        "feColorMatrix",
        "feComponentTransfer",
        "feComposite",
        "feConvolveMatrix",
        "feDiffuseLighting",
        "feDisplacementMap",
        "feFlood",
        "feImage",
        "feMorphology",
        "feSpecularLighting",
        "feTile",
        "feTurbulence",
    }

    # Remove namespace prefix if present (e.g., 'svg:path' -> 'path')
    tag = element.tag.split("}")[-1] if "}" in element.tag else element.tag

    return tag in drawing_elements


def clean_svg_for_sprite(element):
    """
    Clean an SVG element for use in a sprite sheet, removing all non-essential elements.

    Args:
        element: ElementTree element to clean

    Returns:
        Cleaned element suitable for sprite usage, or None if element should be removed
    """
    # Check if this element should be kept
    if not is_drawing_element(element):
        return None

    # Create a new element without namespace to avoid ns0: prefixes
    # Extract the local tag name (without namespace)
    tag = element.tag.split("}")[-1] if "}" in element.tag else element.tag

    # Create new element with clean tag
    new_element = ET.Element(tag)

    # Copy attributes, filtering out problematic ones
    problematic_attrs = {
        "width",
        "height",
        "x",
        "y",  # Positioning/sizing handled by symbol
        "class",  # CSS classes may not exist in sprite context
        "id",  # IDs can conflict when multiple sprites exist
    }

    for attr, value in element.attrib.items():
        # Special handling for style attribute - keep it ONLY if it uses CSS variables
        if attr == "style":
            if "var(--" in value:
                new_element.set(attr, value)
            continue
        # Skip if it's a problematic attribute
        if attr in problematic_attrs:
            continue
        # Skip if it has a namespace prefix (contains ':' or '}')
        if ":" in attr or "}" in attr:
            continue
        # Keep the attribute
        new_element.set(attr, value)

    # Copy text content if present
    if element.text:
        new_element.text = element.text
    if element.tail:
        new_element.tail = element.tail

    # Recursively clean child elements
    for child in element:
        cleaned_child = clean_svg_for_sprite(child)
        if cleaned_child is not None:
            new_element.append(cleaned_child)

    return new_element


def parse_svg_content(svg_content: str, svg_path: str) -> Dict[str, str]:
    """
    Parse SVG content and extract icon data, cleaning it for sprite usage.

    Args:
        svg_content: Raw SVG content string
        svg_path: Path to SVG file (for error reporting)

    Returns:
        Dictionary with SVG data (body, viewBox, width, height)

    Raises:
        ValueError: If SVG content is invalid
    """
    # Clean up the SVG content and parse it
    svg_content = svg_content.strip()
    root = ET.fromstring(svg_content)

    # Extract viewBox (default to 0 0 24 24 if not found)
    viewbox = root.get("viewBox", "0 0 24 24")

    # Extract width/height (default to 24 if not found)
    width = root.get("width", "24")
    height = root.get("height", "24")

    # Try to parse numeric values (keep as strings in return)
    try:
        width_num = float(re.sub(r"[^\d.]", "", str(width))) if width else 24
        height_num = float(re.sub(r"[^\d.]", "", str(height))) if height else 24
        # Convert back to strings for consistency
        width = str(int(width_num))
        height = str(int(height_num))
    except (ValueError, TypeError):
        width, height = "24", "24"

    # Clean the SVG content for sprite usage
    # Clean each child element for sprite usage, collecting only drawing elements
    cleaned_inner_elements = []
    for child in root:
        cleaned_child = clean_svg_for_sprite(child)
        if cleaned_child is not None:
            # Convert cleaned child to string
            cleaned_inner_elements.append(
                ET.tostring(cleaned_child, encoding="unicode")
            )

    # Join all inner elements
    body = "".join(cleaned_inner_elements).strip()

    # If no drawing elements remain after cleaning, return empty body
    # (Don't fall back to regex which would include non-drawing elements)

    return {"body": body, "viewBox": viewbox, "width": width, "height": height}


def load_local_svg(svg_path: str) -> Dict[str, str]:
    """
    Load SVG data from Django's static files.

    Args:
        svg_path: Path to SVG file in static files

    Returns:
        Dictionary with SVG data (body, viewBox, width, height)

    Raises:
        FileNotFoundError: If SVG file is not found in static files
        ValueError: If SVG content is invalid
    """
    # Load from static files using specialized finder that skips IconSpriteFinder
    svg_file_path = find_source_svg(svg_path)

    if svg_file_path is None:
        raise IconNotFoundError(f"SVG file not found in static files: {svg_path}")

    # Read the SVG file content
    try:
        with open(svg_file_path, "r", encoding="utf-8") as f:
            svg_content = f.read()
    except Exception as e:
        raise IconNotFoundError(f"Failed to read SVG file: {svg_path} - {e}")

    # Parse SVG content using helper function
    try:
        return parse_svg_content(svg_content, svg_path)
    except ET.ParseError as e:
        raise IconBuildError(f"Invalid SVG content in {svg_path}: {e}")


def get_cached_iconify_icon(
    prefix: str, icon_name: str, cache_static_path: str
) -> Optional[Dict[str, str]]:
    """
    Try to load a cached Iconify icon from static files.

    Args:
        prefix: Icon prefix (e.g., "mdi", "tabler")
        icon_name: Icon name without prefix (e.g., "home")
        cache_static_path: Static files path for cache (e.g., ".icon_cache")

    Returns:
        Icon data dictionary or None if not cached
    """
    if not cache_static_path:
        return None

    # Build cache file path: .icon_cache/mdi/home.json
    cache_file = f"{cache_static_path}/{prefix}/{icon_name}.json"

    # Try to find in static files
    cached_file = find_source_svg(cache_file)
    if not cached_file:
        return None

    try:
        with open(cached_file, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        # Invalid or corrupted cache file, ignore it
        return None


def save_iconify_icon_to_cache(
    prefix: str, icon_name: str, icon_data: Dict[str, str], cache_root: str
) -> None:
    """
    Save an Iconify icon to the filesystem cache.

    Args:
        prefix: Icon prefix (e.g., "mdi", "tabler")
        icon_name: Icon name without prefix (e.g., "home")
        icon_data: Icon data dictionary with body, viewBox, etc.
        cache_root: Filesystem path for writing cache files
    """
    if not cache_root:
        return

    from pathlib import Path

    # Build cache file path
    cache_dir = Path(cache_root) / prefix
    cache_file = cache_dir / f"{icon_name}.json"

    # Create directory if it doesn't exist
    cache_dir.mkdir(parents=True, exist_ok=True)

    # Write icon data to cache
    try:
        with open(cache_file, "w", encoding="utf-8") as f:
            json.dump(icon_data, f, separators=(",", ":"))
    except IOError:
        # Failed to write cache, silently ignore
        pass


def fetch_iconify_icons(
    prefix: str,
    icon_names: List[str],
    api_base: str,
    cache_root: Optional[str] = None,
    cache_static_path: Optional[str] = None,
) -> Dict[str, str]:
    """
    Fetch icon data from Iconify API for a specific prefix, using cache when available.

    Args:
        prefix: Icon prefix (e.g., "mdi", "tabler")
        icon_names: List of icon names without prefix (e.g., ["home", "account"])
        api_base: Base URL for Iconify API
        cache_root: Optional filesystem path for writing cached icons
        cache_static_path: Optional static files path for reading cached icons

    Returns:
        Dictionary mapping icon names to their SVG bodies

    Raises:
        URLError: If API request fails
        ValueError: If API response is invalid
    """
    icon_data = {}
    icons_to_fetch = []

    # First, check cache for each icon
    for icon_name in icon_names:
        if cache_static_path:
            cached_icon = get_cached_iconify_icon(prefix, icon_name, cache_static_path)
            if cached_icon:
                icon_data[icon_name] = cached_icon
                continue

        # Icon not in cache, need to fetch it
        icons_to_fetch.append(icon_name)

    # If all icons were cached, return early
    if not icons_to_fetch:
        return icon_data

    # Build API URL for missing icons
    icons_param = ",".join(icons_to_fetch)
    url = urljoin(api_base.rstrip("/") + "/", f"{prefix}.json?icons={icons_param}")

    try:
        with urlopen(url) as response:
            data = json.loads(response.read().decode("utf-8"))
    except (URLError, json.JSONDecodeError) as e:
        raise IconAPIError(f"Failed to fetch icons from {url}: {e}")

    # Handle case where API returns just an error code (e.g., 404 for invalid prefix)
    if not isinstance(data, dict):
        # Invalid prefix returns just an integer like 404
        if data == 404:
            # All requested icons are not found for this invalid prefix
            missing_icons = [f"{prefix}:{name}" for name in icons_to_fetch]
            if len(missing_icons) == 1:
                raise IconNotFoundError(
                    f"Icon '{missing_icons[0]}' not found (invalid icon prefix '{prefix}')"
                )
            else:
                icons_list = ", ".join(f"'{icon}'" for icon in missing_icons)
                raise IconNotFoundError(
                    f"Icons not found (invalid icon prefix '{prefix}'): {icons_list}"
                )
        else:
            raise IconAPIError(
                f"Invalid API response from {url}: expected JSON object, got {type(data).__name__}"
            )

    if "icons" not in data:
        raise IconAPIError(f"Invalid API response from {url}: missing 'icons' field")

    icons = data["icons"]

    # Track missing icons to report them all at once
    missing_icons = []
    icons_without_body = []

    # Check for icons explicitly marked as not found by the API
    not_found_list = data.get("not_found", [])
    if not_found_list:
        for icon_name in not_found_list:
            missing_icons.append(f"{prefix}:{icon_name}")

    for icon_name in icons_to_fetch:
        # Skip if already marked as not found
        if icon_name in not_found_list:
            continue

        if icon_name not in icons:
            # Only add to missing if not already in not_found list
            full_name = f"{prefix}:{icon_name}"
            if full_name not in missing_icons:
                missing_icons.append(full_name)
            continue

        icon_info = icons[icon_name]
        if "body" not in icon_info:
            icons_without_body.append(f"{prefix}:{icon_name}")
            continue

        # Get the SVG body
        body = icon_info["body"]

        # Add default viewBox if not present
        viewbox = icon_info.get("viewBox", "0 0 24 24")

        # Create icon data
        single_icon_data = {
            "body": body,
            "viewBox": viewbox,
            "width": icon_info.get("width", 24),
            "height": icon_info.get("height", 24),
        }

        # Store in result
        icon_data[icon_name] = single_icon_data

        # Save to cache if configured
        if cache_root:
            save_iconify_icon_to_cache(prefix, icon_name, single_icon_data, cache_root)

    # Report all missing icons at once for better developer experience
    errors = []
    if missing_icons:
        if len(missing_icons) == 1:
            errors.append(
                f"Icon '{missing_icons[0]}' not found in Iconify API response"
            )
        else:
            icons_list = ", ".join(f"'{icon}'" for icon in missing_icons)
            errors.append(f"Icons not found in Iconify API response: {icons_list}")

    if icons_without_body:
        if len(icons_without_body) == 1:
            errors.append(f"Icon '{icons_without_body[0]}' has no body in API response")
        else:
            icons_list = ", ".join(f"'{icon}'" for icon in icons_without_body)
            errors.append(f"Icons without body in API response: {icons_list}")

    if errors:
        raise IconNotFoundError("; ".join(errors))

    return icon_data


def is_local_svg_path(icon_name: str) -> bool:
    """Check if an icon name is a local SVG file path."""
    # If it contains a colon, check if it's a local prefix
    if ":" in icon_name:
        prefix = icon_name.split(":", 1)[0]
        return prefix in ["local", "file", "svg"]

    # If no colon, check if it looks like a file path
    return icon_name.endswith(".svg") or "/" in icon_name


def build_sprite(
    icons: List[str],
    api_base: str = "https://api.iconify.design",
    component_map: Optional[Dict[str, str]] = None,
    cache_root: Optional[str] = None,
    cache_static_path: Optional[str] = None,
) -> str:
    """
    Build an SVG sprite sheet from a list of icon names (Iconify or local SVG files).

    Args:
        icons: List of icon names (e.g., ["mdi:home", "icons/my-icon.svg", "static/custom.svg"])
        api_base: Base URL for Iconify API
        component_map: Optional mapping from component names to icon names for symbol IDs
        cache_root: Optional filesystem path for writing cached icons
        cache_static_path: Optional static files path for reading cached icons

    Returns:
        Complete SVG sprite sheet as string

    Raises:
        ValueError: If icon names are invalid or API requests fail
        subprocess.CalledProcessError: If SVG optimization fails
    """
    if not icons:
        return '<svg style="display:none"></svg>'

    # If no component map provided, generate one from the icon names
    if component_map is None:
        from .utils import normalize_icon_definition

        component_map = {}
        for icon in icons:
            try:
                component_name, icon_name = normalize_icon_definition(icon)
                component_map[component_name] = icon_name
            except ValueError:
                # If normalization fails, fall back to sanitized name
                from .utils import icon_name_to_symbol_id

                component_map[icon_name_to_symbol_id(icon)] = icon

    # Separate icons by type (Iconify vs local)
    iconify_groups = defaultdict(list)
    local_icons = []

    for icon in icons:
        # Check if this is a local SVG file path
        if is_local_svg_path(icon):
            # Handle local SVG files - should be direct paths like 'icons/logo.svg'
            svg_path = icon
            local_icons.append((icon, svg_path))
        else:
            # This should be an Iconify icon
            if ":" not in icon:
                raise IconConfigurationError(
                    f"Invalid icon name '{icon}': must include prefix (e.g., 'mdi:home') or be a valid SVG path"
                )

            prefix, name = icon.split(":", 1)
            iconify_groups[prefix].append(name)

    # Fetch Iconify icon data - fail fast on any errors
    all_icon_data = {}
    for prefix, names in iconify_groups.items():
        icon_data = fetch_iconify_icons(
            prefix, names, api_base, cache_root, cache_static_path
        )
        for name, data in icon_data.items():
            full_name = f"{prefix}:{name}"
            all_icon_data[full_name] = data

    # Load local SVG files - fail fast on any errors
    for full_name, svg_path in local_icons:
        svg_data = load_local_svg(svg_path)
        all_icon_data[full_name] = svg_data

    # Build sprite symbols - ensure all icons are available
    # First, check for all missing icons to provide a comprehensive error message
    missing_icons = []
    for icon in sorted(icons):  # Sort for deterministic output
        if icon not in all_icon_data:
            missing_icons.append(icon)

    if missing_icons:
        if len(missing_icons) == 1:
            raise IconNotFoundError(
                f"Icon '{missing_icons[0]}' not found in fetched data"
            )
        else:
            icons_list = ", ".join(f"'{icon}'" for icon in missing_icons)
            raise IconNotFoundError(f"Icons not found in fetched data: {icons_list}")

    # Now build the symbols
    symbols = []
    for icon in sorted(icons):
        data = all_icon_data[icon]

        # Find component name for this icon from the map
        # Since we always have a component_map now, just look it up
        symbol_id = None
        for component_name, icon_name in component_map.items():
            if icon_name == icon:
                symbol_id = component_name
                break

        # This should always find a match since we built the map from these icons
        if symbol_id is None:
            raise IconBuildError(f"Icon '{icon}' not found in component map")

        # Create symbol element
        symbol = f'''<symbol id="{symbol_id}" viewBox="{data["viewBox"]}">{data["body"]}</symbol>'''
        symbols.append(symbol)

    # Wrap all symbols in SVG with proper namespace
    sprite_content = (
        '<svg xmlns="http://www.w3.org/2000/svg" style="display:none">\n'
        + "\n".join(symbols)
        + "\n</svg>"
    )

    return sprite_content


def get_sprite_filename(sprite_hash: str) -> str:
    """
    Generate sprite filename from hash.

    Args:
        sprite_hash: Hash of sprite content

    Returns:
        Filename for sprite
    """
    return f"sprite-{sprite_hash}.svg"


def cache_sprite(sprite_hash: str, content: str) -> None:
    """
    Store sprite content in memory cache.

    Args:
        sprite_hash: Hash of sprite content
        content: SVG sprite content
    """
    sprite_cache.set(sprite_hash, content)


def get_cached_sprite(sprite_hash: str) -> Optional[str]:
    """
    Retrieve sprite content from memory cache.

    Args:
        sprite_hash: Hash of sprite content

    Returns:
        Sprite content or None if not found
    """
    return sprite_cache.get(sprite_hash)


def clear_sprite_cache() -> None:
    """Clear the memory cache."""
    sprite_cache.clear()


def get_sprite_settings() -> Dict:
    """
    Get icon sprite settings from Django settings with defaults.

    Returns:
        Dictionary with sprite configuration

    Raises:
        ValueError: If icon definitions contain duplicate component names
    """
    default_settings = {
        "icons": [],
        "api_base": "https://api.iconify.design",
        "dev_mode": getattr(settings, "DEBUG", True),
        "cache_timeout": 3600,
        "api_cache_root": None,  # Filesystem path for writing cached icons
        "api_cache_static_path": None,  # Static files path for reading cached icons
    }

    user_settings = getattr(settings, "INCLUDECONTENTS_ICONS", {})
    merged_settings = {**default_settings, **user_settings}

    # Validate icon definitions for duplicate component names
    icon_definitions = merged_settings.get("icons", [])
    if icon_definitions:
        from .utils import parse_icon_definitions

        try:
            parse_icon_definitions(icon_definitions)
        except ValueError as e:
            raise IconConfigurationError(
                f"Invalid INCLUDECONTENTS_ICONS configuration: {e}"
            )

    return merged_settings


def get_sprite_hash() -> str:
    """
    Get the sprite hash for the current icon configuration without building the sprite.

    This is much more efficient for template rendering where only the hash is needed
    for URL generation.

    Returns:
        Sprite hash string
    """
    sprite_settings = get_sprite_settings()
    icon_definitions = sprite_settings["icons"]

    if not icon_definitions:
        return ""

    # Extract actual icon names from definitions (handles tuples)
    from .utils import get_icon_names_from_definitions

    icons = get_icon_names_from_definitions(icon_definitions)

    if not icons:
        return ""

    # Generate hash for current icon set
    return generate_icon_hash(icons)


def get_or_create_sprite() -> Tuple[str, str]:
    """
    Get or create sprite sheet, handling caching and persistence.

    Returns:
        Tuple of (sprite_hash, sprite_content, was_created)
        was_created is True if sprite was newly built, False if from cache
    """
    sprite_settings = get_sprite_settings()
    icon_definitions = sprite_settings["icons"]

    if not icon_definitions:
        return "", '<svg style="display:none"></svg>'

    # Extract actual icon names from definitions (handles tuples)
    from .utils import get_icon_names_from_definitions

    icons = get_icon_names_from_definitions(icon_definitions)

    if not icons:
        return "", '<svg style="display:none"></svg>'

    # Generate hash for current icon set
    sprite_hash = generate_icon_hash(icons)

    # Try to load from cache first
    cached_content = get_cached_sprite(sprite_hash)
    if cached_content:
        return sprite_hash, cached_content

    # Build new sprite
    try:
        # Get component map for proper symbol IDs
        from .utils import parse_icon_definitions

        try:
            component_map = parse_icon_definitions(icon_definitions)
        except ValueError:
            # If parsing fails, use None (fallback to icon name conversion)
            component_map = None

        sprite_content = build_sprite(
            icons,
            sprite_settings["api_base"],
            component_map,
            sprite_settings.get("api_cache_root"),
            sprite_settings.get("api_cache_static_path"),
        )

        # Cache the result in memory
        cache_sprite(sprite_hash, sprite_content)

        return sprite_hash, sprite_content

    except Exception as e:
        # Fail loudly - a broken sprite build is a serious configuration error
        # that should be fixed immediately, not silently ignored
        if isinstance(
            e, (IconNotFoundError, IconBuildError, IconConfigurationError, IconAPIError)
        ):
            raise  # Re-raise our custom exceptions as-is
        raise IconBuildError(f"Failed to build icon sprite: {e}") from e
