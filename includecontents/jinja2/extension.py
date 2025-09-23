"""Jinja2 extension providing includecontents-style components."""

from __future__ import annotations

from typing import Any, Dict, Iterator, List, Optional

from jinja2 import Environment, nodes, pass_context
from jinja2.exceptions import TemplateRuntimeError
from jinja2.ext import Extension
from jinja2.lexer import Token, TokenStream
from jinja2.parser import Parser

from .attrs import Attrs
from .context import CapturedContents, ComponentContext
from .preprocess import ComponentPreprocessor
from .props import create_props_registry
from includecontents.shared.enums import (
    build_enum_flag_key,
    normalize_enum_values,
    parse_enum_definition,
    suggest_enum_value,
)


class IncludeContentsExtension(Extension):
    """Implements ``includecontents`` / ``contents`` tags for Jinja2 templates."""

    tags = {"includecontents", "contents"}

    def __init__(self, environment: Environment) -> None:  # noqa: D401
        super().__init__(environment)
        self.preprocessor = ComponentPreprocessor()
        self._register_environment_helpers(environment)
        self._props_registry = create_props_registry(environment)
        self._render_stack: List[Dict[str, Any]] = []
        self.use_context_isolation = True

    # ------------------------------------------------------------------
    # Lifecycle hooks
    # ------------------------------------------------------------------

    def preprocess(
        self, source: str, name: Optional[str], filename: Optional[str] = None
    ) -> str:
        return self.preprocessor.process(source)

    def filter_stream(self, stream: TokenStream) -> Iterator[Token]:
        yield from stream

    def parse(self, parser: Parser) -> nodes.Node:
        token = next(parser.stream)
        if token.value == "includecontents":
            return self._parse_includecontents(parser, token)
        if token.value == "contents":
            return self._parse_contents(parser, token)
        parser.fail(f"Unsupported tag '{token.value}'", token.lineno)

    # ------------------------------------------------------------------
    # Parsing helpers
    # ------------------------------------------------------------------

    def _parse_includecontents(self, parser: Parser, token: Token) -> nodes.Node:
        lineno = token.lineno
        component_name = parser.parse_expression()
        args: List[nodes.Expr] = [component_name]
        kwargs: List[nodes.Keyword] = []

        while parser.stream.current.type != "block_end":
            if parser.stream.current.type == "comma":
                parser.stream.skip()
                continue
            key_token = parser.stream.expect("name")
            if parser.stream.current.test("assign"):
                parser.stream.skip()
                value = parser.parse_expression()
            else:
                value = nodes.Const(True, lineno=key_token.lineno)
            kwargs.append(nodes.Keyword(key_token.value, value, lineno=value.lineno))

        body = parser.parse_statements(("name:endincludecontents",), drop_needle=True)
        call = self.call_method(
            "_render_includecontents",
            args=args,
            kwargs=kwargs,
            lineno=lineno,
        )
        node = nodes.CallBlock(call, [], [], body)
        node.set_lineno(lineno)
        return node

    def _parse_contents(self, parser: Parser, token: Token) -> nodes.Node:
        lineno = token.lineno
        current = parser.stream.current
        if current.type == "block_end":
            name_expr: nodes.Expr = nodes.Const(None, lineno=lineno)
        elif current.type == "name":
            name_token = next(parser.stream)
            name_expr = nodes.Const(name_token.value, lineno=name_token.lineno)
        else:
            name_expr = parser.parse_expression()

        body = parser.parse_statements(("name:endcontents",), drop_needle=True)
        call = self.call_method(
            "_capture_contents",
            args=[name_expr],
            lineno=lineno,
        )
        node = nodes.CallBlock(call, [], [], body)
        node.set_lineno(lineno)
        return node

    # ------------------------------------------------------------------
    # Runtime helpers
    # ------------------------------------------------------------------

    @pass_context
    def _render_includecontents(
        self,
        context: Any,
        template_name: Any,
        caller: Optional[Any] = None,
        **attributes: Any,
    ) -> str:
        state: Dict[str, Any] = {"default": [], "named": {}}
        self._render_stack.append(state)
        try:
            body_output = caller() if caller is not None else ""
        finally:
            self._render_stack.pop()

        identifier = self._normalize_template_name(template_name)
        props = self._props_registry.get(identifier)

        default_content = "".join(state["default"]) or body_output
        contents = CapturedContents(default_content, state["named"])

        attrs_obj = Attrs()
        prop_values: Dict[str, Any] = {}

        enum_specs: Dict[str, tuple[tuple[str, ...], bool]] = {}
        if props:
            for name, spec in props.items():
                allowed_values, enum_required = parse_enum_definition(
                    getattr(spec, "default", None)
                )
                if allowed_values:
                    enum_specs[name] = (allowed_values, enum_required)

        if props:
            for key, value in attributes.items():
                if key in props:
                    prop_spec = props[key]
                    prop_values[key] = value
                    if isinstance(value, bool) and value:
                        attrs_obj[key] = True

                    # Validate enum values
                    enum_info = enum_specs.get(key)
                    if enum_info:
                        allowed_values, _ = enum_info
                        for enum_value in normalize_enum_values(value):
                            if enum_value not in allowed_values:
                                allowed = ", ".join(repr(v) for v in allowed_values)
                                suggestion = suggest_enum_value(enum_value, allowed_values)
                                suggestion_text = f" Did you mean {suggestion!r}?" if suggestion else ""

                                # Create a helpful example
                                first_value = allowed_values[0] if allowed_values else "value"
                                example = f'<include:{identifier.replace("components/", "").replace(".html", "")} {key}="{first_value}">'

                                raise TemplateRuntimeError(
                                    f'Invalid value "{enum_value}" for attribute "{key}" '
                                    f"in component '{identifier}'. Allowed values: {allowed}.{suggestion_text}\n"
                                    f"Example: {example}"
                                )
                            flag_key = build_enum_flag_key(key, enum_value)
                            if flag_key:
                                prop_values[flag_key] = True
                else:
                    attrs_obj[key] = value

            for name, spec in props.items():
                if name not in prop_values:
                    enum_info = enum_specs.get(name)
                    if enum_info:
                        _, enum_required = enum_info
                        if enum_required:
                            raise TemplateRuntimeError(
                                f"Component '{identifier}' missing required prop '{name}'"
                            )
                        continue
                    if spec.required:
                        raise TemplateRuntimeError(
                            f"Component '{identifier}' missing required prop '{name}'"
                        )
                    prop_values[name] = spec.clone_default()
        else:
            prop_values = dict(attributes)
            for key, value in attributes.items():
                attrs_obj[key] = value

        template = self.environment.get_template(identifier)
        parent_vars = context.get_all()
        if props and self.use_context_isolation:
            component_context = ComponentContext.create_isolated(parent_vars, prop_values)
        else:
            component_context = parent_vars.copy()
            component_context.update(prop_values)
        component_context["attrs"] = attrs_obj
        component_context["contents"] = contents
        return template.render(component_context)

    @pass_context
    def _capture_contents(
        self,
        context: Any,
        name: Any,
        caller: Optional[Any] = None,
        **_: Any,
    ) -> str:
        content = caller() if caller is not None else ""
        if not self._render_stack:
            return content
        state = self._render_stack[-1]
        key = self._normalize_content_name(name)
        if key is None:
            state["default"].append(content)
        else:
            state["named"][key] = content
        return ""

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _register_environment_helpers(self, environment: Environment) -> None:
        environment.filters.setdefault("component_attrs", str)

        # Register icon function if available
        try:
            environment.globals.setdefault("icon", self._icon_function)
        except ImportError:
            # Icons not available, skip
            pass

    def _icon_function(self, icon_name: str, **attributes) -> str:
        """Jinja2-compatible icon function."""
        try:
            from includecontents.icons.templatetags.icons import IconNode

            # Create an IconNode and render it
            icon_node = IconNode(icon_name, attributes)
            # We need a context-like object, but for icons we can pass minimal context
            context = {}
            return icon_node.render(context)
        except ImportError:
            # Icons not available
            return f'<!-- Icon "{icon_name}" not available -->'
        except Exception:
            # Error rendering icon
            return f'<!-- Error rendering icon "{icon_name}" -->'

    def _normalize_content_name(self, name: Any) -> Optional[str]:
        if name in (None, "", False):
            return None
        return str(name)

    def _normalize_template_name(self, template_name: Any) -> str:
        if isinstance(template_name, str):
            identifier = template_name
        else:
            identifier = str(template_name)
        if not identifier.endswith(".html") and "/" not in identifier:
            identifier = f"components/{identifier}.html"
        return identifier


__all__ = ["IncludeContentsExtension"]
