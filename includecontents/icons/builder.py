"""
Core fetch/build/hashing logic for SVG icon sprites.
"""

import hashlib
import inspect
import json
import os
import re
import subprocess
import tempfile
from collections import defaultdict
from typing import Dict, List, Optional, Tuple
from urllib.error import URLError
from urllib.parse import urljoin
from urllib.request import urlopen
from xml.etree import ElementTree as ET

from django.conf import settings
from django.contrib.staticfiles.finders import get_finder


def find_source_svg(path: str) -> Optional[str]:
    """
    Find a source SVG file using staticfiles finders, but skip IconSpriteFinder.

    This prevents conflicts where IconSpriteFinder adds source SVG files to ignore
    patterns, making them unfindable by the regular finders.find() function.

    Args:
        path: Static file path to find

    Returns:
        Absolute path to the found file, or None if not found
    """
    for finder_path in getattr(settings, "STATICFILES_FINDERS", []):
        # Skip our own IconSpriteFinder to avoid ignore pattern conflicts
        if "IconSpriteFinder" in finder_path:
            continue

        try:
            finder = get_finder(finder_path)
            result = finder.find(path, find_all=False)
            if result:
                return result
        except Exception:
            # Continue to next finder if this one fails
            continue

    return None


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
        "style",  # Inline styles can conflict
        "class",  # CSS classes may not exist in sprite context
        "id",  # IDs can conflict when multiple sprites exist
    }

    for attr, value in element.attrib.items():
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
        raise FileNotFoundError(f"SVG file not found in static files: {svg_path}")

    # Read the SVG file content
    try:
        with open(svg_file_path, "r", encoding="utf-8") as f:
            svg_content = f.read()
    except Exception as e:
        raise FileNotFoundError(f"Failed to read SVG file: {svg_path} - {e}")

    # Parse SVG content using helper function
    try:
        return parse_svg_content(svg_content, svg_path)
    except ET.ParseError as e:
        raise ValueError(f"Invalid SVG content in {svg_path}: {e}")


def fetch_iconify_icons(
    prefix: str, icon_names: List[str], api_base: str
) -> Dict[str, str]:
    """
    Fetch icon data from Iconify API for a specific prefix.

    Args:
        prefix: Icon prefix (e.g., "mdi", "tabler")
        icon_names: List of icon names without prefix (e.g., ["home", "account"])
        api_base: Base URL for Iconify API

    Returns:
        Dictionary mapping icon names to their SVG bodies

    Raises:
        URLError: If API request fails
        ValueError: If API response is invalid
    """
    # Build API URL
    icons_param = ",".join(icon_names)
    url = urljoin(api_base.rstrip("/") + "/", f"{prefix}.json?icons={icons_param}")

    try:
        with urlopen(url) as response:
            data = json.loads(response.read().decode("utf-8"))
    except (URLError, json.JSONDecodeError) as e:
        raise URLError(f"Failed to fetch icons from {url}: {e}")

    if "icons" not in data:
        raise ValueError(f"Invalid API response from {url}: missing 'icons' field")

    icon_data = {}
    icons = data["icons"]

    for icon_name in icon_names:
        if icon_name not in icons:
            continue

        icon_info = icons[icon_name]
        if "body" not in icon_info:
            continue

        # Get the SVG body
        body = icon_info["body"]

        # Add default viewBox if not present
        viewbox = icon_info.get("viewBox", "0 0 24 24")

        # Store with viewBox info for later use
        icon_data[icon_name] = {
            "body": body,
            "viewBox": viewbox,
            "width": icon_info.get("width", 24),
            "height": icon_info.get("height", 24),
        }

    return icon_data


def is_local_svg_path(icon_name: str) -> bool:
    """Check if an icon name is a local SVG file path."""
    # If it contains a colon, check if it's a local prefix
    if ":" in icon_name:
        prefix = icon_name.split(":", 1)[0]
        return prefix in ["local", "file", "svg"]

    # If no colon, check if it looks like a file path
    return icon_name.endswith(".svg") or "/" in icon_name


def optimize_svg_content(svg_content: str, optimize_command: str) -> str:
    """
    Optimize SVG content using a shell command.

    Args:
        svg_content: Raw SVG content to optimize
        optimize_command: Shell command with {input} and {output} placeholders

    Returns:
        Optimized SVG content

    Raises:
        subprocess.CalledProcessError: If optimization command fails
        ValueError: If command format is invalid
    """
    if not optimize_command.strip():
        return svg_content

    # Validate command format
    if "{input}" not in optimize_command or "{output}" not in optimize_command:
        raise ValueError(
            "Optimization command must contain {input} and {output} placeholders"
        )

    # Create temporary files for input and output
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".svg", delete=False
    ) as input_file:
        input_file.write(svg_content)
        input_path = input_file.name

    try:
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".svg", delete=False
        ) as output_file:
            output_path = output_file.name

        # Format the command with actual file paths
        command = optimize_command.format(input=input_path, output=output_path)

        # Execute the optimization command
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=30,  # 30 second timeout for safety
        )

        # Check if command succeeded
        if result.returncode != 0:
            raise subprocess.CalledProcessError(
                result.returncode, command, output=result.stdout, stderr=result.stderr
            )

        # Read the optimized content
        with open(output_path, "r", encoding="utf-8") as f:
            optimized_content = f.read()

        return optimized_content

    finally:
        # Clean up temporary files
        try:
            os.unlink(input_path)
        except OSError:
            pass
        try:
            os.unlink(output_path)
        except OSError:
            pass


def build_sprite(
    icons: List[str],
    api_base: str = "https://api.iconify.design",
    optimize_command: str = "",
    component_map: Optional[Dict[str, str]] = None,
) -> str:
    """
    Build an SVG sprite sheet from a list of icon names (Iconify or local SVG files).

    Args:
        icons: List of icon names (e.g., ["mdi:home", "icons/my-icon.svg", "static/custom.svg"])
        api_base: Base URL for Iconify API
        optimize_command: Optional shell command for SVG optimization
        component_map: Optional mapping from component names to icon names for symbol IDs

    Returns:
        Complete SVG sprite sheet as string

    Raises:
        ValueError: If icon names are invalid or API requests fail
        subprocess.CalledProcessError: If SVG optimization fails
    """
    if not icons:
        return '<svg style="display:none"></svg>'

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
                raise ValueError(
                    f"Invalid icon name '{icon}': must include prefix (e.g., 'mdi:home') or be a valid SVG path"
                )

            prefix, name = icon.split(":", 1)
            iconify_groups[prefix].append(name)

    # Fetch Iconify icon data - fail fast on any errors
    all_icon_data = {}
    for prefix, names in iconify_groups.items():
        icon_data = fetch_iconify_icons(prefix, names, api_base)
        for name, data in icon_data.items():
            full_name = f"{prefix}:{name}"
            all_icon_data[full_name] = data

    # Load local SVG files - fail fast on any errors
    for full_name, svg_path in local_icons:
        svg_data = load_local_svg(svg_path)
        all_icon_data[full_name] = svg_data

    # Build sprite symbols - ensure all icons are available
    symbols = []
    for icon in sorted(icons):  # Sort for deterministic output
        if icon not in all_icon_data:
            raise ValueError(f"Icon '{icon}' not found in fetched data")

        data = all_icon_data[icon]

        # Determine symbol ID - use component name if available, otherwise convert icon name
        if component_map:
            # Find component name that maps to this icon
            symbol_id = None
            for component_name, icon_name in component_map.items():
                if icon_name == icon:
                    symbol_id = component_name
                    break

            # Fallback to converted icon name if not found in map
            if symbol_id is None:
                from .utils import icon_name_to_symbol_id

                symbol_id = icon_name_to_symbol_id(icon)
        else:
            # No component map, use converted icon name
            from .utils import icon_name_to_symbol_id

            symbol_id = icon_name_to_symbol_id(icon)

        # Create symbol element
        symbol = f'''<symbol id="{symbol_id}" viewBox="{data["viewBox"]}">{data["body"]}</symbol>'''
        symbols.append(symbol)

    # Wrap all symbols in SVG with proper namespace
    sprite_content = (
        '<svg xmlns="http://www.w3.org/2000/svg" style="display:none">\n'
        + "\n".join(symbols)
        + "\n</svg>"
    )

    # Apply SVG optimization if command is provided
    if optimize_command:
        sprite_content = optimize_svg_content(sprite_content, optimize_command)

    return sprite_content


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
        "storage": "includecontents.icons.storages.DjangoFileIconStorage",
        "storage_options": {
            "location": "icons/",
        },
        "dev_mode": getattr(settings, "DEBUG", True),
        "cache_timeout": 3600,
        "optimize_command": "",  # Optional SVG optimization command
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
            raise ValueError(f"Invalid INCLUDECONTENTS_ICONS configuration: {e}")

    return merged_settings


def get_icon_storage():
    """
    Get the configured storage backend instance.

    Returns:
        Storage backend instance
    """
    sprite_settings = get_sprite_settings()
    storage_class_path = sprite_settings["storage"]
    storage_options = sprite_settings.get("storage_options", {})

    # Import the storage class
    if isinstance(storage_class_path, str):
        from django.utils.module_loading import import_string

        storage_class = import_string(storage_class_path)

        # Handle storage classes that don't accept any options (like MemoryIconStorage)
        sig = inspect.signature(storage_class.__init__)
        # If __init__ only accepts 'self', don't pass any options
        if len(sig.parameters) == 1:  # Only 'self' parameter
            return storage_class()
        else:
            return storage_class(**storage_options)
    else:
        # Assume it's already an instance
        return storage_class_path


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

    # Try to load from storage first
    from .storage import cache_sprite, get_cached_sprite

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
            sprite_settings.get("optimize_command", ""),
            component_map,
        )

        # Cache the result in memory
        cache_sprite(sprite_hash, sprite_content)

        # Save to persistent storage if it doesn't exist
        from .storage import get_sprite_filename

        storage = get_icon_storage()
        sprite_filename = get_sprite_filename(sprite_hash)
        if not storage.exists(sprite_filename):
            storage.save(sprite_filename, sprite_content)

        return sprite_hash, sprite_content

    except Exception as e:
        print(f"Error building sprite: {e}")
        return sprite_hash, '<svg style="display:none"></svg>'
