"""Source preprocessing utilities for the Jinja2 extension."""

from __future__ import annotations

import re

# html.escape no longer needed - escaping moved to Attrs class
from typing import Iterable, List, Tuple

from jinja2.exceptions import TemplateSyntaxError


class ComponentPreprocessor:
    """Translate HTML-flavoured component syntax into Jinja2 tags."""

    component_pattern = re.compile(
        r"<(?P<closing>/)?(?P<prefix>include|html-component|icon):(?P<name>[\w:./\-]*)(?P<attrs>(?:[^>\"']|\"[^\"]*\"|'[^']*')*)?(?P<selfclosing>/?)>",
        re.IGNORECASE,
    )

    # Pattern to catch malformed component tags - handles unbalanced quotes
    malformed_component_pattern = re.compile(
        r"<(?P<closing>/)?(?P<prefix>include|html-component|icon):(?P<name>[\w:./\-]*)[^>]*>",
        re.IGNORECASE,
    )

    content_pattern = re.compile(
        r"<(?P<closing>/)?content:(?P<name>[\w-]*)(?P<attrs>[^>]*)?(?P<selfclosing>/?)>",
        re.IGNORECASE,
    )

    attr_pattern = re.compile(
        r"(?P<name>[@:\w][@:\w.-]*)\s*(=\s*(?P<value>\"[^\"]*\"|'[^']*'|\{\{[^}]+\}\}|[^\s/>]+))?",
    )

    def process(self, source: str) -> str:
        """Convert custom HTML component tags into Jinja statements."""

        # Check for malformed component tags before processing
        self._validate_malformed_tags(source)

        # Validate proper tag matching
        self._validate_matching_tags(source)

        # First process content blocks
        source = self.content_pattern.sub(self._replace_content, source)
        # Then process components
        return self.component_pattern.sub(self._replace_component, source)

    # -- helpers ---------------------------------------------------------

    def _replace_component(self, match: re.Match[str]) -> str:
        closing = bool(match.group("closing"))
        prefix = match.group("prefix")
        name = match.group("name")
        raw_attrs = match.group("attrs") or ""
        attrs_chunk = raw_attrs.strip()
        self_closing = bool(match.group("selfclosing")) or raw_attrs.rstrip().endswith(
            "/"
        )
        if self_closing and attrs_chunk.endswith("/"):
            attrs_chunk = attrs_chunk[:-1].rstrip()

        # Validate component name
        if not name.strip():
            raise TemplateSyntaxError("Empty component name in include tag", lineno=0)

        # Handle icon tags differently
        if prefix == "icon":
            if closing:
                return ""  # Icons don't have closing tags
            attrs = self._parse_attributes(attrs_chunk)
            return self._build_icon_tag(name, attrs)

        # Handle component tags
        if closing:
            return "{% endincludecontents %}"

        attrs = self._parse_attributes(attrs_chunk)
        tag = self._build_component_tag(name, attrs)

        if self_closing:
            return f"{tag}{{% endincludecontents %}}"
        return tag

    def _replace_content(self, match: re.Match[str]) -> str:
        """Replace <content:name> tags with {% contents name %} tags."""
        closing = bool(match.group("closing"))
        name = match.group("name")

        # Validate content block name
        if not closing:
            if not name.strip():
                # Empty content names are kept as plain text, not processed
                return match.group(0)  # Return the original text unchanged
            if name and name[0].isdigit():
                raise TemplateSyntaxError(
                    f"Invalid content block name '{name}' - cannot start with a number",
                    lineno=0,
                )

        if closing:
            if not name.strip():
                # Empty content names are kept as plain text, not processed
                return match.group(0)  # Return the original text unchanged
            return "{% endcontents %}"
        else:
            return f'{{% contents "{name}" %}}'

    def _parse_attributes(self, chunk: str) -> List[Tuple[str, str]]:
        attributes: List[Tuple[str, str]] = []

        # Note: Quote validation is now handled by _validate_malformed_tags

        for attr in self.attr_pattern.finditer(chunk):
            name = attr.group("name")
            raw_value = attr.group("value")

            # Validate attribute name doesn't start with a number
            if name and name[0].isdigit():
                raise TemplateSyntaxError(
                    f"Invalid attribute name '{name}' - cannot start with a number",
                    lineno=0,
                )

            # Convert special attribute names to valid Jinja2 identifiers
            name = self._normalize_attribute_name(name)

            if raw_value is None:
                attributes.append((name, "True"))
                continue
            value = raw_value.strip()
            if value.startswith("{") and value.endswith("}"):
                inner = value
            elif value.startswith("\\"):
                inner = value
            elif value.startswith('"') and value.endswith('"'):
                inner = value[1:-1]
            elif value.startswith("'") and value.endswith("'"):
                inner = value[1:-1]
            else:
                inner = value
            attributes.append((name, inner))
        return attributes

    def _normalize_attribute_name(self, name: str) -> str:
        """Convert special attribute names to valid dictionary keys.

        With dictionary syntax, we preserve most attribute names as-is since they're quoted strings.
        Only special framework attributes need normalization for consistent handling.

        Examples:
        - @click -> @click (preserved, will be handled in extension)
        - v-on:click -> v-on:click (preserved, will be handled in extension)
        - data-role -> data-role (preserved exactly)
        - inner.class -> inner.class (preserved exactly)
        """
        # No normalization needed - dictionary keys can contain any characters
        # The extension will handle special attribute semantics during rendering
        return name

    def _build_attrs_dict(self, attrs: Iterable[Tuple[str, str]]) -> str:
        """Build a Jinja2 dictionary string from attribute key-value pairs.

        Note: This method does NOT HTML-escape attribute values, only escapes quotes
        for template syntax safety. HTML escaping is handled later by the Attrs class
        to maintain consistency with Django's behavior where hard-coded strings
        are not escaped but template variables are.
        """
        attr_items = []
        for key, value in attrs:
            if value == "True":
                attr_items.append(f'"{key}": True')
            elif value.startswith("{{") and value.endswith("}}"):  # expression
                expr = value[2:-2].strip()
                attr_items.append(f'"{key}": {expr}')
            else:
                # Escape quotes for template syntax but don't HTML-escape
                # HTML escaping is handled by Attrs class based on value source
                escaped_value = value.replace("\\", "\\\\").replace('"', '\\"')
                attr_items.append(f'"{key}": "{escaped_value}"')
        return "{" + ", ".join(attr_items) + "}"

    def _build_component_tag(self, name: str, attrs: Iterable[Tuple[str, str]]) -> str:
        if not attrs:
            return f'{{% includecontents "{name}" %}}'

        # Check if any attribute names contain hyphens or other characters
        # that make them invalid as Python identifiers
        attrs_list = list(attrs)
        needs_dict_syntax = any(
            "-" in key or ":" in key or "@" in key or "." in key or key.startswith("_")
            for key, _ in attrs_list
        )

        if needs_dict_syntax:
            # Use dictionary syntax for complex attribute names
            attrs_dict = self._build_attrs_dict(attrs_list)
            return f'{{% includecontents "{name}" {attrs_dict} %}}'
        else:
            # Use keyword argument syntax for simple attribute names
            parts = [f'{{% includecontents "{name}"']
            for key, value in attrs_list:
                if value == "True":
                    parts.append(f" {key}")
                elif value.startswith("{{") and value.endswith("}}"):  # expression
                    expr = value[2:-2].strip()
                    parts.append(f" {key}={expr}")
                else:
                    # Escape quotes for template syntax but don't HTML-escape
                    # HTML escaping is handled by Attrs class based on value source
                    escaped_value = value.replace("\\", "\\\\").replace('"', '\\"')
                    parts.append(f' {key}="{escaped_value}"')
            parts.append(" %}")
            return "".join(parts)

    def _build_icon_tag(self, name: str, attrs: Iterable[Tuple[str, str]]) -> str:
        if not attrs:
            return f'{{{{ icon("{name}") }}}}'

        attrs_dict = self._build_attrs_dict(attrs)
        return f'{{{{ icon("{name}", **{attrs_dict}) }}}}'

    def _validate_malformed_tags(self, source: str) -> None:
        """Check for malformed component tags that won't parse correctly."""
        # Look for component-like patterns that might have unclosed quotes
        # Use a more permissive pattern to catch malformed cases
        import re

        # Pattern that catches potential component tags including malformed ones
        loose_pattern = re.compile(
            r"<(?P<closing>/)?(?P<prefix>include|html-component|icon):(?P<name>[\w:./\-]*)",
            re.IGNORECASE,
        )

        # Find all potential component starts
        for match in loose_pattern.finditer(source):
            start_pos = match.start()

            # Find the end of this tag by looking for the closing >
            # while respecting quote context as much as possible
            tag_end = self._find_tag_end(source, start_pos)
            if tag_end == -1:
                continue  # Couldn't find tag end

            full_tag = source[start_pos : tag_end + 1]

            # Check if this full tag matches the well-formed pattern
            if not self.component_pattern.match(full_tag):
                # This is malformed - check if it's due to unbalanced quotes
                if self._has_unbalanced_quotes(full_tag):
                    raise TemplateSyntaxError(
                        "Unclosed quote in attribute value", lineno=0
                    )

    def _find_tag_end(self, source: str, start_pos: int) -> int:
        """Find the end position of a tag, respecting quote context."""
        pos = start_pos
        in_double_quote = False
        in_single_quote = False
        escaped = False
        last_gt_pos = -1  # Track the last > we see

        while pos < len(source):
            char = source[pos]

            if escaped:
                escaped = False
                pos += 1
                continue

            if char == "\\":
                escaped = True
            elif char == '"' and not in_single_quote:
                in_double_quote = not in_double_quote
            elif char == "'" and not in_double_quote:
                in_single_quote = not in_single_quote
            elif char == ">":
                last_gt_pos = pos  # Remember this position
                if not in_double_quote and not in_single_quote:
                    return pos  # Found proper tag end
            elif char == "<" and pos > start_pos:
                # If we hit another tag start and we're still in quotes,
                # the quotes are likely unbalanced - use the last > we saw
                if (in_double_quote or in_single_quote) and last_gt_pos != -1:
                    return last_gt_pos

            pos += 1

        # If we reach end of string while in quotes, use the last > if we found one
        if (in_double_quote or in_single_quote) and last_gt_pos != -1:
            return last_gt_pos

        return -1  # Tag never closed

    def _has_unbalanced_quotes(self, text: str) -> bool:
        """Check if a string has unbalanced quotes."""
        in_double_quote = False
        in_single_quote = False
        escaped = False

        for char in text:
            if escaped:
                escaped = False
                continue
            if char == "\\":
                escaped = True
                continue
            if char == '"' and not in_single_quote:
                in_double_quote = not in_double_quote
            elif char == "'" and not in_double_quote:
                in_single_quote = not in_single_quote

        return in_double_quote or in_single_quote

    def _validate_matching_tags(self, source: str) -> None:
        """Validate that component and content tags are properly matched."""
        stack: List[tuple[str, str, int]] = []  # (tag_type, name, position)

        # Find all tags in source order by position
        all_matches = []

        # Collect component tags
        for match in self.component_pattern.finditer(source):
            closing = bool(match.group("closing"))
            prefix = match.group("prefix")
            name = match.group("name")
            self_closing = bool(match.group("selfclosing")) or (
                match.group("attrs") or ""
            ).rstrip().endswith("/")

            if prefix == "icon":
                continue  # Icons don't have closing tags

            if self_closing:
                continue  # Self-closing tags don't need validation

            all_matches.append((match.start(), closing, "component", name))

        # Collect content tags
        for match in self.content_pattern.finditer(source):
            closing = bool(match.group("closing"))
            name = match.group("name")
            all_matches.append((match.start(), closing, "content", name))

        # Sort by position to maintain source order
        all_matches.sort(key=lambda x: x[0])

        # Validate tag matching in source order
        for pos, closing, tag_type, name in all_matches:
            if closing:
                if not stack:
                    raise TemplateSyntaxError(
                        f"Unexpected closing tag </{tag_type}:{name}>", lineno=0
                    )

                last_type, last_name, _ = stack.pop()
                if tag_type != last_type or name != last_name:
                    expected = f"</{last_type}:{last_name}>"
                    found = f"</{tag_type}:{name}>"
                    raise TemplateSyntaxError(
                        f"Mismatched closing tag: expected {expected}, found {found}",
                        lineno=0,
                    )
            else:
                stack.append((tag_type, name, pos))

        # Check for unclosed tags
        if stack:
            tag_type, name, _ = stack[-1]
            if tag_type == "component":
                raise TemplateSyntaxError(f"Unclosed component tag '{name}'", lineno=0)
            else:
                raise TemplateSyntaxError(f"Unclosed content block '{name}'", lineno=0)


__all__ = ["ComponentPreprocessor"]
