"""
Base parser class for design token extraction.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Union
from pathlib import Path
import re

from ..models import DesignTokenInfo


class BaseTokenParser(ABC):
    """Base class for all token parsers."""

    def __init__(self, source_file: Optional[Path] = None):
        self.source_file = source_file
        self.source_type = self.__class__.__name__.replace('Parser', '').lower()

    @abstractmethod
    def parse(self, content: str) -> List[DesignTokenInfo]:
        """Parse content and return list of design tokens."""
        pass

    @abstractmethod
    def can_parse(self, file_path: Path) -> bool:
        """Check if this parser can handle the given file."""
        pass

    def create_token(
        self,
        name: str,
        value: Union[str, int, float],
        path: str,
        token_type: Optional[str] = None,
        description: str = "",
        category: Optional[str] = None,
        css_variable: Optional[str] = None,
        tailwind_class: Optional[str] = None,
        **kwargs
    ) -> DesignTokenInfo:
        """Create a DesignTokenInfo instance with common attributes."""

        # Auto-detect token type if not provided
        if not token_type:
            token_type = self._detect_token_type(name, value, path)

        # Auto-detect category if not provided
        if not category:
            category = self._detect_category(path, token_type)

        # Generate CSS variable if not provided
        if not css_variable:
            css_variable = self._generate_css_variable(path)

        # Generate Tailwind class if not provided and applicable
        if not tailwind_class and self._is_tailwind_token(path):
            tailwind_class = self._generate_tailwind_class(path, token_type)

        return DesignTokenInfo(
            name=name,
            value=value,
            type=token_type,
            category=category,
            path=path,
            description=description,
            css_variable=css_variable,
            source_type=self.source_type,
            source_file=str(self.source_file) if self.source_file else "",
            tailwind_class=tailwind_class or "",
            **kwargs
        )

    def _detect_token_type(self, name: str, value: Any, path: str) -> str:
        """Detect token type from name, value, and path."""
        name_lower = name.lower()
        path_lower = path.lower()

        if isinstance(value, str):
            # Color detection
            if self._is_color_value(value):
                return "color"
            # Font family detection
            elif any(word in name_lower for word in ["family", "font"]) and "," in value:
                return "fontFamily"
            # Dimension detection
            elif self._is_dimension_value(value):
                return "dimension"

        # Number-based type detection
        elif isinstance(value, (int, float)):
            if any(word in name_lower for word in ["weight", "font-weight"]):
                return "fontWeight"
            elif any(word in name_lower for word in ["opacity", "alpha"]):
                return "opacity"
            else:
                return "number"

        # Path-based detection
        if any(word in path_lower for word in ["color", "colour"]):
            return "color"
        elif any(word in path_lower for word in ["spacing", "space", "gap", "margin", "padding"]):
            return "dimension"
        elif any(word in path_lower for word in ["font", "text", "typography"]):
            if "size" in path_lower:
                return "fontSize"
            elif "weight" in path_lower:
                return "fontWeight"
            elif "height" in path_lower or "leading" in path_lower:
                return "lineHeight"
            elif "family" in path_lower:
                return "fontFamily"
        elif any(word in path_lower for word in ["border", "radius"]):
            return "dimension"
        elif any(word in path_lower for word in ["shadow", "elevation"]):
            return "shadow"

        return "string"

    def _detect_category(self, path: str, token_type: str) -> str:
        """Detect token category from path and type with Tailwind-specific patterns."""
        path_lower = path.lower()

        # Semantic color categories (more useful for developers)
        if token_type == "color" or "color" in path_lower:
            if any(word in path_lower for word in ["brand", "primary", "secondary", "accent"]):
                return "brand-colors"
            elif any(word in path_lower for word in ["success", "error", "warning", "info", "danger"]):
                return "semantic-colors"
            elif any(word in path_lower for word in ["gray", "grey", "neutral", "slate", "zinc", "stone"]):
                return "neutral-colors"
            else:
                return "colors"

        # Typography with better granularity
        elif token_type in ["fontFamily", "fontWeight", "fontSize", "lineHeight"] or any(
            word in path_lower for word in ["font", "text", "typography"]
        ):
            return "typography"
        elif token_type == "dimension" or any(
            word in path_lower for word in ["spacing", "space", "gap", "margin", "padding"]
        ):
            return "spacing"
        elif any(word in path_lower for word in ["border", "radius"]):
            return "borders"
        elif any(word in path_lower for word in ["shadow", "elevation"]):
            return "shadows"
        elif any(word in path_lower for word in ["transition", "duration", "timing"]):
            return "transitions"

        return "miscellaneous"

    def _generate_css_variable(self, path: str) -> str:
        """Generate CSS custom property name from token path."""
        # Replace dots with hyphens and ensure it starts with --
        css_var = path.replace(".", "-").lower()
        if not css_var.startswith("--"):
            css_var = f"--{css_var}"
        return css_var

    def _is_tailwind_token(self, path: str) -> bool:
        """Check if this appears to be a Tailwind token based on path structure."""
        # Tailwind tokens typically follow patterns like color.primary.500
        return bool(re.match(r'^(color|font|spacing|size|border|shadow)', path.lower()))

    def _generate_tailwind_class(self, path: str, token_type: str) -> str:
        """Generate Tailwind utility class name from token path and type."""
        parts = path.split(".")
        path_lower = path.lower()

        if len(parts) < 2:
            return ""

        # Generate meaningful utility classes for colors
        if token_type == "color":
            # Handle semantic colors like color.brand.primary -> bg-brand-primary
            if len(parts) >= 3:
                # For nested colors like color.brand.primary or color.success.light
                if parts[1] in ['brand', 'primary', 'secondary', 'accent']:
                    return f"bg-{parts[1]}"
                elif parts[1] in ['success', 'error', 'warning', 'info']:
                    if len(parts) >= 3 and parts[2] in ['light', 'dark']:
                        return f"bg-{parts[1]}-{parts[2]}"
                    else:
                        return f"bg-{parts[1]}"
                else:
                    return f"bg-{parts[1]}-{parts[2]}"
            else:
                # Simple color like color.primary -> bg-primary
                return f"bg-{parts[1]}"

        # Typography tokens
        elif token_type in ["fontSize", "fontWeight", "fontFamily"]:
            if "size" in path_lower or token_type == "fontSize":
                # font.size.lg -> text-lg, fontSize.xl -> text-xl
                return f"text-{parts[-1]}"
            elif "weight" in path_lower or token_type == "fontWeight":
                # font.weight.bold -> font-bold, fontWeight.semibold -> font-semibold
                return f"font-{parts[-1]}"
            elif "family" in path_lower or token_type == "fontFamily":
                # font.family.heading -> font-heading
                return f"font-{parts[-1]}"

        # Spacing tokens
        elif token_type == "dimension" or "spacing" in path_lower:
            # spacing.lg -> p-lg, space.xl -> p-xl
            return f"p-{parts[-1]}"

        # Border radius
        elif "radius" in path_lower or "border" in path_lower:
            return f"rounded-{parts[-1]}"

        # Shadows
        elif "shadow" in path_lower:
            return f"shadow-{parts[-1]}"

        return ""

    def _is_color_value(self, value: str) -> bool:
        """Check if value appears to be a color."""
        value = value.strip()
        return (
            value.startswith("#") or
            value.startswith("rgb") or
            value.startswith("hsl") or
            value.startswith("var(") or
            value in ["transparent", "currentColor", "inherit", "initial"]
        )

    def _is_dimension_value(self, value: str) -> bool:
        """Check if value appears to be a dimension."""
        value = value.strip()
        return bool(re.match(r'^[\d.]+\s*(px|rem|em|%|vh|vw|pt|pc|in|cm|mm|ex|ch|vmin|vmax)$', value))

    def normalize_name(self, name: str) -> str:
        """Normalize token name for consistent naming."""
        return re.sub(r'[^a-zA-Z0-9_-]', '-', name).strip('-').lower()

    def parse_file(self, file_path: Path) -> List[DesignTokenInfo]:
        """Parse a file and return design tokens."""
        if not self.can_parse(file_path):
            return []

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            self.source_file = file_path
            return self.parse(content)

        except (IOError, UnicodeDecodeError) as e:
            print(f"Error reading file {file_path}: {e}")
            return []