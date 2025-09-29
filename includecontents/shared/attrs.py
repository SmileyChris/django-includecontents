"""Engine-agnostic HTML attribute container with advanced merging and modification capabilities.

Supports multiple attribute syntaxes:

1. **JavaScript Framework Attributes** (preserved verbatim):
   - @click="handler()" - Alpine/Vue event handlers
   - x-on:click="toggle()" - Alpine.js events
   - v-model="value" - Vue.js directives
   - :disabled="isLoading" - Vue/Alpine binding (except class:)

2. **Conditional Modifiers** (merged into base attribute):
   - class:active=True - conditionally add "active" to class
   - class:disabled=False - conditionally remove "disabled" from class
   - aria:current="page" - any non-JS attribute with colon

3. **Nested Attributes** (dot notation):
   - inner.class="nested" - creates nested attrs object
   - button.data-id="123" - nested attribute with data

4. **Class Merging Syntax**:
   - class="& suffix" - append "suffix" to existing class
   - class="prefix &" - prepend "prefix" to existing class

5. **Callable Interface**:
   - attrs(class_="default") - returns new attrs with fallbacks
   - Existing attrs override provided fallbacks
   - Trailing underscores are stripped (class_ → class)
"""

from __future__ import annotations

import re
from collections.abc import Iterable, MutableMapping
from typing import Any, Dict, Iterator, Tuple


_re_camel_case = re.compile(r"(?<=.)([A-Z])")


class ConditionalAttribute:
    """
    Wrapper for attributes with conditional modifiers.

    Used for attributes like class:active=True where sub-properties
    can be conditionally toggled. Provides dot-notation access to
    check modifier states.

    Example:
        attrs['class:active'] = True
        attrs['class:disabled'] = False
        attrs.class.active  # Returns True
        attrs.class.disabled  # Returns False
        str(attrs.class)  # Returns "active" (only truthy modifiers)
    """

    def __init__(self, base_value: Any, conditional_modifiers: Dict[str, bool]):
        self._base_value = base_value
        self._conditional_modifiers = conditional_modifiers

    def __getattr__(self, name: str) -> bool:
        """Access conditional modifiers like .active, .disabled, etc."""
        return self._conditional_modifiers.get(name, False)

    def __str__(self) -> str:
        """Return the base value when converted to string"""
        return str(self._base_value)

    def __repr__(self) -> str:
        return f"ConditionalAttribute({self._base_value!r}, {self._conditional_modifiers!r})"


class BaseAttrs(MutableMapping[str, Any]):
    """
    HTML attribute container with advanced merging and modification capabilities.

    This class handles complex attribute scenarios common in HTML component systems.
    It distinguishes between different attribute syntaxes and applies appropriate
    processing to each type.

    Storage Strategy:
    - _attrs: Regular HTML attributes and JS framework attributes
    - _conditional_modifiers: Conditional modifiers that get merged (class:active, aria:current)
    - _nested_attrs: Dot-notation attributes that create sub-objects
    - _prepended_classes: Class parts that should come first in output

    Examples:
        attrs = BaseAttrs()
        attrs['class'] = 'btn'           # Regular attribute
        attrs['class:active'] = True     # Conditional modifier
        attrs['@click'] = 'handler()'    # JS framework (preserved verbatim)
        attrs['inner.class'] = 'nested'  # Nested attribute
        attrs['class'] = '& primary'     # Merge syntax (append)
    """

    def __init__(self) -> None:
        self._attrs: Dict[str, Any] = {}
        self._nested_attrs: Dict[str, BaseAttrs] = {}
        self._conditional_modifiers: Dict[str, Dict[str, bool]] = {}
        self._prepended_classes: Dict[str, Dict[str, bool]] = {}

    # ------------------------------------------------------------------
    # Mapping protocol
    # ------------------------------------------------------------------

    def __getattr__(self, key: str) -> Any:
        if key in self._nested_attrs:
            return self._nested_attrs[key]

        # Check if this attribute has conditional modifiers (class:active, etc.)
        if key in self._conditional_modifiers:
            try:
                base_value = self[key]
                return ConditionalAttribute(
                    base_value, self._conditional_modifiers[key]
                )
            except KeyError:
                # No base value, just return conditional attrs with empty base
                return ConditionalAttribute("", self._conditional_modifiers[key])

        try:
            return self[key]
        except KeyError as exc:
            raise AttributeError(key) from exc

    def __getitem__(self, key: str) -> Any:
        if key not in self._attrs:
            key = _re_camel_case.sub(r"-\1", key).lower()
        return self._attrs[key]

    @staticmethod
    def _is_js_framework_attr(key: str) -> bool:
        """
        Check if attribute is a JavaScript framework directive that should be preserved.

        JavaScript framework attributes are stored verbatim without parsing:
        - @click="handler()" (Alpine.js/Vue event handlers)
        - x-on:click="toggle()" (Alpine.js events)
        - v-model="value" (Vue.js directives)
        - :disabled="isLoading" (Vue/Alpine binding, except class:)
        """
        return (
            key.startswith("@")  # Alpine/Vue events
            or (
                key.startswith(":") and not key.startswith("class:")
            )  # Bindings except class:
            or key.startswith("v-")  # Vue directives
            or key.startswith("x-")  # Alpine directives
        )

    @staticmethod
    def _is_nested_attr(key: str) -> bool:
        """Check if attribute uses dot notation for nested objects."""
        return "." in key

    @staticmethod
    def _is_conditional_modifier(key: str) -> bool:
        """
        Check if attribute uses colon syntax for conditional modifiers.

        Conditional modifiers are merged into their base attribute:
        - class:active=True adds "active" to class if True
        - aria:current="page" sets aria["current"] = "page"
        """
        return ":" in key and not BaseAttrs._is_js_framework_attr(key)

    @staticmethod
    def _is_class_merge_syntax(key: str, value: Any) -> bool:
        """Check if this is class merge syntax (& append/prepend)."""
        return (
            key == "class"
            and isinstance(value, str)
            and (value.startswith("& ") or value.endswith(" &"))
        )

    def _store_js_framework_attr(self, key: str, value: Any) -> None:
        """Store JavaScript framework attribute verbatim."""
        self._attrs[key] = value

    def _store_nested_attr(self, key: str, value: Any) -> None:
        """Store nested attribute using dot notation."""
        nested_key, remainder = key.split(".", 1)
        nested_attrs = self._nested_attrs.setdefault(nested_key, self._new_child())
        nested_attrs[remainder] = value

    def _store_conditional_modifier(self, key: str, value: Any) -> None:
        """Store conditional modifier for later merging."""
        base_key, modifier = key.split(":", 1)
        conditional_modifiers = self._conditional_modifiers.setdefault(base_key, {})
        conditional_modifiers[modifier] = value

    def _handle_class_merge_syntax(self, key: str, value: str) -> None:
        """Handle special class merge syntax (& append/prepend)."""
        if value.startswith("& "):
            # Append syntax: "& suffix"
            conditional_modifiers = self._conditional_modifiers.setdefault(key, {})
            for bit in value[2:].split(" "):
                if bit:
                    conditional_modifiers[bit] = True
        elif value.endswith(" &"):
            # Prepend syntax: "prefix &"
            prepended = self._prepended_classes.setdefault(key, {})
            for bit in value[:-2].strip().split(" "):
                if bit:
                    prepended[bit] = True

    def __setitem__(self, key: str, value: Any) -> None:
        """
        Store attribute with appropriate handling based on key syntax.

        Dispatches to specialized storage methods based on the key pattern:
        - JS framework attrs (@click, v-model) → stored verbatim
        - Nested attrs (inner.class) → creates nested object
        - Conditional modifiers (class:active) → stored for merging
        - Class merge syntax (& append) → handled specially
        - Regular attrs → stored directly
        """
        if self._is_js_framework_attr(key):
            self._store_js_framework_attr(key, value)
        elif self._is_nested_attr(key):
            self._store_nested_attr(key, value)
        elif self._is_conditional_modifier(key):
            self._store_conditional_modifier(key, value)
        elif self._is_class_merge_syntax(key, value):
            self._handle_class_merge_syntax(key, value)
        else:
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
            if key.endswith("_") and key != "_":  # Don't strip standalone underscore
                key = key[:-1]

            # Use __setitem__ to trigger all the special handling logic
            new_attrs[key] = value

        # Then apply existing attrs (they override fallbacks)
        # Need to merge all the internal dictionaries, not just _attrs
        new_attrs.update(self)

        # Merge _conditional_modifiers dictionaries (conditional classes like class:active)
        for base_key, conditional_dict in self._conditional_modifiers.items():
            new_conditional = new_attrs._conditional_modifiers.setdefault(base_key, {})
            new_conditional.update(conditional_dict)

        # Merge _prepended_classes dictionaries (prepended classes)
        for base_key, prepended_dict in self._prepended_classes.items():
            new_prepended = new_attrs._prepended_classes.setdefault(base_key, {})
            new_prepended.update(prepended_dict)

        # Merge _nested_attrs dictionaries
        for nested_key, nested_attrs in self._nested_attrs.items():
            if nested_key not in new_attrs._nested_attrs:
                new_attrs._nested_attrs[nested_key] = nested_attrs._new_child()
            # Always merge the nested attrs - don't skip if it already exists
            new_attrs._nested_attrs[nested_key].update(nested_attrs)

            # Also merge the internal structures (conditional_modifiers, prepended) for nested attrs
            for (
                base_key,
                conditional_dict,
            ) in nested_attrs._conditional_modifiers.items():
                new_conditional = new_attrs._nested_attrs[
                    nested_key
                ]._conditional_modifiers.setdefault(base_key, {})
                new_conditional.update(conditional_dict)

            for base_key, prepended_dict in nested_attrs._prepended_classes.items():
                new_prepended = new_attrs._nested_attrs[
                    nested_key
                ]._prepended_classes.setdefault(base_key, {})
                new_prepended.update(prepended_dict)

        return new_attrs

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _new_child(self) -> BaseAttrs:
        return type(self)()

    def all_attrs(self) -> Iterable[Tuple[str, Any]]:
        """
        Yield flattened attribute key/value pairs with class merging applied.

        Processing order:
        1. Collect conditional modifiers that are truthy
        2. Collect prepended class parts
        3. For each regular attribute:
           - If it has modifiers/prepends, merge them
           - Otherwise, yield as-is
        4. Handle orphaned modifiers (no base attribute exists)
        """

        extended: Dict[str, list[str]] = {}
        prepended: Dict[str, list[str]] = {}

        for key, parts in self._conditional_modifiers.items():
            active = [name for name, flag in parts.items() if flag]
            if active:
                extended[key] = active

        for key, parts in self._prepended_classes.items():
            active = [name for name, flag in parts.items() if flag]
            if active:
                prepended[key] = active

        seen: set[str] = set()

        for key in self._attrs:
            seen.add(key)
            value = self._attrs[key]

            if key in extended or key in prepended:
                value_parts = (
                    [] if value is True or not value else str(value).split(" ")
                )

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

    def __repr__(self) -> str:
        """Return detailed representation for debugging."""
        parts = [f"{self.__class__.__name__}("]

        # Show regular attrs
        if self._attrs:
            parts.append(f"attrs={self._attrs!r}")

        # Show conditional modifiers if present
        if self._conditional_modifiers:
            if self._attrs:
                parts.append(", ")
            parts.append(f"conditional={self._conditional_modifiers!r}")

        # Show nested attrs keys if present
        if self._nested_attrs:
            if self._attrs or self._conditional_modifiers:
                parts.append(", ")
            parts.append(f"nested={list(self._nested_attrs.keys())}")

        # Show prepended classes if present
        if self._prepended_classes:
            if self._attrs or self._conditional_modifiers or self._nested_attrs:
                parts.append(", ")
            parts.append(f"prepended={self._prepended_classes!r}")

        parts.append(")")
        return "".join(parts)

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
