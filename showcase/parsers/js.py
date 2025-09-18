"""
JavaScript parser for tailwind.config.js theme configurations.
"""

import re
import json
from typing import List, Dict, Any, Optional, Union
from pathlib import Path

from .base import BaseTokenParser
from ..models import DesignTokenInfo


class TailwindConfigParser(BaseTokenParser):
    """Parser for tailwind.config.js theme sections."""

    def can_parse(self, file_path: Path) -> bool:
        """Check if this parser can handle the given file."""
        filename = file_path.name.lower()
        return (
            filename in ['tailwind.config.js', 'tailwind.config.ts', 'tailwind.config.mjs'] or
            filename.startswith('tailwind.config.') and filename.endswith(('.js', '.ts', '.mjs'))
        )

    def parse(self, content: str) -> List[DesignTokenInfo]:
        """Parse JavaScript content for Tailwind theme configurations."""
        tokens = []

        try:
            # Extract the theme configuration from the JavaScript
            theme_config = self._extract_theme_config(content)

            if theme_config:
                # Parse the theme configuration recursively
                tokens.extend(self._parse_theme_object(theme_config))

        except Exception as e:
            print(f"Error parsing Tailwind config: {e}")

        return tokens

    def _extract_theme_config(self, content: str) -> Optional[Dict[str, Any]]:
        """Extract the theme configuration from JavaScript content."""
        try:
            # Try multiple approaches to extract theme config

            # Approach 1: Look for theme object in module.exports
            theme = self._extract_from_module_exports(content)
            if theme:
                return theme

            # Approach 2: Look for theme in export default
            theme = self._extract_from_export_default(content)
            if theme:
                return theme

            # Approach 3: Look for standalone theme object
            theme = self._extract_standalone_theme(content)
            if theme:
                return theme

        except Exception as e:
            print(f"Error extracting theme config: {e}")

        return None

    def _extract_from_module_exports(self, content: str) -> Optional[Dict[str, Any]]:
        """Extract theme from module.exports structure."""
        try:
            # Find module.exports = and extract the object with balanced braces
            start_pattern = re.search(r'module\.exports\s*=\s*\{', content)
            if not start_pattern:
                return None

            # Find the matching closing brace
            start_pos = start_pattern.end() - 1  # Position of opening brace
            config_str = self._extract_balanced_braces(content, start_pos)

            if config_str:
                return self._extract_theme_from_config_string(config_str)

        except Exception as e:
            print(f"Error extracting from module.exports: {e}")

        return None

    def _extract_from_export_default(self, content: str) -> Optional[Dict[str, Any]]:
        """Extract theme from export default structure."""
        try:
            # Find export default and extract the object with balanced braces
            start_pattern = re.search(r'export\s+default\s+\{', content)
            if not start_pattern:
                return None

            # Find the matching closing brace
            start_pos = start_pattern.end() - 1  # Position of opening brace
            config_str = self._extract_balanced_braces(content, start_pos)

            if config_str:
                return self._extract_theme_from_config_string(config_str)

        except Exception as e:
            print(f"Error extracting from export default: {e}")

        return None

    def _extract_balanced_braces(self, content: str, start_pos: int) -> Optional[str]:
        """Extract content between balanced braces starting at start_pos."""
        if start_pos >= len(content) or content[start_pos] != '{':
            return None

        brace_count = 0
        i = start_pos
        in_string = False
        string_char = None
        escape_next = False

        while i < len(content):
            char = content[i]

            if escape_next:
                escape_next = False
                i += 1
                continue

            if char == '\\':
                escape_next = True
                i += 1
                continue

            if not in_string:
                if char in ['"', "'", '`']:
                    in_string = True
                    string_char = char
                elif char == '{':
                    brace_count += 1
                elif char == '}':
                    brace_count -= 1
                    if brace_count == 0:
                        return content[start_pos:i + 1]
            else:
                if char == string_char:
                    in_string = False
                    string_char = None

            i += 1

        return None

    def _extract_standalone_theme(self, content: str) -> Optional[Dict[str, Any]]:
        """Extract standalone theme object."""
        # Pattern to match theme: { ... }
        theme_pattern = re.compile(
            r'theme\s*:\s*(\{.*?\})',
            re.DOTALL
        )

        match = theme_pattern.search(content)
        if match:
            theme_str = match.group(1)
            return self._parse_js_object(theme_str)

        return None

    def _extract_theme_from_config_string(self, config_str: str) -> Optional[Dict[str, Any]]:
        """Extract theme section from config object string."""
        try:
            # Find the theme property within the config
            theme_pattern = re.search(r'theme\s*:\s*\{', config_str)
            if not theme_pattern:
                return None

            # Find the matching closing brace
            start_pos = theme_pattern.end() - 1  # Position of opening brace
            theme_str = self._extract_balanced_braces(config_str, start_pos)

            if theme_str:
                return self._parse_js_object(theme_str)

        except Exception as e:
            print(f"Error extracting theme from config: {e}")

        return None

    def _parse_js_object(self, obj_str: str) -> Optional[Dict[str, Any]]:
        """Parse JavaScript object string to Python dict."""
        try:
            # Clean up the JavaScript object to make it JSON-parseable
            cleaned = self._clean_js_object(obj_str)

            # Try to parse as JSON
            return json.loads(cleaned)

        except (json.JSONDecodeError, Exception) as e:
            # If JSON parsing fails, try manual parsing
            return self._manual_parse_js_object(obj_str)

    def _clean_js_object(self, obj_str: str) -> str:
        """Clean JavaScript object string to be JSON-compatible."""
        # Remove JavaScript comments
        obj_str = re.sub(r'//.*$', '', obj_str, flags=re.MULTILINE)
        obj_str = re.sub(r'/\*.*?\*/', '', obj_str, flags=re.DOTALL)

        # Replace single quotes with double quotes
        obj_str = re.sub(r"'([^']*)'", r'"\1"', obj_str)

        # Handle unquoted object keys
        obj_str = re.sub(r'(\w+)\s*:', r'"\1":', obj_str)

        # Remove trailing commas
        obj_str = re.sub(r',\s*}', '}', obj_str)
        obj_str = re.sub(r',\s*]', ']', obj_str)

        # Handle function calls and expressions (replace with placeholders)
        obj_str = re.sub(r'\w+\([^)]*\)', '"__FUNCTION_CALL__"', obj_str)

        # Handle template literals
        obj_str = re.sub(r'`[^`]*`', '"__TEMPLATE_LITERAL__"', obj_str)

        return obj_str

    def _manual_parse_js_object(self, obj_str: str) -> Optional[Dict[str, Any]]:
        """Manually parse JavaScript object using improved nested structure handling."""
        result = {}

        try:
            obj_str = obj_str.strip()
            if obj_str.startswith('{'):
                obj_str = obj_str[1:]
            if obj_str.endswith('}'):
                obj_str = obj_str[:-1]

            # Find key-value pairs, handling nested objects properly
            i = 0
            while i < len(obj_str):
                # Skip whitespace
                while i < len(obj_str) and obj_str[i].isspace():
                    i += 1
                if i >= len(obj_str):
                    break

                # Find key (handle quoted and unquoted keys)
                key_start = i
                key = None

                if obj_str[i] in ['"', "'"]:
                    # Quoted key
                    quote_char = obj_str[i]
                    i += 1
                    key_start = i
                    while i < len(obj_str) and obj_str[i] != quote_char:
                        if obj_str[i] == '\\':  # Handle escaped characters
                            i += 1
                        i += 1
                    key = obj_str[key_start:i]
                    if i < len(obj_str):
                        i += 1  # Skip closing quote
                else:
                    # Unquoted key
                    while i < len(obj_str) and (obj_str[i].isalnum() or obj_str[i] in '_'):
                        i += 1
                    key = obj_str[key_start:i]

                if not key:  # No key found
                    i += 1
                    continue

                # Skip whitespace and colon
                while i < len(obj_str) and (obj_str[i].isspace() or obj_str[i] == ':'):
                    i += 1

                if i >= len(obj_str):
                    break

                # Find value (handling nested objects)
                value_start = i
                if obj_str[i] == '{':
                    # Handle nested object
                    brace_count = 1
                    i += 1
                    while i < len(obj_str) and brace_count > 0:
                        if obj_str[i] == '{':
                            brace_count += 1
                        elif obj_str[i] == '}':
                            brace_count -= 1
                        i += 1
                    value_str = obj_str[value_start:i].strip()
                    value = self._parse_js_object(value_str)
                elif obj_str[i] in ['"', "'"]:
                    # Handle quoted string value
                    quote_char = obj_str[i]
                    i += 1
                    value_start = i
                    while i < len(obj_str) and obj_str[i] != quote_char:
                        if obj_str[i] == '\\':  # Handle escaped characters
                            i += 1
                        i += 1
                    value_str = obj_str[value_start:i]
                    value = value_str
                    if i < len(obj_str):
                        i += 1  # Skip closing quote
                else:
                    # Unquoted value, go until comma or closing brace
                    while i < len(obj_str) and obj_str[i] not in ',}':
                        i += 1
                    value_str = obj_str[value_start:i].strip()
                    value = self._parse_js_value(value_str)

                if value is not None:
                    result[key] = value

                # Skip comma
                while i < len(obj_str) and (obj_str[i].isspace() or obj_str[i] == ','):
                    i += 1

        except Exception as e:
            print(f"Error in improved JS object parsing: {e}")

        return result if result else None

    def _parse_js_value(self, value_str: str) -> Any:
        """Parse a JavaScript value string."""
        value_str = value_str.strip()

        # Handle strings (quoted)
        if (value_str.startswith('"') and value_str.endswith('"')) or \
           (value_str.startswith("'") and value_str.endswith("'")):
            return value_str[1:-1]

        # Handle numbers
        try:
            if '.' in value_str:
                return float(value_str)
            else:
                return int(value_str)
        except ValueError:
            pass

        # Handle booleans
        if value_str.lower() == 'true':
            return True
        elif value_str.lower() == 'false':
            return False

        # Handle objects (recursive)
        if value_str.startswith('{') and value_str.endswith('}'):
            return self._parse_js_object(value_str)

        # Handle arrays
        if value_str.startswith('[') and value_str.endswith(']'):
            return self._parse_js_array(value_str)

        # Default: return as string
        return value_str

    def _parse_js_array(self, array_str: str) -> List[Any]:
        """Parse JavaScript array string."""
        array_str = array_str[1:-1]  # Remove brackets
        items = []

        # Simple split by comma (could be improved for nested structures)
        for item in array_str.split(','):
            item = item.strip()
            if item:
                items.append(self._parse_js_value(item))

        return items

    def _parse_theme_object(self, theme_config: Dict[str, Any], prefix: str = "") -> List[DesignTokenInfo]:
        """Recursively parse theme configuration object."""
        tokens = []

        for key, value in theme_config.items():
            current_path = f"{prefix}.{key}" if prefix else key

            if isinstance(value, dict):
                # Check if this is a token (has primitive values) or category (has nested objects)
                if self._is_token_object(value):
                    # This is a token object with scale values
                    tokens.extend(self._parse_token_scale(key, value, current_path))
                else:
                    # This is a category, recurse
                    tokens.extend(self._parse_theme_object(value, current_path))

            elif isinstance(value, (str, int, float)):
                # This is a direct token value
                token = self._create_token_from_value(key, value, current_path)
                if token:
                    tokens.append(token)

            elif isinstance(value, list):
                # Handle array values (like font families)
                tokens.extend(self._parse_array_value(key, value, current_path))

        return tokens

    def _is_token_object(self, obj: Dict[str, Any]) -> bool:
        """Check if object represents a token scale (all values are primitives)."""
        return all(isinstance(v, (str, int, float)) for v in obj.values())

    def _parse_token_scale(self, category: str, scale: Dict[str, Any], base_path: str) -> List[DesignTokenInfo]:
        """Parse a token scale (e.g., color.blue.100, color.blue.200, etc.)."""
        tokens = []

        for scale_key, scale_value in scale.items():
            if isinstance(scale_value, (str, int, float)):
                token_path = f"{base_path}.{scale_key}"
                token = self._create_token_from_value(scale_key, scale_value, token_path)

                if token:
                    # Override the tailwind class generation for scales
                    token.tailwind_class = self._generate_scale_tailwind_class(base_path, scale_key)
                    tokens.append(token)

        return tokens

    def _parse_array_value(self, key: str, array: List[Any], path: str) -> List[DesignTokenInfo]:
        """Parse array values (typically for font families)."""
        tokens = []

        # For arrays, create a single token with the array as the value
        if array:
            # Join string arrays with commas (common for font families)
            if all(isinstance(item, str) for item in array):
                value = ", ".join(array)
            else:
                value = str(array)

            token = self._create_token_from_value(key, value, path)
            if token:
                tokens.append(token)

        return tokens

    def _create_token_from_value(self, name: str, value: Any, path: str) -> Optional[DesignTokenInfo]:
        """Create a DesignTokenInfo from a theme value."""
        try:
            # Generate description based on path
            description = self._generate_description_from_path(path, value)

            # Generate CSS variable name
            css_variable = f"--{path.replace('.', '-')}"

            # Generate Tailwind class
            tailwind_class = self._generate_tailwind_class_from_path(path)

            # Create the token
            token = self.create_token(
                name=name,
                value=value,
                path=path,
                description=description,
                css_variable=css_variable,
                tailwind_class=tailwind_class
            )

            # Override source type to indicate JS origin
            token.source_type = "js"

            return token

        except Exception as e:
            print(f"Error creating token from {name}: {e}")
            return None

    def _generate_description_from_path(self, path: str, value: Any) -> str:
        """Generate description based on the token path."""
        path_lower = path.lower()

        if 'color' in path_lower or 'colours' in path_lower:
            return f"Tailwind color token from theme configuration"
        elif 'font' in path_lower:
            if 'family' in path_lower:
                return f"Tailwind font family from theme configuration"
            elif 'size' in path_lower:
                return f"Tailwind font size from theme configuration"
            elif 'weight' in path_lower:
                return f"Tailwind font weight from theme configuration"
            else:
                return f"Tailwind typography token from theme configuration"
        elif 'spacing' in path_lower or 'space' in path_lower:
            return f"Tailwind spacing token from theme configuration"
        elif 'screen' in path_lower or 'breakpoint' in path_lower:
            return f"Tailwind breakpoint from theme configuration"
        elif 'border' in path_lower:
            if 'radius' in path_lower:
                return f"Tailwind border radius from theme configuration"
            else:
                return f"Tailwind border token from theme configuration"
        elif 'shadow' in path_lower:
            return f"Tailwind shadow token from theme configuration"

        return f"Tailwind design token from theme configuration"

    def _generate_tailwind_class_from_path(self, path: str) -> str:
        """Generate Tailwind utility class from theme path."""
        parts = path.split('.')

        if len(parts) < 2:
            return ""

        category = parts[0].lower()
        subcategory = parts[1].lower() if len(parts) > 1 else ""
        scale = parts[2] if len(parts) > 2 else ""

        # Map theme paths to Tailwind classes
        if category == 'colors' or category == 'color':
            if scale:
                return f"bg-{subcategory}-{scale}"
            else:
                return f"bg-{subcategory}"

        elif category == 'fontsize' or (category == 'font' and subcategory == 'size'):
            return f"text-{scale or subcategory}"

        elif category == 'fontweight' or (category == 'font' and subcategory == 'weight'):
            return f"font-{scale or subcategory}"

        elif category == 'fontfamily' or (category == 'font' and subcategory == 'family'):
            return f"font-{scale or subcategory}"

        elif category == 'spacing':
            return f"p-{subcategory}"  # Default to padding

        elif category == 'borderradius' or (category == 'border' and subcategory == 'radius'):
            return f"rounded-{scale or subcategory}"

        elif category == 'screens' or category == 'breakpoints':
            return f"{subcategory}:"  # Responsive prefix

        return ""

    def _generate_scale_tailwind_class(self, base_path: str, scale: str) -> str:
        """Generate Tailwind class for scale-based tokens."""
        parts = base_path.split('.')

        if len(parts) < 2:
            return ""

        category = parts[0].lower()
        color_name = parts[1].lower()

        if category in ['colors', 'color']:
            return f"bg-{color_name}-{scale}"

        return ""