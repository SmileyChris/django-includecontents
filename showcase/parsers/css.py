"""
CSS parser for Tailwind 4.0 @theme directives and custom CSS properties.
"""

import re
from typing import List, Dict, Any, Optional
from pathlib import Path

from .base import BaseTokenParser
from ..models import DesignTokenInfo


class CSSThemeParser(BaseTokenParser):
    """Parser for Tailwind CSS 4.0 @theme directives and CSS custom properties."""

    # Regex patterns for parsing
    THEME_BLOCK_PATTERN = re.compile(
        r'@theme\s*\{([^}]*)\}',
        re.DOTALL | re.IGNORECASE
    )

    # CSS custom property pattern with flexible syntax
    CSS_VAR_PATTERN = re.compile(
        r'--([a-zA-Z0-9_-]+(?:-[a-zA-Z0-9_-]+)*)\s*:\s*([^;]+);',
        re.MULTILINE
    )

    # Root block pattern for standalone CSS variables
    ROOT_BLOCK_PATTERN = re.compile(
        r':root\s*\{([^}]*)\}',
        re.DOTALL | re.IGNORECASE
    )

    def can_parse(self, file_path: Path) -> bool:
        """Check if this parser can handle the given file."""
        return file_path.suffix.lower() in ['.css', '.scss', '.sass', '.less']

    def parse(self, content: str) -> List[DesignTokenInfo]:
        """Parse CSS content for @theme directives and custom properties."""
        tokens = []

        # Parse @theme blocks (Tailwind 4.0)
        tokens.extend(self._parse_theme_blocks(content))

        # Parse :root blocks with CSS custom properties
        tokens.extend(self._parse_root_blocks(content))

        # Parse standalone CSS custom properties (not in blocks)
        tokens.extend(self._parse_standalone_variables(content))

        return tokens

    def _parse_theme_blocks(self, content: str) -> List[DesignTokenInfo]:
        """Parse @theme blocks for Tailwind 4.0 theme variables."""
        tokens = []

        for match in self.THEME_BLOCK_PATTERN.finditer(content):
            block_content = match.group(1)
            block_tokens = self._parse_css_variables(block_content, is_theme_block=True)
            tokens.extend(block_tokens)

        return tokens

    def _parse_root_blocks(self, content: str) -> List[DesignTokenInfo]:
        """Parse :root blocks for CSS custom properties."""
        tokens = []

        for match in self.ROOT_BLOCK_PATTERN.finditer(content):
            block_content = match.group(1)
            block_tokens = self._parse_css_variables(block_content, is_theme_block=False)
            tokens.extend(block_tokens)

        return tokens

    def _parse_standalone_variables(self, content: str) -> List[DesignTokenInfo]:
        """Parse standalone CSS custom properties outside of blocks."""
        # Remove @theme and :root blocks to avoid duplicates
        cleaned_content = self.THEME_BLOCK_PATTERN.sub('', content)
        cleaned_content = self.ROOT_BLOCK_PATTERN.sub('', cleaned_content)

        return self._parse_css_variables(cleaned_content, is_theme_block=False)

    def _parse_css_variables(self, content: str, is_theme_block: bool = False) -> List[DesignTokenInfo]:
        """Parse CSS custom properties from content."""
        tokens = []

        for match in self.CSS_VAR_PATTERN.finditer(content):
            var_name = match.group(1)
            var_value = match.group(2).strip()

            # Clean up the value (remove comments, normalize whitespace)
            var_value = self._clean_css_value(var_value)

            if not var_value:
                continue

            # Generate token information
            token = self._create_token_from_css_var(var_name, var_value, is_theme_block)
            if token:
                tokens.append(token)

        return tokens

    def _create_token_from_css_var(self, var_name: str, var_value: str, is_theme_block: bool) -> Optional[DesignTokenInfo]:
        """Create a DesignTokenInfo from a CSS custom property."""
        try:
            # Parse the variable name to extract semantic information
            path_parts = self._parse_variable_name(var_name)
            if not path_parts:
                return None

            # Create the path (dot-notation)
            path = ".".join(path_parts)

            # Get the display name (last part of the path)
            name = path_parts[-1]

            # Generate description
            description = self._generate_description(var_name, var_value, is_theme_block)

            # Generate CSS variable name
            css_variable = f"--{var_name}"

            # Generate Tailwind class if applicable
            tailwind_class = ""
            if is_theme_block:
                tailwind_class = self._generate_tailwind_class_from_name(var_name, path_parts)

            # Create the token
            token = self.create_token(
                name=name,
                value=var_value,
                path=path,
                description=description,
                css_variable=css_variable,
                tailwind_class=tailwind_class
            )

            # Override source type to indicate CSS origin
            token.source_type = "css"

            return token

        except Exception as e:
            print(f"Error creating token from CSS variable {var_name}: {e}")
            return None

    def _parse_variable_name(self, var_name: str) -> List[str]:
        """Parse CSS variable name into semantic path parts."""
        # Remove any leading dashes
        clean_name = var_name.lstrip('-')

        # Split on hyphens and underscores
        parts = re.split(r'[-_]', clean_name)

        # Filter out empty parts
        parts = [part for part in parts if part]

        if not parts:
            return []

        # Try to identify the main category from common patterns
        normalized_parts = []

        # Handle common Tailwind patterns
        if parts[0] in ['color', 'colours']:
            normalized_parts = ['color'] + parts[1:]
        elif parts[0] in ['font']:
            if len(parts) > 1:
                if parts[1] in ['family', 'families']:
                    normalized_parts = ['font', 'family'] + parts[2:]
                elif parts[1] in ['size', 'sizes']:
                    normalized_parts = ['font', 'size'] + parts[2:]
                elif parts[1] in ['weight', 'weights']:
                    normalized_parts = ['font', 'weight'] + parts[2:]
                else:
                    normalized_parts = ['font'] + parts[1:]
            else:
                normalized_parts = parts
        elif parts[0] in ['spacing', 'space']:
            normalized_parts = ['spacing'] + parts[1:]
        elif parts[0] in ['border']:
            if len(parts) > 1 and parts[1] in ['radius']:
                normalized_parts = ['border', 'radius'] + parts[2:]
            else:
                normalized_parts = parts
        elif parts[0] in ['shadow', 'shadows']:
            normalized_parts = ['shadow'] + parts[1:]
        else:
            # Default: use parts as-is
            normalized_parts = parts

        return normalized_parts

    def _generate_description(self, var_name: str, var_value: str, is_theme_block: bool) -> str:
        """Generate a human-readable description for the token."""
        source = "Tailwind @theme" if is_theme_block else "CSS custom property"

        # Try to infer meaning from the variable name
        name_lower = var_name.lower()

        if 'color' in name_lower or 'colour' in name_lower:
            return f"{source} color value"
        elif 'font' in name_lower and 'family' in name_lower:
            return f"{source} font family"
        elif 'font' in name_lower and 'size' in name_lower:
            return f"{source} font size"
        elif 'font' in name_lower and 'weight' in name_lower:
            return f"{source} font weight"
        elif 'spacing' in name_lower or 'space' in name_lower:
            return f"{source} spacing value"
        elif 'border' in name_lower and 'radius' in name_lower:
            return f"{source} border radius"
        elif 'shadow' in name_lower:
            return f"{source} shadow value"
        elif 'primary' in name_lower:
            return f"{source} primary design token"
        elif 'secondary' in name_lower:
            return f"{source} secondary design token"

        return f"{source} design token"

    def _generate_tailwind_class_from_name(self, var_name: str, path_parts: List[str]) -> str:
        """Generate Tailwind utility class name from CSS variable name."""
        if not path_parts:
            return ""

        # Map CSS variable patterns to Tailwind classes
        if len(path_parts) >= 2:
            category = path_parts[0].lower()

            if category == 'color':
                # color-primary-500 -> bg-primary-500
                if len(path_parts) >= 3:
                    return f"bg-{path_parts[1]}-{path_parts[2]}"
                else:
                    return f"bg-{path_parts[1]}"

            elif category == 'font':
                if len(path_parts) >= 3:
                    subcategory = path_parts[1].lower()
                    if subcategory == 'size':
                        return f"text-{path_parts[2]}"
                    elif subcategory == 'weight':
                        return f"font-{path_parts[2]}"
                    elif subcategory == 'family':
                        return f"font-{path_parts[2]}"

            elif category == 'spacing':
                if len(path_parts) >= 2:
                    return f"p-{path_parts[1]}"  # Default to padding

            elif category == 'border' and len(path_parts) >= 3 and path_parts[1] == 'radius':
                return f"rounded-{path_parts[2]}"

        return ""

    def _clean_css_value(self, value: str) -> str:
        """Clean and normalize CSS value."""
        # Remove CSS comments
        value = re.sub(r'/\*.*?\*/', '', value, flags=re.DOTALL)

        # Remove trailing comments (// style)
        value = re.sub(r'//.*$', '', value, flags=re.MULTILINE)

        # Normalize whitespace
        value = re.sub(r'\s+', ' ', value.strip())

        # Remove trailing commas or semicolons
        value = value.rstrip(',;')

        return value

    def extract_theme_variables(self, content: str) -> Dict[str, str]:
        """Extract just the @theme variables as a dictionary (for external use)."""
        variables = {}

        for match in self.THEME_BLOCK_PATTERN.finditer(content):
            block_content = match.group(1)

            for var_match in self.CSS_VAR_PATTERN.finditer(block_content):
                var_name = var_match.group(1)
                var_value = self._clean_css_value(var_match.group(2))
                variables[f"--{var_name}"] = var_value

        return variables