"""Engine-agnostic HTML attribute container."""

from __future__ import annotations

import re
from collections.abc import Iterable, MutableMapping
from typing import Any, Dict, Iterator, Tuple


_re_camel_case = re.compile(r"(?<=.)([A-Z])")


class ExtendedAttribute:
    """Wrapper for attributes that have extended properties (class:active, etc.)"""

    def __init__(self, base_value: Any, extended_attrs: Dict[str, bool]):
        self._base_value = base_value
        self._extended_attrs = extended_attrs

    def __getattr__(self, name: str) -> bool:
        """Access extended attributes like .active, .disabled, etc."""
        return self._extended_attrs.get(name, False)

    def __str__(self) -> str:
        """Return the base value when converted to string"""
        return str(self._base_value)

    def __repr__(self) -> str:
        return f"ExtendedAttribute({self._base_value!r}, {self._extended_attrs!r})"


class BaseAttrs(MutableMapping[str, Any]):
    """Collects attributes with support for nested groups and class merging."""

    def __init__(self) -> None:
        self._attrs: Dict[str, Any] = {}
        self._nested_attrs: Dict[str, BaseAttrs] = {}
        self._extended: Dict[str, Dict[str, bool]] = {}
        self._prepended: Dict[str, Dict[str, bool]] = {}

    # ------------------------------------------------------------------
    # Mapping protocol
    # ------------------------------------------------------------------

    def __getattr__(self, key: str) -> Any:
        if key in self._nested_attrs:
            return self._nested_attrs[key]

        # Check if this attribute has extended properties (class:active, etc.)
        if key in self._extended:
            try:
                base_value = self[key]
                return ExtendedAttribute(base_value, self._extended[key])
            except KeyError:
                # No base value, just return extended attrs with empty base
                return ExtendedAttribute("", self._extended[key])

        try:
            return self[key]
        except KeyError as exc:
            raise AttributeError(key) from exc

    def __getitem__(self, key: str) -> Any:
        if key not in self._attrs:
            key = _re_camel_case.sub(r"-\1", key).lower()
        return self._attrs[key]

    def __setitem__(self, key: str, value: Any) -> None:
        # Preserve JavaScript style attributes verbatim (@click, :bind, etc.)
        if (
            key.startswith("@")
            or (key.startswith(":") and not key.startswith("class:"))
            or key.startswith("v-")
            or key.startswith("x-")
        ):
            self._attrs[key] = value
            return

        if "." in key:
            nested_key, remainder = key.split(".", 1)
            nested_attrs = self._nested_attrs.setdefault(nested_key, self._new_child())
            nested_attrs[remainder] = value
            return


        if ":" in key:
            base_key, extend_key = key.split(":", 1)
            extended = self._extended.setdefault(base_key, {})
            extended[extend_key] = value
            return

        if key == "class" and isinstance(value, str) and value.startswith("& "):
            extended = self._extended.setdefault(key, {})
            for bit in value[2:].split(" "):
                if bit:
                    extended[bit] = True
            return

        if key == "class" and isinstance(value, str) and value.endswith(" &"):
            prepended = self._prepended.setdefault(key, {})
            for bit in value[:-2].strip().split(" "):
                if bit:
                    prepended[bit] = True
            return

        self._attrs[key] = value

    def __delitem__(self, key: str) -> None:
        del self._attrs[key]

    def __iter__(self) -> Iterator[str]:
        return iter(self._attrs)

    def __len__(self) -> int:
        return len(self._attrs)

    # ------------------------------------------------------------------
    # Callable interface
    # ------------------------------------------------------------------

    def __call__(self, **kwargs) -> BaseAttrs:
        """
        Return a new Attrs object with fallbacks applied.

        Examples:
        - Simple: attrs(class_='btn', type='button')  # trailing _ stripped
        - Complex names via unpacking: attrs(**{'data-id': '123', '@click': 'handler'})
        - Mixed: attrs(type='button', **{'@click': 'handler'})

        Special syntaxes:
        - class_="& suffix" or class="& suffix" - append to existing class
        - class_="prefix &" or class="prefix &" - prepend to existing class
        - Use **{'class:active': True} for conditional classes

        Trailing underscores are stripped from keyword arguments to allow
        using Python reserved words: class_='btn' becomes class='btn'.

        Returns a new Attrs object with fallbacks applied (immutable).
        """
        new_attrs = self._new_child()

        # First apply the fallbacks
        for key, value in kwargs.items():
            # Strip trailing underscore from keyword arguments (e.g. class_ -> class)
            if key.endswith('_') and key != '_':  # Don't strip standalone underscore
                key = key[:-1]

            # Use __setitem__ to trigger all the special handling logic
            new_attrs[key] = value

        # Then apply existing attrs (they override fallbacks)
        # Need to merge all the internal dictionaries, not just _attrs
        new_attrs.update(self)

        # Merge _extended dictionaries (conditional classes like class:active)
        for base_key, extended_dict in self._extended.items():
            new_extended = new_attrs._extended.setdefault(base_key, {})
            new_extended.update(extended_dict)

        # Merge _prepended dictionaries (prepended classes)
        for base_key, prepended_dict in self._prepended.items():
            new_prepended = new_attrs._prepended.setdefault(base_key, {})
            new_prepended.update(prepended_dict)

        # Merge _nested_attrs dictionaries
        for nested_key, nested_attrs in self._nested_attrs.items():
            if nested_key not in new_attrs._nested_attrs:
                new_attrs._nested_attrs[nested_key] = nested_attrs._new_child()
                new_attrs._nested_attrs[nested_key].update(nested_attrs)

        return new_attrs

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _new_child(self) -> BaseAttrs:
        return type(self)()

    def all_attrs(self) -> Iterable[Tuple[str, Any]]:
        """Yield flattened attribute key/value pairs with class merging applied."""

        extended: Dict[str, list[str]] = {}
        prepended: Dict[str, list[str]] = {}

        for key, parts in self._extended.items():
            active = [name for name, flag in parts.items() if flag]
            if active:
                extended[key] = active

        for key, parts in self._prepended.items():
            active = [name for name, flag in parts.items() if flag]
            if active:
                prepended[key] = active

        seen: set[str] = set()

        for key in self._attrs:
            seen.add(key)
            value = self._attrs[key]

            if key in extended or key in prepended:
                value_parts = [] if value is True or not value else str(value).split(" ")

                if key in prepended:
                    prepend_parts = prepended[key]
                    value_parts = prepend_parts + [
                        part for part in value_parts if part not in prepend_parts
                    ]

                if key in extended:
                    for part in extended[key]:
                        if part not in value_parts:
                            value_parts.append(part)

                value = " ".join(value_parts) if value_parts else None

            yield key, value

        for key in list(extended.keys()) + list(prepended.keys()):
            if key in seen:
                continue
            value_parts: list[str] = []
            value_parts.extend(prepended.get(key, []))
            for part in extended.get(key, []):
                if part not in value_parts:
                    value_parts.append(part)
            value = " ".join(value_parts) if value_parts else None
            yield key, value

    # ------------------------------------------------------------------
    # String rendering
    # ------------------------------------------------------------------

    def __str__(self) -> str:
        """Render attributes as HTML string with engine-specific formatting."""
        parts = []
        for key, value in self.all_attrs():
            if value is None:
                continue
            if value is True:
                parts.append(key)
            else:
                parts.append(self._render_attr(key, value))
        return " ".join(parts)

    def _render_attr(self, key: str, value: Any) -> str:
        """Render a single attribute. Override in subclasses for engine-specific escaping."""
        return f'{key}="{value}"'


__all__ = ["BaseAttrs"]
