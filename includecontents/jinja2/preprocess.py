"""Source preprocessing utilities for the Jinja2 extension."""

from __future__ import annotations

import re
from html import escape
from typing import Iterable, List, Tuple


class ComponentPreprocessor:
    """Translate HTML-flavoured component syntax into Jinja2 tags."""

    component_pattern = re.compile(
        r"<(?P<closing>/)?(?P<prefix>include|html-component|icon):(?P<name>[\w-]+)(?P<attrs>(?:[^>\"']|\"[^\"]*\"|'[^']*')*)?(?P<selfclosing>/?)>",
        re.IGNORECASE,
    )

    content_pattern = re.compile(
        r"<(?P<closing>/)?content:(?P<name>[\w-]+)(?P<attrs>[^>]*)?(?P<selfclosing>/?)>",
        re.IGNORECASE,
    )

    attr_pattern = re.compile(
        r"(?P<name>[@:\w][@:\w.-]*)\s*(=\s*(?P<value>\"[^\"]*\"|'[^']*'|\{\{[^}]+\}\}|[^\s/>]+))?",
    )

    def process(self, source: str) -> str:
        """Convert custom HTML component tags into Jinja statements."""

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
        self_closing = bool(match.group("selfclosing")) or raw_attrs.rstrip().endswith("/")
        if self_closing and attrs_chunk.endswith("/"):
            attrs_chunk = attrs_chunk[:-1].rstrip()

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

        if closing:
            return "{% endcontents %}"
        else:
            return f"{{% contents \"{name}\" %}}"

    def _parse_attributes(self, chunk: str) -> List[Tuple[str, str]]:
        attributes: List[Tuple[str, str]] = []
        for attr in self.attr_pattern.finditer(chunk):
            name = attr.group("name")
            raw_value = attr.group("value")

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
            elif value.startswith("\"") and value.endswith("\""):
                inner = value[1:-1]
            elif value.startswith("'") and value.endswith("'"):
                inner = value[1:-1]
            else:
                inner = value
            attributes.append((name, inner))
        return attributes

    def _normalize_attribute_name(self, name: str) -> str:
        """Convert special attribute names to valid Jinja2 identifiers.

        Examples:
        - @click -> _at_click
        - v-on:click -> v_on_click
        - x-on:click.stop -> x_on_click_stop
        - :class -> _bind_class
        - inner.class -> inner_class
        - inner.@click -> inner_at_click
        """
        # Handle @ prefix (Vue/Alpine shorthand)
        if name.startswith("@"):
            name = "_at_" + name[1:]

        # Handle : prefix (bind shorthand)
        elif name.startswith(":"):
            name = "_bind_" + name[1:]

        # Replace special characters with underscores
        # Handle nested @, like inner.@click -> inner_at_click
        name = name.replace(".@", "_at_")
        name = name.replace(":", "_").replace("-", "_").replace(".", "_").replace("@", "_at_")

        return name

    def _build_component_tag(self, name: str, attrs: Iterable[Tuple[str, str]]) -> str:
        parts = [f'{{% includecontents "{name}"']
        for key, value in attrs:
            if value == "True":
                parts.append(f" {key}")
            elif value.startswith("{{") and value.endswith("}}"):  # expression
                expr = value[2:-2].strip()
                parts.append(f" {key}={expr}")
            else:
                quoted = escape(value, quote=True)
                parts.append(f' {key}="{quoted}"')
        parts.append(" %}")
        return "".join(parts)

    def _build_icon_tag(self, name: str, attrs: Iterable[Tuple[str, str]]) -> str:
        parts = [f'{{{{ icon("{name}"']
        for key, value in attrs:
            if value == "True":
                parts.append(f", {key}=True")
            elif value.startswith("{{") and value.endswith("}}"):  # expression
                expr = value[2:-2].strip()
                parts.append(f", {key}={expr}")
            else:
                quoted = escape(value, quote=True)
                parts.append(f', {key}="{quoted}"')
        parts.append(") }}")
        return "".join(parts)


__all__ = ["ComponentPreprocessor"]
