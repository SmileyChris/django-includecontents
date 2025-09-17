import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from django.template import engines
from django.template.loaders.filesystem import Loader
from django.utils.text import smart_split

from .models import ComponentExample, ComponentInfo, PropDefinition, DesignTokenInfo, TokenCategory

import yaml

try:  # pragma: no cover - handled for Python <3.11
    import tomllib
except ModuleNotFoundError:  # pragma: no cover
    try:
        import tomli as tomllib  # type: ignore
    except ModuleNotFoundError:
        tomllib = None


class ComponentRegistry:
    """Registry for discovering and managing components and design tokens."""

    def __init__(self):
        self._components: Dict[str, ComponentInfo] = {}
        self._categories: Dict[str, List[str]] = {}
        self._tokens: Dict[str, DesignTokenInfo] = {}
        self._token_categories: Dict[str, TokenCategory] = {}
        self._discovered = False

    def discover(self, force: bool = False) -> None:
        """Discover all components and design tokens in the project."""
        if self._discovered and not force:
            return

        self._components.clear()
        self._categories.clear()
        self._tokens.clear()
        self._token_categories.clear()

        # Get template engine
        all_engines = engines.all()
        if not all_engines:
            return
        engine = all_engines[0]

        # Discover components from template directories
        loader_queue = []
        for loader in engine.engine.template_loaders:
            if hasattr(loader, "loaders"):
                loader_queue.extend(loader.loaders)
            else:
                loader_queue.append(loader)

        for loader in loader_queue:
            if hasattr(loader, "get_dirs"):
                for template_dir in loader.get_dirs():
                    components_dir = Path(template_dir) / "components"
                    if components_dir.exists():
                        self._scan_directory(components_dir, components_dir)

        # Organize components by category
        for component in self._components.values():
            if component.category not in self._categories:
                self._categories[component.category] = []
            self._categories[component.category].append(component.name)

        # Discover design tokens
        self._discover_tokens()

        self._discovered = True

    def _scan_directory(self, root: Path, current: Path, prefix: str = "") -> None:
        """Recursively scan directory for component templates."""
        for item in current.iterdir():
            if item.is_dir():
                # Skip hidden directories
                if item.name.startswith("."):
                    continue
                new_prefix = f"{prefix}{item.name}/" if prefix else f"{item.name}/"
                self._scan_directory(root, item, new_prefix)
            elif item.is_file() and item.suffix == ".html":
                # Skip private components (starting with _)
                if item.name.startswith("_"):
                    continue

                relative_path = item.relative_to(root)
                component_path = str(relative_path)
                component_name = component_path.replace("/", ":").replace(".html", "")

                # Parse component template
                component_info = self._parse_component(item, component_path, component_name)
                if component_info:
                    self._components[component_name] = component_info

    def _parse_component(self, file_path: Path, component_path: str, component_name: str) -> Optional[ComponentInfo]:
        """Parse a component template file to extract props."""
        try:
            with open(file_path, "r") as f:
                content = f.read()

            # Extract props comment
            props_match = re.search(r"{#\s*props\s+(.*?)\s*#}", content, re.DOTALL)
            if not props_match:
                # Component without props
                component = ComponentInfo(
                    name=component_name,
                    path=component_path,
                    category=self._guess_category(component_path),
                )
                metadata = self._load_component_metadata(file_path)
                if metadata:
                    self._apply_metadata(component, metadata)
                return component

            props_string = props_match.group(1).strip()
            props = self._parse_props_string(props_string)

            # Extract content blocks
            content_blocks = re.findall(r"{%\s*contents\s+([\w:-]+)\s*%}", content)

            component = ComponentInfo(
                name=component_name,
                path=component_path,
                category=self._guess_category(component_path),
                props=props,
                content_blocks=content_blocks
            )

            metadata = self._load_component_metadata(file_path)
            if metadata:
                self._apply_metadata(component, metadata)

            return component
        except Exception as e:
            print(f"Error parsing component {file_path}: {e}")
            return None

    def _parse_props_string(self, props_string: str) -> Dict[str, PropDefinition]:
        """Parse the props string from a component comment."""
        props = {}

        for bit in smart_split(props_string):
            match = re.match(r"^(\w+)(?:=(.+?))?,?$", bit)
            if match:
                prop_name, default_value = match.groups()

                prop_def = PropDefinition(name=prop_name)

                if default_value is None:
                    # Required prop
                    prop_def.required = True
                else:
                    # Optional prop with default
                    if "," in default_value and " " not in default_value:
                        # Enum values
                        if (default_value.startswith('"') and default_value.endswith('"')) or \
                           (default_value.startswith("'") and default_value.endswith("'")):
                            default_value = default_value[1:-1]

                        enum_values = default_value.split(",")
                        prop_def.allowed_values = enum_values
                        prop_def.type = "enum"

                        # First non-empty value is the default
                        non_empty = [v for v in enum_values if v]
                        if non_empty:
                            prop_def.default = non_empty[0]
                        prop_def.required = bool(enum_values[0])
                        if prop_def.default is not None or not enum_values[0]:
                            prop_def.required = False
                    else:
                        # Regular default value
                        lowered = default_value.lower()
                        if lowered in {"true", "false"}:
                            prop_def.type = "boolean"
                            prop_def.default = lowered == "true"
                        else:
                            # Try to coerce into an integer first, then float
                            number_value = None
                            try:
                                number_value = int(default_value)
                            except (TypeError, ValueError):
                                try:
                                    number_value = float(default_value)
                                except (TypeError, ValueError):
                                    number_value = None

                            if number_value is not None:
                                prop_def.type = "number"
                                prop_def.default = number_value
                            else:
                                # Remove quotes if present
                                if (default_value.startswith('"') and default_value.endswith('"')) or \
                                   (default_value.startswith("'") and default_value.endswith("'")):
                                    default_value = default_value[1:-1]
                                prop_def.default = default_value

                props[prop_name] = prop_def

        return props

    def _guess_category(self, component_path: str) -> str:
        """Guess component category from its path."""
        parts = component_path.split("/")
        if len(parts) > 1:
            # Use subdirectory as category
            category = parts[0]
            return category.replace("-", " ").replace("_", " ").title()

        # Try to guess from component name
        name = parts[0].replace(".html", "").lower()
        if any(word in name for word in ["button", "input", "form", "field", "select", "checkbox"]):
            return "Forms"
        elif any(word in name for word in ["card", "container", "grid", "layout", "column", "row"]):
            return "Layout"
        elif any(word in name for word in ["nav", "menu", "tab", "breadcrumb", "pagination"]):
            return "Navigation"
        elif any(word in name for word in ["alert", "modal", "toast", "notification", "progress"]):
            return "Feedback"
        elif any(word in name for word in ["table", "list", "badge", "avatar", "chip"]):
            return "Display"
        elif any(word in name for word in ["heading", "text", "quote", "paragraph"]):
            return "Typography"
        elif any(word in name for word in ["image", "video", "gallery", "media"]):
            return "Media"
        elif "icon" in name:
            return "Icons"
        else:
            return "Uncategorized"

    def _load_component_metadata(self, template_path: Path) -> Optional[Dict[str, Any]]:
        """Load metadata stored alongside a component template."""
        for suffix, loader in (
            (".yaml", self._load_yaml_metadata),
            (".yml", self._load_yaml_metadata),
            (".toml", self._load_toml_metadata),
        ):
            metadata_path = template_path.with_suffix(suffix)
            if metadata_path.exists():
                return loader(metadata_path)
        return None

    def _load_yaml_metadata(self, path: Path) -> Optional[Dict[str, Any]]:
        try:
            with open(path, "r", encoding="utf-8") as f:
                return yaml.safe_load(f) or {}
        except Exception as e:
            print(f"Error loading metadata {path}: {e}")
            return None

    def _load_toml_metadata(self, path: Path) -> Optional[Dict[str, Any]]:
        if tomllib is None:
            print(
                f"Skipping TOML metadata {path}: tomllib/tomli not available"
            )
            return None
        try:
            with open(path, "rb") as f:
                return tomllib.load(f)
        except Exception as e:
            print(f"Error loading metadata {path}: {e}")
            return None

    def _apply_metadata(self, component: ComponentInfo, data: Dict[str, Any]) -> None:
        if not data:
            return

        if "description" in data:
            component.description = data["description"]
        if "category" in data:
            component.category = data["category"]
        if "best_practices" in data:
            component.best_practices = data["best_practices"]
        if "accessibility" in data:
            component.accessibility = data["accessibility"]
        if "related" in data:
            component.related = data["related"]

        props_data = data.get("props", {})
        for prop_name, prop_data in props_data.items():
            if prop_name in component.props:
                prop = component.props[prop_name]
                if "description" in prop_data:
                    prop.description = prop_data["description"]
                if "type" in prop_data:
                    prop.type = prop_data["type"]
                if "default" in prop_data:
                    prop.default = prop_data["default"]
                if "values" in prop_data:
                    prop.allowed_values = prop_data["values"]

        examples = data.get("examples", [])
        for example_data in examples:
            example = ComponentExample(
                name=example_data.get("name", ""),
                code=example_data.get("code", ""),
                description=example_data.get("description", ""),
                props=example_data.get("props", {}),
            )
            component.examples.append(example)

    def get_component(self, name: str) -> Optional[ComponentInfo]:
        """Get a specific component by name."""
        self.discover()
        return self._components.get(name)

    def get_all_components(self) -> List[ComponentInfo]:
        """Get all discovered components."""
        self.discover()
        return list(self._components.values())

    def get_components_by_category(self, category: str) -> List[ComponentInfo]:
        """Get all components in a specific category."""
        self.discover()
        component_names = self._categories.get(category, [])
        return [self._components[name] for name in component_names]

    def get_categories(self) -> List[Tuple[str, int]]:
        """Get all categories with component counts."""
        self.discover()
        return [(cat, len(names)) for cat, names in sorted(self._categories.items())]

    def search_components(self, query: str) -> List[ComponentInfo]:
        """Search components by name or description."""
        self.discover()
        query = query.lower()
        results = []

        for component in self._components.values():
            if query in component.name.lower() or query in component.description.lower():
                results.append(component)
            elif any(query in prop.name.lower() for prop in component.props.values()):
                results.append(component)

        return results

    def _discover_tokens(self) -> None:
        """Discover design tokens from JSON files."""
        # Look for JSON token files directly in the showcase directory
        from django.conf import settings
        import os

        # Try to find the showcase directory in the project
        try:
            from django.conf import settings
            project_root = Path(settings.BASE_DIR)
            showcase_dir = project_root / "showcase"
            if showcase_dir.exists():
                self._scan_tokens_directory(showcase_dir)
        except (AttributeError, FileNotFoundError):
            pass

    def _scan_tokens_directory(self, tokens_dir: Path) -> None:
        """Scan directory for JSON token files."""
        for json_file in tokens_dir.glob("*.json"):
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    tokens_data = json.load(f)
                self._parse_tokens(tokens_data, json_file.stem)
            except (json.JSONDecodeError, IOError) as e:
                print(f"Error loading tokens from {json_file}: {e}")

    def _parse_tokens(self, data: Dict[str, Any], file_category: str, path_prefix: str = "") -> None:
        """Parse tokens from JSON data recursively."""
        for key, value in data.items():
            current_path = f"{path_prefix}.{key}" if path_prefix else key

            if isinstance(value, dict):
                if "value" in value:
                    # This is a token
                    token_type = value.get("type", self._guess_token_type(key, value["value"]))
                    category = value.get("category", self._guess_token_category(current_path, token_type))

                    token = DesignTokenInfo(
                        name=key,
                        value=value["value"],
                        type=token_type,
                        category=category,
                        path=current_path,
                        description=value.get("description", ""),
                        css_variable=value.get("css_variable", "")
                    )

                    self._tokens[current_path] = token

                    # Add to category
                    if category not in self._token_categories:
                        self._token_categories[category] = TokenCategory(
                            name=category.title(),
                            slug=category.lower(),
                            description=f"{category.title()} design tokens"
                        )
                    self._token_categories[category].tokens.append(token)
                else:
                    # Recursive call for nested objects
                    self._parse_tokens(value, file_category, current_path)

    def _guess_token_type(self, name: str, value: Any) -> str:
        """Guess the token type based on name and value."""
        name_lower = name.lower()

        if isinstance(value, str):
            if value.startswith("#") or value.startswith("rgb") or value.startswith("hsl"):
                return "color"
            elif any(unit in value for unit in ["px", "rem", "em", "%", "vh", "vw"]):
                return "dimension"
            elif any(word in name_lower for word in ["font", "family"]):
                return "fontFamily"
            elif "weight" in name_lower:
                return "fontWeight"
        elif isinstance(value, (int, float)):
            if any(word in name_lower for word in ["size", "spacing", "gap", "margin", "padding"]):
                return "dimension"
            elif "weight" in name_lower:
                return "fontWeight"

        return "string"

    def _guess_token_category(self, path: str, token_type: str) -> str:
        """Guess the token category based on path and type."""
        path_lower = path.lower()

        if "color" in path_lower or token_type == "color":
            return "colors"
        elif any(word in path_lower for word in ["font", "text", "typography"]) or token_type in ["fontFamily", "fontWeight", "fontSize"]:
            return "typography"
        elif any(word in path_lower for word in ["spacing", "space", "gap", "margin", "padding"]) or token_type == "dimension":
            return "spacing"
        elif any(word in path_lower for word in ["border", "radius"]):
            return "borders"
        elif any(word in path_lower for word in ["shadow", "elevation"]):
            return "shadows"

        return "miscellaneous"

    # Design token methods
    def get_token(self, path: str) -> Optional[DesignTokenInfo]:
        """Get a specific token by path."""
        self.discover()
        return self._tokens.get(path)

    def get_all_tokens(self) -> List[DesignTokenInfo]:
        """Get all discovered tokens."""
        self.discover()
        return list(self._tokens.values())

    def get_token_categories(self) -> List[TokenCategory]:
        """Get all token categories."""
        self.discover()
        return list(self._token_categories.values())

    def get_tokens_by_category(self, category: str) -> List[DesignTokenInfo]:
        """Get all tokens in a specific category."""
        self.discover()
        category_obj = self._token_categories.get(category.lower())
        return category_obj.tokens if category_obj else []

    def search_tokens(self, query: str) -> List[DesignTokenInfo]:
        """Search tokens by name, path, or description."""
        self.discover()
        query = query.lower()
        results = []

        for token in self._tokens.values():
            if (query in token.name.lower() or
                query in token.path.lower() or
                query in token.description.lower()):
                results.append(token)

        return results


# Global registry instance
registry = ComponentRegistry()
