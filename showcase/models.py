from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Union


@dataclass
class PropDefinition:
    """Definition of a component prop."""

    name: str
    type: str = "string"  # string, enum, boolean, number
    default: Any = None
    required: bool = False
    description: str = ""
    allowed_values: List[str] = field(default_factory=list)

    @property
    def is_enum(self) -> bool:
        return bool(self.allowed_values)


@dataclass
class ComponentExample:
    """Example usage of a component."""

    name: str
    code: str
    description: str = ""
    props: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ComponentInfo:
    """Complete information about a component."""

    name: str
    path: str
    category: str = "Uncategorized"
    description: str = ""
    props: Dict[str, PropDefinition] = field(default_factory=dict)
    examples: List[ComponentExample] = field(default_factory=list)
    best_practices: str = ""
    accessibility: str = ""
    related: List[str] = field(default_factory=list)
    content_blocks: List[str] = field(default_factory=list)

    @property
    def slug(self) -> str:
        """Generate URL-friendly slug from component name."""
        base_name = self.name.rsplit(":", 1)[-1]
        return base_name.lower().replace("_", "-")

    @property
    def template_name(self) -> str:
        """Get the template name for this component."""
        return f"components/{self.path}"

    @property
    def tag_name(self) -> str:
        """Get the HTML-style tag name for this component."""
        return f"include:{self.path.replace('/', ':').replace('.html', '')}"

    def get_default_props(self) -> Dict[str, Any]:
        """Get default prop values for this component."""
        defaults = {}
        for prop_name, prop_def in self.props.items():
            if prop_def.default is not None:
                defaults[prop_name] = prop_def.default
            elif prop_def.is_enum and prop_def.allowed_values:
                # Use first non-empty enum value as default
                non_empty = [v for v in prop_def.allowed_values if v]
                if non_empty:
                    defaults[prop_name] = non_empty[0]
        return defaults


@dataclass
class DesignTokenInfo:
    """Information about a design token."""

    name: str
    value: Union[str, int, float]
    type: str  # color, dimension, fontFamily, fontWeight, duration, etc.
    category: str  # colors, typography, spacing, etc.
    path: str  # dot-notation path like "color.primary.500"
    description: str = ""
    css_variable: str = ""  # CSS custom property name

    @property
    def slug(self) -> str:
        """Generate URL-friendly slug from token name."""
        return self.name.lower().replace(".", "-").replace("_", "-")

    @property
    def css_var_name(self) -> str:
        """Generate CSS custom property name."""
        if self.css_variable:
            return self.css_variable
        return f"--{self.path.replace('.', '-')}"

    @property
    def is_color(self) -> bool:
        """Check if this is a color token."""
        return self.type == "color"

    @property
    def is_dimension(self) -> bool:
        """Check if this is a dimension/spacing token."""
        return self.type in ("dimension", "spacing", "size")

    @property
    def is_typography(self) -> bool:
        """Check if this is a typography token."""
        return self.type in ("fontFamily", "fontWeight", "fontSize", "lineHeight")


@dataclass
class TokenCategory:
    """Category grouping for design tokens."""

    name: str
    slug: str
    description: str = ""
    tokens: List[DesignTokenInfo] = field(default_factory=list)

    @property
    def count(self) -> int:
        """Number of tokens in this category."""
        return len(self.tokens)
