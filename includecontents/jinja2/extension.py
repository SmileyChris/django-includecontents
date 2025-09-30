"""Jinja2 extension providing includecontents-style components."""

from __future__ import annotations

from typing import Any, Dict, Iterator, List, Optional

from jinja2 import Environment, nodes, pass_context, Undefined
from jinja2.exceptions import TemplateNotFound, TemplateRuntimeError
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
    suggest_enum_value,
)
from includecontents.shared.props import PropDefinition, build_prop_definition


class _EscapableValue:
    """Wrapper to mark values that came from template expressions and need escaping.

    This class is used to distinguish between:
    - Hard-coded strings in component syntax: <include:button text="Don't worry" />
    - Template variables in component syntax: <include:button text="{{ user_input }}" />

    Hard-coded strings are treated as safe/trusted content and are NOT escaped.
    Template variables are wrapped in _EscapableValue to indicate they should be escaped
    for security (to prevent XSS attacks from user-provided content).

    This matches Django's behavior where literal strings in template syntax are not escaped
    but variable content is escaped via conditional_escape().
    """

    def __init__(self, value: Any):
        self.value = value

    def __str__(self) -> str:
        return str(self.value)

    def __repr__(self) -> str:
        return f"_EscapableValue({self.value!r})"


class IncludeContentsExtension(Extension):
    """Implements ``includecontents`` / ``contents`` tags for Jinja2 templates.

    HTML Escaping Strategy:
    ----------------------
    This extension matches Django's escaping behavior:

    1. Hard-coded strings in component syntax are NOT escaped:
       <include:button text="Don't worry" /> → text="Don't worry"

    2. Template variables in component syntax ARE escaped:
       <include:button text="{{ user_input }}" /> → text="Don&#39;t worry"

    This is achieved by:
    - Preprocessor: Only escapes quotes for template syntax, no HTML escaping
    - Extension: Wraps template expression results in _EscapableValue
    - Attrs class: Selectively escapes based on _EscapableValue wrapper

    This provides security (XSS protection) for user content while preserving
    developer intent for literal strings.
    """

    tags = {"includecontents", "contents"}

    def __init__(self, environment: Environment) -> None:  # noqa: D401
        super().__init__(environment)
        self.preprocessor = ComponentPreprocessor()
        self._register_environment_helpers(environment)
        self._props_registry = create_props_registry(environment)
        self._render_stack: List[Dict[str, Any]] = []
        self.use_context_isolation = True
        self._component_environment: Optional[Environment] = None

    @property
    def component_environment(self) -> Environment:
        """Get or create an environment specifically for component rendering.

        This environment uses standard Undefined behavior to ensure
        components render undefined variables as empty strings,
        regardless of the main environment's debug settings.

        Uses Jinja2's overlay() method for efficient environment cloning.
        """
        if self._component_environment is None:
            # Create overlay environment with standard Undefined behavior
            # This automatically inherits all settings from parent environment
            self._component_environment = self.environment.overlay(undefined=Undefined)
        return self._component_environment

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

            # Check if this looks like a dictionary (starts with {)
            if parser.stream.current.test("lbrace"):
                dict_expr = parser.parse_expression()
                # Add dictionary as a special argument that we'll handle in render
                args.append(dict_expr)
                break
            else:
                # Parse individual attribute name (traditional keyword syntax)
                key_token = parser.stream.expect("name")
                key_name = key_token.value

                if parser.stream.current.test("assign"):
                    parser.stream.skip()
                    value = parser.parse_expression()
                else:
                    value = nodes.Const(True, lineno=lineno)
                kwargs.append(nodes.Keyword(key_name, value, lineno=lineno))

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
        *args: Any,
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

        # Handle dictionary unpacking arguments (**{...})
        for arg in args:
            if isinstance(arg, dict):
                attributes.update(arg)

        default_content = "".join(state["default"]) or body_output
        contents = CapturedContents(default_content, state["named"])

        attrs_obj = Attrs()
        prop_values: Dict[str, Any] = {}

        # Build prop definitions with enum validation info
        prop_definitions: Dict[str, PropDefinition] = {}
        if props:
            for name, spec in props.items():
                prop_definitions[name] = build_prop_definition(spec)

        if props:
            for key, value in attributes.items():
                # Process template expressions in attribute values
                processed_value = self._process_template_expression(value, context)

                # Handle bound attributes (e.g., :title)
                if key.startswith(":"):
                    prop_name = key[1:]  # Remove the : prefix
                    if prop_name in props:
                        prop_values[prop_name] = processed_value
                        if isinstance(value, bool) and value:
                            attrs_obj[prop_name] = True

                        # Validate enum values
                        prop_def = prop_definitions.get(prop_name)
                        if prop_def and prop_def.is_enum():
                            allowed_values = prop_def.enum_values or ()
                            for enum_value in normalize_enum_values(processed_value):
                                if enum_value not in allowed_values:
                                    allowed = ", ".join(repr(v) for v in allowed_values)
                                    suggestion = suggest_enum_value(
                                        enum_value, allowed_values
                                    )
                                    suggestion_text = (
                                        f" Did you mean {suggestion!r}?"
                                        if suggestion
                                        else ""
                                    )

                                    # Create a helpful example
                                    first_value = (
                                        allowed_values[0] if allowed_values else "value"
                                    )
                                    example = f'<include:{identifier.replace("components/", "").replace(".html", "")} {prop_name}="{first_value}">'

                                    raise TemplateRuntimeError(
                                        f'Invalid value "{enum_value}" for attribute "{prop_name}" '
                                        f"in component '{identifier}'. Allowed values: {allowed}.{suggestion_text}\n"
                                        f"Example: {example}"
                                    )
                                flag_key = build_enum_flag_key(prop_name, enum_value)
                                if flag_key:
                                    prop_values[flag_key] = True
                    else:
                        # Bound attribute that's not a prop goes to attrs
                        attrs_obj[key] = value
                elif key in props:
                    prop_values[key] = processed_value
                    if isinstance(value, bool) and value:
                        attrs_obj[key] = True

                    # Validate enum values
                    prop_def = prop_definitions.get(key)
                    if prop_def and prop_def.is_enum():
                        allowed_values = prop_def.enum_values or ()
                        for enum_value in normalize_enum_values(processed_value):
                            if enum_value not in allowed_values:
                                allowed = ", ".join(repr(v) for v in allowed_values)
                                suggestion = suggest_enum_value(
                                    enum_value, allowed_values
                                )
                                suggestion_text = (
                                    f" Did you mean {suggestion!r}?"
                                    if suggestion
                                    else ""
                                )

                                # Create a helpful example
                                first_value = (
                                    allowed_values[0] if allowed_values else "value"
                                )
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
                    attrs_obj[key] = processed_value

            for name, prop_def in prop_definitions.items():
                if name not in prop_values:
                    # PropDefinition.required already accounts for enum_required
                    if prop_def.required:
                        raise TemplateRuntimeError(
                            f"Component '{identifier}' missing required prop '{name}'"
                        )
                    # Skip enums with defaults - they don't set a value, just allow certain values
                    if prop_def.is_enum():
                        continue
                    prop_values[name] = prop_def.clone_default()
        else:
            # No props defined, use attributes as-is
            prop_values = {}
            for key, value in attributes.items():
                processed_value = self._process_template_expression(value, context)
                prop_values[key] = processed_value
                attrs_obj[key] = processed_value

        try:
            template = self.component_environment.get_template(identifier)
        except TemplateNotFound as e:
            # Enhance error message with component name
            component_name = identifier.replace("components/", "").replace(".html", "")
            if ":" in component_name:
                namespace, name = component_name.split(":", 1)
                raise TemplateNotFound(
                    f"Component template not found: {namespace}:{name} (looked for {identifier})"
                ) from e
            else:
                raise TemplateNotFound(
                    f"Component template not found: {component_name} (looked for {identifier})"
                ) from e

        # Use flattened context for better Django parity
        parent_vars = self._flatten_jinja_context(context)
        if props and self.use_context_isolation:
            component_context = ComponentContext.create_isolated(
                parent_vars, prop_values
            )
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
            return content  # Render as plain text outside components
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
            # Create a standalone function that can be decorated with pass_context
            def icon_function(context, icon_name: str, **attributes) -> str:
                return self._icon_function(context, icon_name, **attributes)

            environment.globals.setdefault("icon", pass_context(icon_function))
        except ImportError:
            # Icons not available, skip
            pass

    def _icon_function(self, context, icon_name: str, **attributes) -> str:
        """Jinja2-compatible icon function."""
        try:
            from includecontents.icons.templatetags.icons import IconNode

            # Process template variables in attribute values
            processed_attributes = {}
            for key, value in attributes.items():
                if isinstance(value, str) and ("{{" in value or "{%" in value):
                    try:
                        # Create and render mini-template for this attribute value
                        mini_template = self.environment.from_string(value)
                        processed_value = mini_template.render(context.get_all())
                        processed_attributes[key] = processed_value
                    except Exception:
                        # If processing fails, use original value
                        processed_attributes[key] = value
                else:
                    processed_attributes[key] = value

            # Create an IconNode and render it
            icon_node = IconNode(icon_name, processed_attributes)

            # Create minimal context-like object for Django compatibility
            class MinimalContext:
                def get(self, key, default=None):
                    return default

            return icon_node.render(MinimalContext())
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

        # Handle namespaced components (forms:field -> forms/field)
        identifier = identifier.replace(":", "/")

        if not identifier.endswith(".html") and "/" not in identifier:
            identifier = f"components/{identifier}.html"
        elif not identifier.endswith(".html"):
            identifier = f"components/{identifier}.html"
        return identifier

    def _process_template_expression(self, value: Any, context: Any) -> Any:
        """Process template expressions in attribute values.

        This method evaluates template variables ({{ }}) and control structures ({% %})
        within attribute values to provide Django template parity.
        """
        # Handle Undefined objects from Jinja2 - convert to empty string
        # This ensures props with undefined variables render as empty strings
        # even when the main environment uses DebugUndefined or StrictUndefined
        if isinstance(value, Undefined):
            return ""

        if not isinstance(value, str):
            return value

        # If the value contains template syntax, render it as a mini-template
        if "{{" in value or "{%" in value:
            try:
                # Create a mini-template from the value with autoescape enabled
                # to ensure variables get escaped like in Django
                # Also use standard Undefined to render undefined vars as empty strings
                env = self.environment.overlay(autoescape=True, undefined=Undefined)
                mini_template = env.from_string(value)
                # Render with the current context variables
                parent_vars = context.get_all()
                result = mini_template.render(parent_vars)
                # Mark this as coming from a template expression so it gets escaped
                return _EscapableValue(result)
            except Exception:
                # If template processing fails, return the original value
                # This maintains compatibility with literal strings that might contain { }
                return value

        return value

    def _flatten_jinja_context(self, context: Any) -> Dict[str, Any]:
        """Flatten Jinja2 context similar to Django's context.flatten().

        Django's context.flatten() merges all context dictionaries into a single dict,
        with later dictionaries taking precedence. Jinja2's get_all() is similar but
        we want to ensure consistent behavior.
        """
        if hasattr(context, "get_all"):
            # Standard Jinja2 context - get_all() already provides flattened view
            return dict(context.get_all())
        elif hasattr(context, "items"):
            # Dict-like object
            return dict(context.items())
        else:
            # Fallback for other context types
            return dict(context) if context else {}

    def _denormalize_attribute_name(self, name: str) -> str:
        """Convert normalized attribute names back to their original form.

        This reverses the normalization done in preprocessing:
        - _at_click -> @click
        - _bind_class -> :class
        - v_on_click -> v-on:click
        - x_on_click_stop -> x-on:click.stop
        - inner_class -> inner.class
        """
        # Handle @click attributes
        if name.startswith("_at_"):
            return "@" + name[4:].replace("_", ".")

        # Handle :bind attributes
        if name.startswith("_bind_"):
            return ":" + name[6:].replace("_", ".")

        # Handle v-on:, v-model, etc.
        if name.startswith("v_"):
            # v_on_click_stop -> v-on:click.stop
            parts = name.split("_")
            if len(parts) >= 3 and parts[1] in (
                "on",
                "bind",
                "model",
                "show",
                "if",
                "for",
            ):
                directive = f"v-{parts[1]}"
                if parts[1] in ("on", "bind") and len(parts) >= 3:
                    # v-on:click or v-bind:class
                    event_or_prop = parts[2]
                    modifiers = ".".join(parts[3:]) if len(parts) > 3 else ""
                    result = f"{directive}:{event_or_prop}"
                    if modifiers:
                        result += f".{modifiers}"
                    return result
                else:
                    # v-model, v-show, etc.
                    suffix = "_".join(parts[2:]) if len(parts) > 2 else ""
                    result = directive
                    if suffix:
                        result += f".{suffix.replace('_', '.')}"
                    return result

        # Handle x-on:, x-data, etc. (Alpine.js)
        if name.startswith("x_"):
            parts = name.split("_")
            if len(parts) >= 3 and parts[1] in (
                "on",
                "data",
                "show",
                "if",
                "for",
                "text",
                "html",
            ):
                directive = f"x-{parts[1]}"
                if parts[1] == "on" and len(parts) >= 3:
                    # x-on:click
                    event = parts[2]
                    modifiers = ".".join(parts[3:]) if len(parts) > 3 else ""
                    result = f"{directive}:{event}"
                    if modifiers:
                        result += f".{modifiers}"
                    return result
                else:
                    # x-data, x-show, etc.
                    suffix = "_".join(parts[2:]) if len(parts) > 2 else ""
                    result = directive
                    if suffix:
                        result += f".{suffix.replace('_', '.')}"
                    return result

        # Handle nested attributes with @ (inner_at_click -> inner.@click)
        if "_at_" in name and not name.startswith("_at_"):
            return name.replace("_at_", ".@").replace("_", ".")

        # Handle nested attributes (inner_class -> inner.class, data_role -> data.role)
        if "_" in name and not (
            name.startswith("v_") or name.startswith("x_") or name.startswith("_")
        ):
            # Convert underscores to dots for nested attributes
            return name.replace("_", ".")

        # Handle regular kebab-case attributes
        if "_" in name:
            return name.replace("_", "-")

        return name


__all__ = ["IncludeContentsExtension"]
