import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from django.template import engines
from django.template.loaders.filesystem import Loader
from django.utils.text import smart_split

from .models import ComponentExample, ComponentInfo, PropDefinition, DesignTokenInfo, TokenCategory
from .parsers import CSSThemeParser, TailwindConfigParser, TailwindTokenTransformer

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
        # Style Dictionary tokens (JSON)
        self._tokens: Dict[str, DesignTokenInfo] = {}
        self._token_categories: Dict[str, TokenCategory] = {}
        # Tailwind tokens (CSS @theme and tailwind.config.js)
        self._tailwind_tokens: Dict[str, DesignTokenInfo] = {}
        self._tailwind_token_categories: Dict[str, TokenCategory] = {}
        self._discovered = False

    def discover(self, force: bool = False) -> None:
        """Discover all components and design tokens in the project."""
        if self._discovered and not force:
            return

        self._components.clear()
        self._categories.clear()
        self._tokens.clear()
        self._token_categories.clear()
        self._tailwind_tokens.clear()
        self._tailwind_token_categories.clear()

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

        # Discover Tailwind tokens
        self._discover_tailwind_tokens()

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

                # Skip showcase templates (ending with .showcase.html)
                if item.name.endswith(".showcase.html"):
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

            # Check for showcase template
            showcase_template_path = None
            showcase_file_path = file_path.with_suffix('.showcase.html')
            if showcase_file_path.exists():
                # Store relative path from components directory
                showcase_template_path = str(Path(component_path).with_suffix('.showcase.html'))

            # Extract props comment
            props_match = re.search(r"{#\s*props\s+(.*?)\s*#}", content, re.DOTALL)
            if not props_match:
                # Component without props
                component = ComponentInfo(
                    name=component_name,
                    path=component_path,
                    category=self._guess_category(component_path),
                    showcase_template_path=showcase_template_path,
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
                content_blocks=content_blocks,
                showcase_template_path=showcase_template_path,
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
                # Store the source file for token creation
                self.source_file = json_file
                self._parse_tokens(tokens_data, json_file.stem)
            except (json.JSONDecodeError, IOError) as e:
                print(f"Error loading tokens from {json_file}: {e}")
            finally:
                # Clear source file after processing
                self.source_file = None

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
                        css_variable=value.get("css_variable", ""),
                        source_type="json",
                        source_file=str(self.source_file) if hasattr(self, 'source_file') and self.source_file else "",
                        tailwind_class=""
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

    def _discover_tailwind_tokens(self) -> None:
        """Discover design tokens from Tailwind configurations."""
        try:
            from django.conf import settings
            project_root = Path(settings.BASE_DIR)

            # Get Tailwind discovery settings
            tailwind_settings = getattr(settings, 'SHOWCASE_TAILWIND_DISCOVERY', {
                'enabled': True,
                'config_paths': [
                    'tailwind.config.js',
                    'tailwind.config.ts',
                    'tailwind.config.mjs',
                    'frontend/tailwind.config.js',
                    'assets/tailwind.config.js',
                ],
                'css_paths': [
                    'static/**/*.css',
                    'assets/**/*.css',
                    '**/*.css',
                ],
                'auto_scan': True,
                'lazy_discovery': True  # Enable lazy discovery by default
            })

            if not tailwind_settings.get('enabled', True):
                return

            # Check if we should do lazy discovery
            if tailwind_settings.get('lazy_discovery', True) and not self._has_tailwind_tokens():
                # Only do minimal discovery on first load if no Tailwind tokens exist
                self._discover_minimal_tailwind_tokens(project_root, tailwind_settings)
            elif not tailwind_settings.get('lazy_discovery', True):
                # Full discovery (for management commands or when lazy_discovery=False)
                self._discover_tailwind_config_files(project_root, tailwind_settings)
                self._discover_css_theme_files(project_root, tailwind_settings)
            # If lazy_discovery=True and Tailwind tokens already exist, skip discovery for performance

        except (AttributeError, ImportError, FileNotFoundError) as e:
            # Silently fail for lazy discovery to avoid spamming logs
            if not tailwind_settings.get('lazy_discovery', True):
                print(f"Warning: Could not discover Tailwind tokens: {e}")

    def _discover_minimal_tailwind_tokens(self, project_root: Path, settings: Dict[str, Any]) -> None:
        """Lightweight discovery for common Tailwind configs only."""
        # Only check the most common locations to avoid performance impact
        common_paths = [
            'tailwind.config.js',
            'tailwind.config.ts',
        ]

        found_any = False

        # Quick check for common config files
        for config_path in common_paths:
            config_file = project_root / config_path
            if config_file.exists():
                try:
                    parser = TailwindConfigParser()
                    tokens = parser.parse_file(config_file)
                    if tokens:
                        self._add_tailwind_tokens(tokens)
                        found_any = True
                        # Only process first found config for performance
                        break
                except Exception:
                    continue  # Silently continue for lazy discovery

        # Quick check for @theme in main CSS files if no config found
        if not found_any:
            css_patterns = ['static/**/*.css', 'assets/css/*.css']
            for pattern in css_patterns:
                css_files = list(project_root.glob(pattern))[:3]  # Limit to first 3 files
                for css_file in css_files:
                    try:
                        # Quick check for @theme without full parsing
                        with open(css_file, 'r', encoding='utf-8') as f:
                            content = f.read(2000)  # Only read first 2KB
                            if '@theme' in content:
                                parser = CSSThemeParser()
                                tokens = parser.parse_file(css_file)
                                if tokens:
                                    self._add_tailwind_tokens(tokens)
                                    break
                    except (IOError, UnicodeDecodeError):
                        continue

    def _has_any_tokens(self) -> bool:
        """Check if any design tokens exist in the registry."""
        return len(self._tokens) > 0

    def _discover_tailwind_config_files(self, project_root: Path, settings: Dict[str, Any]) -> None:
        """Discover and parse Tailwind config files."""
        parser = TailwindConfigParser()
        config_paths = settings.get('config_paths', [])

        # Search specified paths
        for config_path in config_paths:
            full_path = project_root / config_path
            if full_path.exists() and full_path.is_file():
                self._parse_tailwind_config_file(full_path, parser)

        # Auto-scan if enabled and no configs found
        if settings.get('auto_scan', True) and not self._has_tailwind_tokens():
            self._auto_scan_for_tailwind_configs(project_root, parser)

    def _discover_css_theme_files(self, project_root: Path, settings: Dict[str, Any]) -> None:
        """Discover and parse CSS files with @theme directives."""
        parser = CSSThemeParser()
        css_paths = settings.get('css_paths', [])

        # Search specified CSS paths
        for css_pattern in css_paths:
            css_files = project_root.glob(css_pattern)
            for css_file in css_files:
                if css_file.is_file() and parser.can_parse(css_file):
                    self._parse_css_theme_file(css_file, parser)

        # Auto-scan for @theme directives if enabled
        if settings.get('auto_scan', True):
            self._auto_scan_for_css_themes(project_root, parser)

    def _parse_tailwind_config_file(self, config_file: Path, parser: TailwindConfigParser) -> None:
        """Parse a Tailwind config file and add tokens."""
        try:
            tokens = parser.parse_file(config_file)
            self._add_tailwind_tokens(tokens)
            print(f"Discovered {len(tokens)} tokens from {config_file}")
        except Exception as e:
            print(f"Error parsing Tailwind config {config_file}: {e}")

    def _parse_css_theme_file(self, css_file: Path, parser: CSSThemeParser) -> None:
        """Parse a CSS file with @theme directives and add tokens."""
        try:
            tokens = parser.parse_file(css_file)
            if tokens:  # Only add if we found @theme tokens
                self._add_tailwind_tokens(tokens)
                print(f"Discovered {len(tokens)} tokens from {css_file}")
        except Exception as e:
            print(f"Error parsing CSS theme file {css_file}: {e}")

    def _add_tailwind_tokens(self, tokens: List[DesignTokenInfo]) -> None:
        """Add Tailwind tokens to the separate Tailwind registry."""
        for token in tokens:
            # Add to Tailwind tokens registry (separate from Style Dictionary)
            self._tailwind_tokens[token.path] = token

            # Add to Tailwind category
            if token.category not in self._tailwind_token_categories:
                self._tailwind_token_categories[token.category] = TokenCategory(
                    name=token.category.title(),
                    slug=token.category.lower(),
                    description=f"{token.category.title()} tokens from Tailwind configuration"
                )
            self._tailwind_token_categories[token.category].tokens.append(token)

    def _has_tailwind_tokens(self) -> bool:
        """Check if we already have Tailwind tokens."""
        return len(self._tailwind_tokens) > 0

    def _auto_scan_for_tailwind_configs(self, project_root: Path, parser: TailwindConfigParser) -> None:
        """Auto-scan project for Tailwind config files."""
        # Common config file patterns
        config_patterns = [
            '**/tailwind.config.js',
            '**/tailwind.config.ts',
            '**/tailwind.config.mjs',
        ]

        for pattern in config_patterns:
            config_files = project_root.glob(pattern)
            for config_file in config_files:
                if config_file.is_file() and parser.can_parse(config_file):
                    # Skip node_modules and other common directories
                    if not any(part.startswith('.') or part == 'node_modules' for part in config_file.parts):
                        self._parse_tailwind_config_file(config_file, parser)

    def _auto_scan_for_css_themes(self, project_root: Path, parser: CSSThemeParser) -> None:
        """Auto-scan project for CSS files with @theme directives."""
        # Look for CSS files that might contain @theme
        css_files = project_root.glob('**/*.css')

        for css_file in css_files:
            if css_file.is_file():
                # Skip node_modules and other common directories
                if not any(part.startswith('.') or part == 'node_modules' for part in css_file.parts):
                    try:
                        # Quick check if file contains @theme before full parsing
                        with open(css_file, 'r', encoding='utf-8') as f:
                            content = f.read(1000)  # Read first 1000 chars
                            if '@theme' in content:
                                self._parse_css_theme_file(css_file, parser)
                    except (IOError, UnicodeDecodeError):
                        continue

    # Tailwind-specific token methods
    def get_tailwind_token(self, path: str) -> Optional[DesignTokenInfo]:
        """Get a specific Tailwind token by path."""
        self.discover()
        return self._tailwind_tokens.get(path)

    def get_all_tailwind_tokens(self) -> List[DesignTokenInfo]:
        """Get all discovered Tailwind tokens."""
        self.discover()
        return list(self._tailwind_tokens.values())

    def get_tailwind_token_categories(self) -> List[TokenCategory]:
        """Get all Tailwind token categories."""
        self.discover()
        return list(self._tailwind_token_categories.values())

    def get_tailwind_tokens_by_category(self, category: str) -> List[DesignTokenInfo]:
        """Get all Tailwind tokens in a specific category."""
        self.discover()
        category_obj = self._tailwind_token_categories.get(category.lower())
        return category_obj.tokens if category_obj else []

    def search_tailwind_tokens(self, query: str) -> List[DesignTokenInfo]:
        """Search Tailwind tokens by name, path, or description."""
        self.discover()
        query = query.lower()
        results = []

        for token in self._tailwind_tokens.values():
            if (query in token.name.lower() or
                query in token.path.lower() or
                query in token.description.lower()):
                results.append(token)

        return results

    def get_tailwind_tokens_by_source(self, source_type: str) -> List[DesignTokenInfo]:
        """Get Tailwind tokens by source type (css, js)."""
        self.discover()
        return [token for token in self._tailwind_tokens.values() if token.source_type == source_type]

    def get_tailwind_token_stats(self) -> Dict[str, int]:
        """Get statistics about Tailwind tokens."""
        self.discover()
        stats = {
            'total': len(self._tailwind_tokens),
            'css_tokens': len(self.get_tailwind_tokens_by_source('css')),
            'js_tokens': len(self.get_tailwind_tokens_by_source('js')),
            'categories': len(self._tailwind_token_categories)
        }
        return stats


# Global registry instance
registry = ComponentRegistry()
