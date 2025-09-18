"""
Transformer for converting Tailwind design tokens to Style Dictionary format.
"""

from typing import Dict, List, Any, Optional, Union
from pathlib import Path
import re

from ..models import DesignTokenInfo


class TailwindTokenTransformer:
    """Transforms Tailwind tokens to Style Dictionary format and vice versa."""

    # Tailwind category mappings to Style Dictionary format
    CATEGORY_MAPPINGS = {
        'colors': 'color',
        'fontSizes': 'font.size',
        'fontWeights': 'font.weight',
        'fontFamilies': 'font.family',
        'lineHeights': 'font.lineHeight',
        'spacing': 'spacing',
        'borderRadius': 'border.radius',
        'borderWidths': 'border.width',
        'shadows': 'shadow',
        'screens': 'breakpoint',
        'opacity': 'opacity',
        'zIndex': 'zIndex',
    }

    # Style Dictionary type mappings
    TYPE_MAPPINGS = {
        'color': 'color',
        'dimension': 'dimension',
        'fontFamily': 'fontFamily',
        'fontWeight': 'fontWeight',
        'fontSize': 'fontSize',
        'lineHeight': 'lineHeight',
        'spacing': 'dimension',
        'borderRadius': 'dimension',
        'borderWidth': 'dimension',
        'shadow': 'shadow',
        'opacity': 'number',
        'zIndex': 'number',
    }

    def __init__(self):
        self.tokens = []

    def transform_to_style_dictionary(self, tailwind_tokens: List[DesignTokenInfo]) -> Dict[str, Any]:
        """Transform Tailwind tokens to Style Dictionary format."""
        style_dict = {}

        for token in tailwind_tokens:
            # Build the nested structure
            path_parts = token.path.split('.')
            current_level = style_dict

            # Navigate/create the nested structure
            for i, part in enumerate(path_parts[:-1]):
                if part not in current_level:
                    current_level[part] = {}
                current_level = current_level[part]

            # Add the token value
            token_name = path_parts[-1]
            current_level[token_name] = {
                'value': token.value,
                'type': token.type,
                'description': token.description,
            }

            # Add additional metadata if present
            if token.css_variable:
                current_level[token_name]['css_variable'] = token.css_variable

            if token.tailwind_class:
                current_level[token_name]['tailwind_class'] = token.tailwind_class

            if token.source_type:
                current_level[token_name]['source_type'] = token.source_type

            if token.source_file:
                current_level[token_name]['source_file'] = token.source_file

        return style_dict

    def transform_from_style_dictionary(self, style_dict: Dict[str, Any], source_file: str = "") -> List[DesignTokenInfo]:
        """Transform Style Dictionary format to Tailwind tokens."""
        tokens = []
        self._extract_tokens_recursive(style_dict, tokens, "", source_file)
        return tokens

    def _extract_tokens_recursive(
        self,
        obj: Dict[str, Any],
        tokens: List[DesignTokenInfo],
        path_prefix: str = "",
        source_file: str = ""
    ):
        """Recursively extract tokens from Style Dictionary structure."""
        for key, value in obj.items():
            current_path = f"{path_prefix}.{key}" if path_prefix else key

            if isinstance(value, dict):
                if 'value' in value:
                    # This is a token
                    token = DesignTokenInfo(
                        name=key,
                        value=value['value'],
                        type=value.get('type', 'string'),
                        category=self._infer_category_from_path(current_path),
                        path=current_path,
                        description=value.get('description', ''),
                        css_variable=value.get('css_variable', f"--{current_path.replace('.', '-')}"),
                        source_type=value.get('source_type', 'json'),
                        source_file=value.get('source_file', source_file),
                        tailwind_class=value.get('tailwind_class', '')
                    )
                    tokens.append(token)
                else:
                    # This is a nested object, recurse
                    self._extract_tokens_recursive(value, tokens, current_path, source_file)

    def _infer_category_from_path(self, path: str) -> str:
        """Infer token category from its path."""
        path_lower = path.lower()

        if any(word in path_lower for word in ['color', 'colours']):
            return 'colors'
        elif any(word in path_lower for word in ['font', 'text', 'typography']):
            return 'typography'
        elif any(word in path_lower for word in ['spacing', 'space', 'margin', 'padding']):
            return 'spacing'
        elif any(word in path_lower for word in ['border', 'radius']):
            return 'borders'
        elif any(word in path_lower for word in ['shadow', 'elevation']):
            return 'shadows'
        elif any(word in path_lower for word in ['screen', 'breakpoint']):
            return 'breakpoints'

        return 'miscellaneous'

    def normalize_tailwind_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize Tailwind config to consistent format."""
        normalized = {}

        for category, values in config.items():
            # Map Tailwind categories to standard names
            standard_category = self._normalize_category_name(category)

            if isinstance(values, dict):
                normalized[standard_category] = self._normalize_values(values, category)
            else:
                normalized[standard_category] = values

        return normalized

    def _normalize_category_name(self, category: str) -> str:
        """Normalize Tailwind category names."""
        category_lower = category.lower()

        # Map common Tailwind category variations
        if category_lower in ['colors', 'color']:
            return 'colors'
        elif category_lower in ['fontsize', 'fontsizes', 'font-size']:
            return 'fontSizes'
        elif category_lower in ['fontweight', 'fontweights', 'font-weight']:
            return 'fontWeights'
        elif category_lower in ['fontfamily', 'fontfamilies', 'font-family']:
            return 'fontFamilies'
        elif category_lower in ['lineheight', 'lineheights', 'line-height']:
            return 'lineHeights'
        elif category_lower in ['spacing', 'space']:
            return 'spacing'
        elif category_lower in ['borderradius', 'border-radius']:
            return 'borderRadius'
        elif category_lower in ['borderwidth', 'border-width']:
            return 'borderWidths'
        elif category_lower in ['boxshadow', 'shadow', 'shadows']:
            return 'shadows'
        elif category_lower in ['screens', 'breakpoints']:
            return 'screens'

        return category

    def _normalize_values(self, values: Dict[str, Any], category: str) -> Dict[str, Any]:
        """Normalize token values within a category."""
        normalized = {}

        for key, value in values.items():
            if isinstance(value, dict):
                # Nested object (like color scales)
                normalized[key] = self._normalize_values(value, category)
            else:
                # Direct value
                normalized[key] = self._normalize_single_value(value, category)

        return normalized

    def _normalize_single_value(self, value: Any, category: str) -> Any:
        """Normalize a single token value."""
        if isinstance(value, str):
            value = value.strip()

            # Normalize color values
            if category.lower() in ['colors', 'color']:
                return self._normalize_color_value(value)

            # Normalize dimension values
            elif category.lower() in ['spacing', 'fontsize', 'borderradius']:
                return self._normalize_dimension_value(value)

        return value

    def _normalize_color_value(self, color: str) -> str:
        """Normalize color values to consistent format."""
        color = color.strip()

        # Convert named colors to hex if needed
        # (This could be expanded with a color name mapping)

        # Ensure hex colors are lowercase
        if color.startswith('#'):
            return color.lower()

        return color

    def _normalize_dimension_value(self, dimension: str) -> str:
        """Normalize dimension values to consistent format."""
        dimension = dimension.strip()

        # Convert px values to rem if desired
        # (This is optional and could be configurable)

        return dimension

    def generate_css_variables(self, tokens: List[DesignTokenInfo]) -> str:
        """Generate CSS custom properties from tokens."""
        css_lines = [':root {']

        for token in tokens:
            css_var = token.css_variable or f"--{token.path.replace('.', '-')}"
            css_lines.append(f"  {css_var}: {token.value};")

        css_lines.append('}')
        return '\n'.join(css_lines)

    def generate_tailwind_theme(self, tokens: List[DesignTokenInfo]) -> Dict[str, Any]:
        """Generate Tailwind theme configuration from tokens."""
        theme = {}

        for token in tokens:
            path_parts = token.path.split('.')

            # Build nested structure
            current_level = theme
            for part in path_parts[:-1]:
                if part not in current_level:
                    current_level[part] = {}
                current_level = current_level[part]

            # Add the value
            current_level[path_parts[-1]] = token.value

        return theme

    def merge_token_sources(self, *token_lists: List[DesignTokenInfo]) -> List[DesignTokenInfo]:
        """Merge multiple token sources, handling conflicts."""
        merged = {}
        all_tokens = []

        # Collect all tokens
        for token_list in token_lists:
            all_tokens.extend(token_list)

        # Sort by priority (css > js > json)
        source_priority = {'css': 3, 'js': 2, 'json': 1, 'manual': 0}
        all_tokens.sort(key=lambda t: source_priority.get(t.source_type, 0), reverse=True)

        # Merge, keeping highest priority for conflicts
        for token in all_tokens:
            if token.path not in merged:
                merged[token.path] = token

        return list(merged.values())

    def validate_tokens(self, tokens: List[DesignTokenInfo]) -> List[str]:
        """Validate tokens and return list of issues."""
        issues = []

        for token in tokens:
            # Check for required fields
            if not token.name:
                issues.append(f"Token at path '{token.path}' missing name")

            if not token.value:
                issues.append(f"Token '{token.name}' missing value")

            if not token.path:
                issues.append(f"Token '{token.name}' missing path")

            # Validate color values
            if token.type == 'color' and isinstance(token.value, str):
                if not self._is_valid_color(token.value):
                    issues.append(f"Token '{token.name}' has invalid color value: {token.value}")

            # Validate dimension values
            if token.type in ['dimension', 'fontSize', 'spacing'] and isinstance(token.value, str):
                if not self._is_valid_dimension(token.value):
                    issues.append(f"Token '{token.name}' has invalid dimension value: {token.value}")

        return issues

    def _is_valid_color(self, color: str) -> bool:
        """Check if color value is valid."""
        color = color.strip()
        return (
            color.startswith('#') and len(color) in [4, 7, 9] or
            color.startswith('rgb') or
            color.startswith('hsl') or
            color.startswith('var(') or
            color in ['transparent', 'currentColor', 'inherit', 'initial']
        )

    def _is_valid_dimension(self, dimension: str) -> bool:
        """Check if dimension value is valid."""
        dimension = dimension.strip()
        return bool(re.match(r'^[\d.]+\s*(px|rem|em|%|vh|vw|pt|pc|in|cm|mm|ex|ch|vmin|vmax)$', dimension))

    def export_to_json(self, tokens: List[DesignTokenInfo]) -> Dict[str, Any]:
        """Export tokens to JSON format for backup/sharing."""
        return {
            'version': '1.0',
            'tokens': [
                {
                    'name': token.name,
                    'value': token.value,
                    'type': token.type,
                    'category': token.category,
                    'path': token.path,
                    'description': token.description,
                    'css_variable': token.css_variable,
                    'source_type': token.source_type,
                    'source_file': token.source_file,
                    'tailwind_class': token.tailwind_class,
                }
                for token in tokens
            ]
        }