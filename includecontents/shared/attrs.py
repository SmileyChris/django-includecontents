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

    # Intentionally leave __str__ abstract; engine wrappers should format output.


__all__ = ["BaseAttrs"]
