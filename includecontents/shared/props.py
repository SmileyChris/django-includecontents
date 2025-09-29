"""Shared utilities for parsing component props metadata."""

from __future__ import annotations

import ast
import re
import shlex
from dataclasses import dataclass
from typing import Any, Callable, Dict, Generic, Optional, Sequence, Tuple, TypeVar


_MISSING = object()


def _is_valid_prop_name(name: str) -> bool:
    """Check if a prop name is a valid Python identifier."""
    if "-" in name:
        if name.startswith("data-") or name.startswith("aria-"):
            candidate = name.replace("-", "_")
            return candidate.isidentifier() and not candidate.startswith("_")
        return False
    return name.isidentifier() and not name.startswith("_")


def _raise_props_parsing_error(
    message: str, body: str, source: str, token: str = None
) -> None:
    """Raise a helpful error for props parsing issues."""
    import re

    # Find the line number of the props comment
    lines = source.split("\n")
    props_line_num = 1
    for i, line in enumerate(lines, 1):
        if re.search(r"{#\s*props\s+.*?#}", line):
            props_line_num = i
            break

    error_parts = [
        f"Props parsing error: {message}",
        f"  In template line {props_line_num}: {{# props {body} #}}",
    ]

    if token:
        error_parts.append(f"  Problem with: '{token}'")

    # Add helpful suggestions
    error_parts.extend(
        [
            "",
            "Common issues:",
            "  - Prop names must be valid Python identifiers (no spaces, special chars)",
            '  - String values should be quoted: name="value"',
            "  - Lists should use brackets: items=[1,2,3]",
            "  - Use commas or spaces to separate props: prop1=value1 prop2=value2",
            "",
            "Examples:",
            "  {# props title required_field=True items=[1,2,3] #}",
            '  {# props variant=primary,secondary,accent size="large" #}',
        ]
    )

    from django.template import TemplateSyntaxError

    raise TemplateSyntaxError("\n".join(error_parts))


@dataclass(frozen=True)
class PropSpec:
    """Represents a declared component prop."""

    name: str
    default: Any = _MISSING

    @property
    def required(self) -> bool:
        return self.default is _MISSING

    def clone_default(self) -> Any:
        if self.required:
            return _MISSING
        value = self.default
        try:
            from copy import deepcopy

            return deepcopy(value)
        except Exception:  # pragma: no cover - defensive fallback
            return value


_PROPS_COMMENT_RE = re.compile(
    r"^\s*{#\s*props(?P<body>.*?)#}", re.DOTALL | re.IGNORECASE | re.MULTILINE
)


def parse_props_comment(source: str) -> Dict[str, PropSpec]:
    """Extract a mapping of prop name to :class:`PropSpec` from ``source``."""

    match = _PROPS_COMMENT_RE.search(source)
    if not match:
        return {}

    body = match.group("body").strip()
    if not body:
        return {}

    specs: Dict[str, PropSpec] = {}
    try:
        tokens = _tokenize_props_body(body)
    except Exception as e:
        _raise_props_parsing_error(
            f"Failed to tokenize props comment: {e}", body, source
        )

    for token in tokens:
        if not token:
            continue
        try:
            name, default = _parse_prop_token(token)
            if name in specs:
                _raise_props_parsing_error(
                    f"Duplicate prop definition: '{name}'", body, source, token
                )
            specs[name] = PropSpec(name=name, default=default)
        except Exception as e:
            _raise_props_parsing_error(
                f"Invalid prop definition '{token}': {e}", body, source, token
            )
    return specs


def _tokenize_props_body(body: str) -> list[str]:
    lexer = shlex.shlex(body, posix=True)
    lexer.whitespace_split = True
    lexer.commenters = ""
    tokens: list[str] = []
    for token in lexer:
        token = token.strip()
        if token.endswith(","):
            token = token[:-1]
        if token:
            tokens.append(token)
    return tokens


def _parse_prop_token(token: str) -> tuple[str, Any]:
    if "=" not in token:
        name = token.strip()
        if not name:
            raise ValueError("Empty prop name")
        if not _is_valid_prop_name(name):
            raise ValueError(
                f"Invalid prop name '{name}'. Prop names must be valid Python identifiers."
            )
        return name, _MISSING

    parts = token.split("=", 1)
    if len(parts) != 2:
        raise ValueError(f"Invalid prop syntax. Expected 'name=value', got '{token}'")

    name, raw = parts
    name = name.strip()
    raw = raw.strip()

    if not name:
        raise ValueError("Empty prop name")
    if not _is_valid_prop_name(name):
        raise ValueError(
            f"Invalid prop name '{name}'. Prop names must be valid Python identifiers."
        )

    if not raw:
        return name, ""

    try:
        value = ast.literal_eval(raw)
    except (ValueError, SyntaxError) as e:
        # Check if this looks like a comma-separated enum (common pattern)
        if (
            "," in raw
            and " " not in raw
            and not any(c in raw for c in ["(", ")", "[", "]", "{", "}", '"', "'"])
        ):
            # This is likely an enum definition like "primary,secondary,accent"
            value = raw
        # For strings that look like they should be quoted, provide helpful hint
        elif (
            raw
            and not raw.startswith(('"', "'"))
            and any(c in raw for c in [" ", "(", ")", "[", "]", "{"])
        ):
            raise ValueError(
                f"Invalid value '{raw}'. Did you forget quotes around a string value?"
            ) from e
        else:
            # Otherwise treat as raw string
            value = raw
    except Exception as e:
        raise ValueError(f"Invalid value '{raw}': {e}") from e

    return name, value


K = TypeVar("K")


@dataclass
class _PropsEntry:
    props: Dict[str, PropSpec]
    uptodate: Optional[Callable[[], bool]]

    def is_fresh(self) -> bool:
        if self.uptodate is None:
            return True
        try:
            return bool(self.uptodate())
        except Exception:  # pragma: no cover - defensive
            return False


class PropsRegistry(Generic[K]):
    """Cache for parsed props keyed by template identifier."""

    def __init__(
        self, source_loader: Callable[[K], Tuple[str, Optional[Callable[[], bool]]]]
    ) -> None:
        self._source_loader = source_loader
        self._cache: Dict[K, _PropsEntry] = {}

    def get(self, key: K) -> Dict[str, PropSpec]:
        entry = self._cache.get(key)
        if entry is not None and entry.is_fresh():
            return entry.props

        source, uptodate = self._source_loader(key)
        props = parse_props_comment(source)
        self._cache[key] = _PropsEntry(props, uptodate)
        return props

    def clear(self) -> None:
        self._cache.clear()


@dataclass(frozen=True)
class PropDefinition:
    """
    Represents a component prop definition with optional enum validation.

    Wraps a PropSpec and adds enum-specific metadata when the prop
    is defined with enum constraints.
    """

    spec: PropSpec
    enum_values: Sequence[str] | None = None
    enum_required: bool = False

    @property
    def name(self) -> str:
        return self.spec.name

    @property
    def required(self) -> bool:
        if self.enum_values is not None:
            return self.enum_required
        return self.spec.required

    def clone_default(self) -> Any:
        return self.spec.clone_default()

    def is_enum(self) -> bool:
        return self.enum_values is not None


def build_prop_definition(spec: PropSpec) -> PropDefinition:
    """
    Build a PropDefinition from a PropSpec, parsing any enum constraints.

    If the spec's default value contains enum definition syntax (e.g., "a,b,c" or "!a,b,c"),
    this function extracts the allowed values and required flag.
    """
    from includecontents.shared.enums import parse_enum_definition

    default = spec.default
    allowed, required = parse_enum_definition(default)
    if allowed:
        return PropDefinition(spec=spec, enum_values=allowed, enum_required=required)
    return PropDefinition(spec=spec)


__all__ = [
    "PropSpec",
    "PropsRegistry",
    "parse_props_comment",
    "PropDefinition",
    "build_prop_definition",
    "_MISSING",
]
