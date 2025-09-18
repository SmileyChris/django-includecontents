"""
Django management command for discovering and importing Tailwind design tokens.
"""

from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from pathlib import Path
import json

from ...registry import registry
from ...parsers import CSSThemeParser, TailwindConfigParser, TailwindTokenTransformer


class Command(BaseCommand):
    help = 'Discover and import design tokens from Tailwind configurations'

    def add_arguments(self, parser):
        parser.add_argument(
            '--config-file',
            type=str,
            help='Specific Tailwind config file to parse'
        )
        parser.add_argument(
            '--css-file',
            type=str,
            help='Specific CSS file with @theme directives to parse'
        )
        parser.add_argument(
            '--output',
            type=str,
            help='Output JSON file path for discovered tokens'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be discovered without adding to registry'
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force re-discovery even if tokens already exist'
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Show detailed output'
        )

    def handle(self, *args, **options):
        self.verbosity = int(options.get('verbosity', 1))
        self.verbose = options.get('verbose', False)

        try:
            project_root = Path(settings.BASE_DIR)
        except AttributeError:
            raise CommandError("Could not determine project root (BASE_DIR not set)")

        tokens = []

        # Parse specific files if provided
        if options['config_file']:
            tokens.extend(self._parse_config_file(project_root, options['config_file']))

        if options['css_file']:
            tokens.extend(self._parse_css_file(project_root, options['css_file']))

        # If no specific files, do full discovery
        if not options['config_file'] and not options['css_file']:
            tokens.extend(self._discover_all_tokens(project_root, options))

        # Handle output
        if not tokens:
            self.stdout.write(
                self.style.WARNING('No Tailwind tokens discovered')
            )
            return

        self._output_results(tokens, options)

        if not options['dry_run']:
            self._add_to_registry(tokens, options)

    def _parse_config_file(self, project_root: Path, config_path: str) -> list:
        """Parse a specific Tailwind config file."""
        config_file = project_root / config_path
        if not config_file.exists():
            raise CommandError(f"Config file not found: {config_file}")

        parser = TailwindConfigParser()
        if not parser.can_parse(config_file):
            raise CommandError(f"Cannot parse file: {config_file}")

        try:
            tokens = parser.parse_file(config_file)
            self._log(f"Parsed {len(tokens)} tokens from {config_file}")
            return tokens
        except Exception as e:
            raise CommandError(f"Error parsing {config_file}: {e}")

    def _parse_css_file(self, project_root: Path, css_path: str) -> list:
        """Parse a specific CSS file with @theme directives."""
        css_file = project_root / css_path
        if not css_file.exists():
            raise CommandError(f"CSS file not found: {css_file}")

        parser = CSSThemeParser()
        if not parser.can_parse(css_file):
            raise CommandError(f"Cannot parse file: {css_file}")

        try:
            tokens = parser.parse_file(css_file)
            self._log(f"Parsed {len(tokens)} tokens from {css_file}")
            return tokens
        except Exception as e:
            raise CommandError(f"Error parsing {css_file}: {e}")

    def _discover_all_tokens(self, project_root: Path, options: dict) -> list:
        """Discover all Tailwind tokens in the project."""
        self._log("Starting comprehensive Tailwind token discovery...")

        # Force full discovery by temporarily disabling lazy mode
        original_setting = getattr(settings, 'SHOWCASE_TAILWIND_DISCOVERY', {})
        temp_setting = original_setting.copy()
        temp_setting['lazy_discovery'] = False

        # Temporarily override setting
        settings.SHOWCASE_TAILWIND_DISCOVERY = temp_setting

        try:
            # Force registry refresh to trigger full discovery
            registry._discovered = False
            registry._tailwind_tokens.clear()
            registry._tailwind_token_categories.clear()

            # Trigger discovery
            registry.discover(force=True)

            # Return discovered Tailwind tokens
            tokens = list(registry._tailwind_tokens.values())
            self._log(f"Total tokens discovered: {len(tokens)}")
            return tokens

        finally:
            # Restore original setting
            if original_setting:
                settings.SHOWCASE_TAILWIND_DISCOVERY = original_setting
            else:
                delattr(settings, 'SHOWCASE_TAILWIND_DISCOVERY')

    def _discover_config_files(self, project_root: Path) -> list:
        """Discover Tailwind config files."""
        parser = TailwindConfigParser()
        tokens = []

        # Common config file patterns
        patterns = [
            'tailwind.config.js',
            'tailwind.config.ts',
            'tailwind.config.mjs',
            '**/tailwind.config.js',
            '**/tailwind.config.ts',
        ]

        for pattern in patterns:
            config_files = project_root.glob(pattern)
            for config_file in config_files:
                if self._should_parse_file(config_file):
                    try:
                        file_tokens = parser.parse_file(config_file)
                        tokens.extend(file_tokens)
                        self._log(f"Found {len(file_tokens)} tokens in {config_file}")
                    except Exception as e:
                        self._log(f"Error parsing {config_file}: {e}", error=True)

        return tokens

    def _discover_css_files(self, project_root: Path) -> list:
        """Discover CSS files with @theme directives."""
        parser = CSSThemeParser()
        tokens = []

        # Look for CSS files
        css_files = project_root.glob('**/*.css')
        for css_file in css_files:
            if self._should_parse_file(css_file):
                try:
                    # Quick check for @theme
                    with open(css_file, 'r', encoding='utf-8') as f:
                        content = f.read(1000)  # Read first 1000 chars
                        if '@theme' in content:
                            file_tokens = parser.parse_file(css_file)
                            if file_tokens:
                                tokens.extend(file_tokens)
                                self._log(f"Found {len(file_tokens)} @theme tokens in {css_file}")
                except (IOError, UnicodeDecodeError) as e:
                    self._log(f"Error reading {css_file}: {e}", error=True)

        return tokens

    def _should_parse_file(self, file_path: Path) -> bool:
        """Check if file should be parsed (skip node_modules, etc.)."""
        skip_dirs = {'.git', 'node_modules', '.venv', '__pycache__', '.pytest_cache'}
        return not any(part.startswith('.') or part in skip_dirs for part in file_path.parts)

    def _output_results(self, tokens: list, options: dict) -> None:
        """Output the discovered tokens."""
        # Group tokens by source
        by_source = {}
        for token in tokens:
            source = token.source_type
            if source not in by_source:
                by_source[source] = []
            by_source[source].append(token)

        # Display summary
        self.stdout.write(
            self.style.SUCCESS(f"\nDiscovered {len(tokens)} Tailwind design tokens:")
        )

        for source_type, source_tokens in by_source.items():
            self.stdout.write(f"  {source_type}: {len(source_tokens)} tokens")

        # Show detailed breakdown if verbose
        if self.verbose:
            self._show_detailed_breakdown(by_source)

        # Save to JSON if requested
        if options.get('output'):
            self._save_to_json(tokens, options['output'])

    def _show_detailed_breakdown(self, by_source: dict) -> None:
        """Show detailed breakdown of discovered tokens."""
        self.stdout.write("\nDetailed breakdown:")

        for source_type, tokens in by_source.items():
            self.stdout.write(f"\n{source_type.upper()} tokens:")

            # Group by category
            by_category = {}
            for token in tokens:
                cat = token.category
                if cat not in by_category:
                    by_category[cat] = []
                by_category[cat].append(token)

            for category, cat_tokens in by_category.items():
                self.stdout.write(f"  {category}: {len(cat_tokens)} tokens")
                if self.verbosity >= 2:
                    for token in cat_tokens[:5]:  # Show first 5
                        self.stdout.write(f"    - {token.path}: {token.value}")
                    if len(cat_tokens) > 5:
                        self.stdout.write(f"    ... and {len(cat_tokens) - 5} more")

    def _save_to_json(self, tokens: list, output_path: str) -> None:
        """Save tokens to JSON file."""
        transformer = TailwindTokenTransformer()

        try:
            data = transformer.export_to_json(tokens)

            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            self.stdout.write(
                self.style.SUCCESS(f"Tokens saved to {output_path}")
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"Error saving to {output_path}: {e}")
            )

    def _add_to_registry(self, tokens: list, options: dict) -> None:
        """Add Tailwind tokens to the showcase registry."""
        if not tokens:
            return

        try:
            # Force registry refresh if requested
            if options.get('force'):
                registry._tailwind_tokens.clear()
                registry._tailwind_token_categories.clear()

            # Add tokens to Tailwind registry
            for token in tokens:
                registry._tailwind_tokens[token.path] = token

                # Add to Tailwind category
                if token.category not in registry._tailwind_token_categories:
                    from ...models import TokenCategory
                    registry._tailwind_token_categories[token.category] = TokenCategory(
                        name=token.category.title(),
                        slug=token.category.lower(),
                        description=f"{token.category.title()} Tailwind design tokens"
                    )
                registry._tailwind_token_categories[token.category].tokens.append(token)

            self.stdout.write(
                self.style.SUCCESS(f"Added {len(tokens)} Tailwind tokens to showcase registry")
            )

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"Error adding to registry: {e}")
            )

    def _log(self, message: str, error: bool = False) -> None:
        """Log message if verbose mode enabled."""
        if self.verbose or error:
            if error:
                self.stdout.write(self.style.ERROR(message))
            else:
                self.stdout.write(message)