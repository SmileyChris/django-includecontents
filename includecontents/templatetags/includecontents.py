import re
from collections import abc
from typing import TYPE_CHECKING, Any, Dict, Iterable, NoReturn, Optional, cast

from django import template
from django.conf import settings
from django.template import TemplateDoesNotExist, TemplateSyntaxError
from django.template.base import FilterExpression, Node, NodeList, Parser, TokenType
from django.template.context import Context
from django.template.defaulttags import TemplateIfParser
from django.template.loader_tags import IncludeNode, construct_relative_path, do_include
from django.utils.html import conditional_escape
from django.utils.safestring import mark_safe
from django.utils.text import smart_split

from includecontents.django.base import Template
from includecontents.shared.attrs import BaseAttrs
from includecontents.shared.context import CapturedContents, ComponentContext
from includecontents.shared.enums import (
    build_enum_flag_key,
    normalize_enum_values,
    suggest_enum_value,
)
from includecontents.shared.props import PropDefinition

register = template.Library()


if TYPE_CHECKING:

    class ContextWithProcessors(Context):
        _processor_data: Dict[str, Any]
        _processors_index: int


class TemplateAttributeExpression:
    """
    A custom expression that evaluates template syntax in attribute values.
    This allows mixed content like 'class="btn {{ variant }}"' to work correctly.
    """

    def __init__(self, template_string):
        self.template_string = template_string
        self._template = None

    def resolve(self, context):
        if self._template is None:
            # Compile the template once and cache it
            self._template = Template(self.template_string)
        return self._template.render(context)


def is_pure_variable_expression(value):
    """
    Check if a value is a pure variable expression like "{{ variable }}"
    with no other content. Returns the variable expression if true, None otherwise.
    """
    if not value:
        return None

    stripped = value.strip()
    if stripped.startswith("{{") and stripped.endswith("}}"):
        return stripped[2:-2].strip()
    return None


@register.filter(name="not")
def not_filter(value):
    """Template filter to negate a boolean value."""
    return not value


@register.tag
def includecontents(parser, token):
    """
    An extension of the ``{% include %}`` tag which loads a template and
    renders it with the current context. It accepts all the standard
    include tag arguments.

    The contents of this block tag is made available as a ``contents``
    variable in the context of the included template.

    Use ``{% contents some_name %}`` to use named areas which are
    available as ``contents.some_name`` in the context of the included
    template.

    Example::

        {% includecontents "includes/dialog.html" with dismissable=False %}
        Default contents lives outside a named area.
        {% contents title %}
            The contents of the named area called &quot;title&quot;.
        {% endcontents %}
        Default contents can live both before and after named areas at the same time.
        {% endincludecontents %}

    Included Template:

        <div class="dialog"{% if dismissable %} data-dismissable{% endif %}>
            {% if contents.title %}
                <h3>{{ contents.title }}</h3>
            {% endif %}
            <section>
            {{ contents }}
            </section>
            <button>{{ contents.save|default:"Save" %}</button>
            {% if "note" in contents %}
                {% if contents.note %}
                    <small>{{ contents.note }}</small>
                {% endif %}
            {% else %}
                <small>Default note only shown if named area wasn't provided.</small>
            {% endif %}
        </div>
    """
    # Store the original token contents for checking template syntax
    original_contents = token.contents

    # Remove template {{ }} only for non-quoted contexts
    # This regex only removes {{ }} when they're not inside quotes
    token.contents = re.sub(r"(['\"]?)\{\{ *(.*?) *\}\}\1", r"\2", token.contents)
    bits = token.split_contents()
    # If this was an HTML tag, it's second element is the tag name prefixed with an
    # underscore (and ending with a slash if it's self-closing).
    if len(bits) >= 2 and bits[1].startswith("_"):
        token_name = f"<{bits[1][1:]}>"
        # Rewrite the token name on the command stack for better error messages.
        parser.command_stack[-1] = (token_name,) + parser.command_stack[-1][1:]
        # Replace the token contents to use the rewritten token name.
        bits[1] = token_name
        del bits[0]
        # Split out nested attributes (those with a dot in the name).
        new_bits = []
        advanced_attrs = {}

        # Parse the original token to find attributes with template syntax
        original_bits = list(smart_split(original_contents))
        if len(original_bits) >= 2 and original_bits[1].startswith("_"):
            original_bits = original_bits[2:]  # Skip includecontents and tag name

        # Create a mapping of processed bits to original bits for template detection
        bit_to_original = {}
        for orig_bit in original_bits:
            # Strip {{ }} to match processed version
            processed = re.sub(r"(['\"]?)\{\{ *(.*?) *\}\}\1", r"\2", orig_bit)
            if processed in bits:
                bit_to_original[processed] = orig_bit

        for i, bit in enumerate(bits):
            if i < 3:
                new_bits.append(bit)
            elif bit.startswith("..."):
                # Handle spread syntax - strip the ... prefix
                spread_value = bit[3:]
                advanced_attrs["..."] = parser.compile_filter(spread_value)
            elif (
                bit.startswith("@")
                or (bit.startswith(":") and not bit.startswith("class:"))
                or bit.startswith("v-")
                or bit.startswith("x-")
            ):
                # JavaScript framework attributes (Vue, Alpine.js) can't be handled by the standard include.
                # This includes: @ (Vue events), : (Vue/Alpine bind), v- (Vue directives), x- (Alpine directives)
                # Note: class:something is NOT a JS framework attribute, it's our conditional class syntax
                if "=" in bit:
                    attr, value = bit.split("=", 1)
                else:
                    attr, value = bit, ""
                advanced_attrs[attr] = parser.compile_filter(value or "True")
            elif match := re.match(r"(^\w+\.[-.@:\w]+)(?:=(.+))?$", bit):
                # Nested attrs can't be handled by the standard include tag.
                attr, value = match.groups()
                advanced_attrs[attr] = parser.compile_filter(value or "True")
            elif "-" in bit or ":" in bit:
                # Attributes with a dash or colon also can't be handled by the standard include.
                # This includes class:something for conditional classes
                if "=" in bit:
                    attr, value = bit.split("=", 1)
                    # Check if this attribute had template syntax in the original
                    original_bit = bit_to_original.get(bit, bit)
                    if original_bit and ("{{" in original_bit or "{%" in original_bit):
                        # Extract the original value with template syntax
                        if "=" in original_bit:
                            _, orig_value = original_bit.split("=", 1)
                            # Remove quotes if present
                            if (
                                orig_value.startswith('"') and orig_value.endswith('"')
                            ) or (
                                orig_value.startswith("'") and orig_value.endswith("'")
                            ):
                                orig_value = orig_value[1:-1]
                            # Check if this is a pure variable expression
                            if var_expr := is_pure_variable_expression(orig_value):
                                # Use FilterExpression to preserve the actual object
                                advanced_attrs[attr] = parser.compile_filter(var_expr)
                            else:
                                # Use TemplateAttributeExpression for mixed content
                                advanced_attrs[attr] = TemplateAttributeExpression(
                                    orig_value
                                )
                        else:
                            advanced_attrs[attr] = parser.compile_filter(
                                value or "True"
                            )
                    else:
                        advanced_attrs[attr] = parser.compile_filter(value or "True")
                else:
                    attr, value = bit, ""
                    advanced_attrs[attr] = parser.compile_filter(value or "True")
            elif match := re.match(r"^{ *(\w+) *}$", bit):
                # Shorthand, e.g. {attr} is equivalent to attr=attr.
                attr = match.group(1)
                advanced_attrs[attr] = parser.compile_filter(attr)
            elif match := re.match(r"^(\w+)={(\w+)}$", bit):
                # Old style template variable syntax: title={myTitle}
                attr, var = match.groups()
                advanced_attrs[attr] = parser.compile_filter(var)
            else:
                # Check if this attribute had template syntax in the original
                original_bit = bit_to_original.get(bit, bit)
                if (
                    original_bit
                    and "=" in original_bit
                    and ("{{" in original_bit or "{%" in original_bit)
                ):
                    # This is a regular attribute with template syntax
                    attr, orig_value = original_bit.split("=", 1)
                    # Remove quotes if present
                    if (orig_value.startswith('"') and orig_value.endswith('"')) or (
                        orig_value.startswith("'") and orig_value.endswith("'")
                    ):
                        orig_value = orig_value[1:-1]
                    # Check if this is a pure variable expression
                    if var_expr := is_pure_variable_expression(orig_value):
                        # Use FilterExpression to preserve the actual object
                        advanced_attrs[attr] = parser.compile_filter(var_expr)
                    else:
                        # Use TemplateAttributeExpression for mixed content
                        advanced_attrs[attr] = TemplateAttributeExpression(orig_value)
                else:
                    # In tag mode, attributes without a value are treated as boolean flags.
                    if "=" not in bit:
                        bit = f"{bit}=True"
                    new_bits.append(bit)
        if new_bits and new_bits[-1] == "with":
            new_bits = new_bits[:-1]
        token.contents = " ".join(new_bits)
    else:
        token_name = bits[0]
        advanced_attrs = {}
    if len(bits) < 2:
        raise TemplateSyntaxError(
            f"{token_name} tag takes at least one argument: the name of the template"
        )
    nodelist, named_nodelists = get_contents_nodelists(parser, token_name)
    include_node = do_include(parser, token)
    include_node.origin = parser.origin

    return IncludeContentsNode(
        token_name=token_name,
        advanced_attrs=advanced_attrs,
        include_node=include_node,
        nodelist=nodelist,
        named_nodelists=named_nodelists,
    )


class RenderedContents(abc.Mapping):
    """Wrapper providing mapping semantics for captured contents."""

    def __init__(
        self, context: Context, nodelist: NodeList, named_nodelists: Dict[str, NodeList]
    ) -> None:
        default = self._render_block(nodelist, context)
        named = {
            key: self._render_block(named_nodelist, context)
            for key, named_nodelist in named_nodelists.items()
        }
        self._captured = CapturedContents(default, named)

    @staticmethod
    def _render_block(nodelist: NodeList, context: Context) -> str:
        with context.push():
            rendered = nodelist.render(context)
        if not rendered.strip():
            rendered = ""
        return mark_safe(rendered)

    def __str__(self) -> str:
        return str(self._captured)

    def __getitem__(self, key: str) -> Any:
        return self._captured._named[key]

    def __iter__(self) -> Iterable[str]:
        return iter(self._captured.keys())

    def __len__(self) -> int:
        return len(str(self._captured))

    def __getattr__(self, name: str) -> Any:
        return getattr(self._captured, name)

    def __contains__(self, name: str) -> bool:
        return name in self._captured

    def get(self, name: Optional[str], default: str = "") -> str:
        return self._captured.get(name, default)

    def keys(self) -> Iterable[str]:
        return self._captured.keys()

    def items(self) -> Iterable[tuple[str, str]]:
        return self._captured.items()


class IncludeContentsNode(template.Node):
    def __init__(
        self,
        token_name,
        advanced_attrs,
        include_node,
        nodelist,
        named_nodelists,
    ) -> None:
        self.token_name = token_name
        self.advanced_attrs = advanced_attrs
        self.include_node: IncludeNode = include_node
        self.nodelist = nodelist
        self.named_nodelists = named_nodelists

        self.is_component = token_name.startswith("<")

        isolated_context = True if self.is_component else include_node.isolated_context
        include_node.isolated_context = False
        self.isolated_context = isolated_context

    def render(self, context: Context) -> str:
        component_props: Optional[Dict[str, "PropDefinition"]] = None
        prop_values: Dict[str, Any] = {}
        attrs_obj: Optional["Attrs"] = None

        if self.is_component:
            try:
                template = self.get_component_template(context)
            except TemplateDoesNotExist as e:
                self._raise_enhanced_template_error(e)
            component_props = self.get_component_props(template)
            prop_values, attrs_obj = self._resolve_component_bindings(
                context, component_props
            )

        new_context = context.new() if self.isolated_context else context

        processor_data: Dict[str, Any] = {}
        component_scope: Optional[Dict[str, Any]] = None

        inherit_parent_values = False
        if self.is_component and self.isolated_context:
            processor_data = self._collect_processor_data(context)
            parent_vars = context.flatten()
            scope_values = (
                {**processor_data, **prop_values} if processor_data else prop_values
            )
            inherit_parent_values = bool(processor_data.get("request"))
            component_scope = ComponentContext.create_isolated(
                parent_vars,
                scope_values,
                inherit_parent=inherit_parent_values,
            )

        with new_context.push():
            if self.is_component:
                if component_scope is not None:
                    new_context.update(component_scope)
                    if processor_data:
                        new_context = cast("ContextWithProcessors", new_context)
                        new_context._processor_data = processor_data
                else:
                    new_context.update(prop_values)

                if attrs_obj is not None:
                    new_context["attrs"] = attrs_obj

            render_context = new_context if inherit_parent_values else context
            new_context["contents"] = RenderedContents(
                context=render_context,
                nodelist=self.nodelist,
                named_nodelists=self.named_nodelists,
            )

            rendered = self._render_include(new_context)
            if self.is_component:
                rendered = rendered.strip()
        return rendered

    def _render_include(self, render_context: Context) -> str:
        if not self.is_component:
            return self.include_node.render(render_context)
        extra_context = self.include_node.extra_context
        self.include_node.extra_context = {}
        try:
            return self.include_node.render(render_context)
        except TemplateDoesNotExist as e:
            # Enhance error message for component templates
            self._raise_enhanced_template_error(e)
        finally:
            self.include_node.extra_context = extra_context

    def _collect_processor_data(self, context: Context) -> Dict[str, Any]:
        processor_data: Dict[str, Any] = {}
        processors_index = getattr(context, "_processors_index", None)
        if processors_index is not None and hasattr(context, "dicts"):
            processor_data = context.dicts[processors_index].copy()
        elif hasattr(context, "_processor_data"):
            processor_data = cast(
                "ContextWithProcessors", context
            )._processor_data.copy()

        request = context.get("request")
        if request is None:
            request = getattr(context, "request", None)
        should_run_processors = not processor_data

        if request is not None:
            processor_data.setdefault("request", request)

        manual_csrf = None
        if hasattr(context, "dicts"):
            for mapping in reversed(context.dicts):
                if "csrf_token" in mapping:
                    manual_csrf = mapping["csrf_token"]
                    break

        if manual_csrf is not None:
            processor_data["csrf_token"] = manual_csrf
            if request is not None and isinstance(manual_csrf, str):
                if hasattr(request, "META"):
                    request.META["CSRF_COOKIE"] = manual_csrf
                if hasattr(request, "COOKIES"):
                    request.COOKIES[settings.CSRF_COOKIE_NAME] = manual_csrf
        if should_run_processors and request is not None:
            engine = getattr(getattr(context, "template", None), "engine", None)
            processors = getattr(engine, "template_context_processors", None)
            if processors:
                for processor in processors:
                    if (
                        manual_csrf is not None
                        and getattr(processor, "__name__", "") == "csrf"
                        and getattr(processor, "__module__", "").endswith(
                            "context_processors"
                        )
                    ):
                        continue
                    try:
                        processor_data.update(processor(request))
                    except Exception:  # pragma: no cover - defensive
                        continue

        if processor_data and not hasattr(context, "_processor_data"):
            context = cast("ContextWithProcessors", context)
            context._processor_data = processor_data.copy()

        csrf_token = context.get("csrf_token")
        if csrf_token is not None:
            processor_data.setdefault("csrf_token", csrf_token)

        return processor_data

    def _resolve_component_bindings(
        self,
        context: Context,
        component_props: Optional[Dict[str, "PropDefinition"]],
    ) -> tuple[Dict[str, Any], Optional["Attrs"]]:
        attrs_sequence = list(self.all_attrs())
        spread_attrs = self._resolve_spread(context, attrs_sequence)

        if component_props is None:
            prop_values: Dict[str, Any] = {}
            for key, value_expr in attrs_sequence:
                if key == "...":
                    continue
                if "." in key or ":" in key:
                    raise TemplateSyntaxError(
                        f"Advanced attribute {key!r} only allowed if component template"
                        " defines props"
                    )
                prop_values[key] = value_expr.resolve(context)  # type: ignore
            return prop_values, None

        prop_values = {}
        provided_props: set[str] = set()
        undefined_attrs = Attrs()

        for key, value_expr in attrs_sequence:
            if key == "...":
                continue
            resolved_value = value_expr.resolve(context)  # type: ignore
            prop_def = component_props.get(key)
            if prop_def is not None:
                provided_props.add(key)
                prop_values[key] = resolved_value
                if prop_def.is_enum():
                    allowed_values = prop_def.enum_values or ()
                    for enum_value in normalize_enum_values(resolved_value):
                        if enum_value not in allowed_values:
                            allowed = ", ".join(repr(v) for v in allowed_values)
                            suggestion = suggest_enum_value(enum_value, allowed_values)
                            suggestion_text = (
                                f" Did you mean {suggestion!r}?" if suggestion else ""
                            )

                            # Create a helpful example
                            first_value = (
                                allowed_values[0] if allowed_values else "value"
                            )
                            component_name = self.token_name.replace("<", "").replace(
                                ">", ""
                            )
                            example = f'<{component_name} {key}="{first_value}">'

                            raise TemplateSyntaxError(
                                f'Invalid value "{enum_value}" for attribute "{key}" '
                                f"in {self.token_name}. Allowed values: {allowed}.{suggestion_text}\n"
                                f"Example: {example}"
                            )
                        flag_key = build_enum_flag_key(key, enum_value)
                        if flag_key:
                            prop_values[flag_key] = True
            else:
                undefined_attrs[key] = resolved_value

        if isinstance(spread_attrs, Attrs):
            for key, value in spread_attrs.all_attrs():
                if key not in undefined_attrs:
                    undefined_attrs[key] = value

        for name, definition in component_props.items():
            if name in provided_props:
                continue
            if definition.is_enum():
                if definition.required:
                    raise TemplateSyntaxError(
                        f'Missing required attribute "{name}" in {self.token_name}'
                    )
                continue
            if definition.required:
                raise TemplateSyntaxError(
                    f'Missing required attribute "{name}" in {self.token_name}'
                )
            prop_values[name] = definition.clone_default()

        return prop_values, undefined_attrs

    @staticmethod
    def _resolve_spread(
        context: Context, attrs_sequence: Iterable[tuple[str, Any]]
    ) -> Any:
        for key, value_expr in attrs_sequence:
            if key == "...":
                return value_expr.resolve(context)
        return None

    def _raise_enhanced_template_error(
        self, original_error: TemplateDoesNotExist
    ) -> NoReturn:
        """Raise an enhanced TemplateDoesNotExist error with helpful debugging info."""
        template_name = original_error.args[0] if original_error.args else "unknown"

        # Extract component name from token
        component_name = self.token_name.replace("<include:", "").replace(">", "")

        # Create helpful suggestions
        suggestions = []

        # Suggest common naming conventions
        if not template_name.startswith("components/"):
            suggestions.append(
                f"Create template: templates/components/{component_name}.html"
            )
        else:
            suggestions.append(f"Create template: templates/{template_name}")

        # Suggest checking template directories
        suggestions.append(
            "Check TEMPLATES['DIRS'] setting includes your template directory"
        )

        # Suggest checking app structure
        if "components/" in template_name:
            suggestions.append(
                "For app-based components: create template in <app>/templates/components/"
            )

        # Create enhanced error message
        message_parts = [
            f"Component template not found: {self.token_name}",
            f"Looked for: {template_name}",
            "",
            "Suggestions:",
        ]

        for i, suggestion in enumerate(suggestions, 1):
            message_parts.append(f"  {i}. {suggestion}")

        if hasattr(original_error, "tried") and original_error.tried:
            message_parts.extend(
                [
                    "",
                    "Template loader tried:",
                ]
            )
            for origin, reason in original_error.tried:
                message_parts.append(f"  - {origin} ({reason})")

        enhanced_message = "\n".join(message_parts)

        # Raise new error with enhanced message but preserve original exception chain
        raise TemplateDoesNotExist(
            enhanced_message, tried=getattr(original_error, "tried", [])
        ) from original_error

    def all_attrs(self):
        for key, value in self.include_node.extra_context.items():
            yield key, value
        for key, value in self.advanced_attrs.items():
            yield key, value

    def get_component_props(
        self, template: Template
    ) -> Dict[str, PropDefinition] | None:
        resolver = getattr(template, "get_component_prop_definitions", None)
        if callable(resolver):
            return cast(Dict[str, PropDefinition] | None, resolver())
        return None

    def get_component_template(self, context) -> Template:
        template = self.include_node.template.resolve(context)
        # Does this quack like a Template?
        if not callable(getattr(template, "render", None)):
            # If not, try the cache and select_template().
            template_name = template or ()
            if isinstance(template_name, str):
                template_name = (
                    construct_relative_path(
                        self.origin.template_name,  # type: ignore
                        template_name,
                    ),
                )
            else:
                template_name = tuple(template_name)
            # Use the same cache as the include node to avoid duplicate template loads.
            cache = context.render_context.dicts[0].setdefault(self.include_node, {})
            template = cache.get(template_name)
            if template is None:
                template = context.template.engine.select_template(template_name)
                cache[template_name] = template
        # Use the base.Template of a backends.django.Template.
        elif hasattr(template, "template"):
            template = template.template
        return template

    @staticmethod
    def _normalize_enum_values(value: Any) -> list[str]:
        return normalize_enum_values(value)

    @staticmethod
    def _build_enum_flag_key(prop_name: str, enum_value: str) -> Optional[str]:
        return build_enum_flag_key(prop_name, enum_value)

    @staticmethod
    def _suggest_closest_enum_value(
        invalid_value: str, allowed_values: tuple[str, ...]
    ) -> Optional[str]:
        return suggest_enum_value(invalid_value, allowed_values)


def get_contents_nodelists(
    parser: Parser, token_name: str
) -> tuple[NodeList, dict[str, NodeList]]:
    if token_name.endswith("/>"):
        return NodeList(), {}
    end_tag = (
        f"</{token_name[1:]}" if token_name.startswith("<") else f"end{token_name}"
    )
    named_nodelists = {}
    default = []
    nesting_level = 0  # Track nesting level for proper scoping

    while parser.tokens:
        token = parser.next_token()
        if token.token_type != TokenType.BLOCK:
            default.append(token)
            continue
        bits = token.split_contents()
        tag_name = bits[0]

        # Check if this is a nested includecontents tag
        if tag_name == "includecontents":
            # For includecontents tags, check the second element to see if it's self-closing
            if len(bits) >= 2 and bits[1].startswith("_") and bits[1].endswith("/"):
                # Self-closing tag, don't increment nesting
                pass
            else:
                nesting_level += 1
            default.append(token)
            continue
        elif tag_name.startswith("<include:"):
            # This case shouldn't happen as these are converted to includecontents
            if not tag_name.endswith("/>"):
                nesting_level += 1
            default.append(token)
            continue
        elif tag_name.startswith("</include:") or tag_name.startswith("end"):
            # Check if this is the end of a nested includecontents
            if nesting_level > 0 and (
                tag_name.startswith("</include:") or tag_name == "endincludecontents"
            ):
                nesting_level -= 1
                default.append(token)
                continue

        # Only process contents tags that are at our nesting level (nesting_level == 0)
        if tag_name == "contents" and nesting_level == 0:
            if len(bits) < 2:
                raise TemplateSyntaxError(
                    "Unnamed {tag_name!r} tag within {token_name}" % tag_name
                )
            if len(bits) > 2:
                raise TemplateSyntaxError(f"Invalid {tag_name!r} tag format")
            content_name = bits[1]
            if content_name in named_nodelists:
                raise TemplateSyntaxError(
                    f"Duplicate name for {tag_name!r} tag: {content_name!r}"
                )
            named_nodelists[content_name] = parser.parse((f"end{tag_name}",))
            parser.delete_first_token()
            continue
        elif (
            tag_name == end_tag
            or (
                tag_name.startswith("</include:")
                and end_tag.startswith("</include:")
                and tag_name == end_tag[:-1]
            )
        ) and nesting_level == 0:
            default.append(token)
            for default_token in reversed(default):
                parser.prepend_token(default_token)
            nodelist = parser.parse((end_tag,))
            parser.delete_first_token()
            return nodelist, named_nodelists
        default.append(token)
    parser.unclosed_block_tag((end_tag,))
    raise Exception


NO_VALUE = object()


class Attrs(BaseAttrs):
    def __init__(self) -> None:
        super().__init__()

    def __str__(self) -> str:
        """Render attributes with Django-specific HTML escaping and mark_safe."""
        return mark_safe(super().__str__())

    def _render_attr(self, key: str, value: Any) -> str:
        """Render a single attribute with Django's conditional HTML escaping."""
        return f'{key}="{conditional_escape(value)}"'

    @staticmethod
    def _normalize_enum_values(value: Any) -> list[str]:
        return normalize_enum_values(value)

    @staticmethod
    def _build_enum_flag_key(prop_name: str, enum_value: str) -> Optional[str]:
        return build_enum_flag_key(prop_name, enum_value)

    @staticmethod
    def _suggest_closest_enum_value(
        invalid_value: str, allowed_values: tuple[str, ...]
    ) -> Optional[str]:
        return suggest_enum_value(invalid_value, allowed_values)


@register.tag
def attrs(parser: Parser, token):
    """
    Render a component's undefined attrs as a string of HTML attributes with fallbacks.

    For example::

        {% attrs type="text" %}

    The ``class`` attribute can be extended in a specific way:

    ``{% attrs class:field=value %}`` if value is truthy (or if no `=value` is used),
    will ensure the `field` class always part of the ``class`` attribute.

    To render a nested set of attributes, add the name of the nested group as a dotted
    suffix to the tag::

        {% attrs.nested required %}
    """
    bits = smart_split(token.contents)
    tag_name = next(bits)
    if "." in tag_name:
        sub_key = tag_name.split(".", 1)[1]
    else:
        sub_key = None

    fallbacks = {}
    for bit in bits:
        match = re.match(r"^([\w.-]+(?::[-\w]+)?)(?:=(.+?))?$", bit)
        if not match:
            raise TemplateSyntaxError(f"Invalid {tag_name!r} tag attribute: {bit!r}")
        key, value = match.groups()
        fallbacks[key] = parser.compile_filter(value) if value else NO_VALUE
    return AttrsNode(sub_key, fallbacks)


class AttrsNode(template.Node):
    def __init__(self, sub_key, fallbacks):
        self.sub_key = sub_key
        self.fallbacks = fallbacks

    def render(self, context):
        context_attrs = context.get("attrs")
        if self.sub_key:
            context_attrs = getattr(context_attrs, self.sub_key, None)
        if not isinstance(context_attrs, Attrs):
            raise TemplateSyntaxError(
                "The attrs tag requires an attrs variable in the context"
            )

        # Build kwargs dict from resolved fallbacks
        kwargs = {}
        for key, value in self.fallbacks.items():
            if isinstance(value, FilterExpression):
                kwargs[key] = value.resolve(context)  # type: ignore
            elif value is NO_VALUE:  # Boolean attribute
                kwargs[key] = True
            else:
                kwargs[key] = value

        # Call the attrs object with kwargs - this now uses the new callable interface
        return str(context_attrs(**kwargs))


class ContentsObject:
    """Object that provides both string representation and attribute access for contents blocks."""

    def __init__(self, contents_dict):
        self._contents = contents_dict
        self.default = contents_dict.get(None, "")

    def __str__(self):
        return str(self.default)

    def __getattr__(self, name):
        return self._contents.get(name, "")

    def __bool__(self):
        return bool(self.default)

    def __contains__(self, name):
        return name in self._contents


class WrapperSpec:
    """Represents a wrapper specification - either shorthand or full template."""

    def __init__(self, tag_name=None, attrs=None, nodelist=None):
        self.tag_name = tag_name  # For shorthand syntax
        self.attrs = attrs or {}  # For shorthand syntax
        self.nodelist = nodelist  # For full template syntax
        self.is_shorthand = tag_name is not None


class WrapIfNode(Node):
    def __init__(self, conditions_and_wrappers, default_wrapper, contents_nodelists):
        self.conditions_and_wrappers = (
            conditions_and_wrappers  # [(condition, wrapper_spec), ...]
        )
        self.default_wrapper = default_wrapper  # For wrapelse
        self.contents_nodelists = (
            contents_nodelists  # {'default': nodelist, 'header': nodelist, ...}
        )

    def get_nodes_by_type(self, nodetype):
        """Collect nodes of given type from all contents nodelists."""
        nodes = []
        # Collect nodes from all contents nodelists
        for nodelist in self.contents_nodelists.values():
            nodes.extend(nodelist.get_nodes_by_type(nodetype))
        return nodes

    def render(self, context):
        # First, render all contents blocks
        contents_dict = {}
        for name, nodelist in self.contents_nodelists.items():
            rendered = nodelist.render(context)
            if name == "default":
                contents_dict[None] = mark_safe(rendered)
            else:
                contents_dict[name] = mark_safe(rendered)

        # Create a contents object that supports both dict access and default str()
        contents_obj = ContentsObject(contents_dict)

        # Store contents in context
        context.push()
        context["contents"] = contents_obj

        try:
            # Evaluate conditions in order
            for condition, wrapper_spec in self.conditions_and_wrappers:
                try:
                    match = condition.eval(context)
                except Exception:
                    match = False

                if match:
                    return self.apply_wrapper(contents_obj, wrapper_spec, context)

            # No conditions matched, use default wrapper if provided
            if self.default_wrapper:
                return self.apply_wrapper(contents_obj, self.default_wrapper, context)

            # No wrapper applies, return all contents
            # If we have multiple contents blocks, concatenate them
            if len(contents_dict) > 1:
                result_parts = []
                for name, content in contents_dict.items():
                    if content:  # Only include non-empty content
                        result_parts.append(content)
                return mark_safe("".join(result_parts))
            else:
                return contents_obj.default
        finally:
            context.pop()

    def apply_wrapper(self, contents_obj, wrapper_spec, context):
        if wrapper_spec.is_shorthand:
            # Build HTML tag with attributes
            attrs_str = self.build_attrs_string(wrapper_spec.attrs, context)
            if attrs_str:
                return mark_safe(
                    f"<{wrapper_spec.tag_name} {attrs_str}>{contents_obj.default}</{wrapper_spec.tag_name}>"
                )
            else:
                return mark_safe(
                    f"<{wrapper_spec.tag_name}>{contents_obj.default}</{wrapper_spec.tag_name}>"
                )
        else:
            # For full template syntax, render the wrapper template
            # The wrapper template will have access to the contents via context
            return wrapper_spec.nodelist.render(context)

    def build_attrs_string(self, attrs, context):
        """Build HTML attributes string from attrs dict."""
        rendered_attrs = []
        for key, value in attrs.items():
            resolved = value.resolve(context)
            if resolved is True:
                rendered_attrs.append(key)
            elif resolved not in (False, None, ""):
                rendered_attrs.append(f'{key}="{conditional_escape(resolved)}"')
        return " ".join(rendered_attrs)


def parse_wrapper_shorthand(bits, parser):
    """Parse shorthand wrapper syntax: then "tag" attr=value..."""
    if not bits:
        raise TemplateSyntaxError("Expected tag name after 'then'")

    # First bit should be the tag name (possibly quoted)
    tag_name = bits[0]
    if tag_name.startswith(('"', "'")) and tag_name.endswith(tag_name[0]):
        tag_name = tag_name[1:-1]

    # Parse attributes
    attrs = {}
    for bit in bits[1:]:
        if "=" in bit:
            key, value = bit.split("=", 1)
            attrs[key] = parser.compile_filter(value)
        else:
            # Boolean attribute
            attrs[bit] = parser.compile_filter("True")

    return WrapperSpec(tag_name=tag_name, attrs=attrs)


def extract_contents_from_wrapper(nodelist):
    """Check if wrapper nodelist contains contents tags."""
    for node in nodelist:
        if isinstance(node, ContentsNode):
            return True
    return False


def parse_contents_from_full_syntax(wrapper_nodelist):
    """Parse contents blocks from the wrapper nodelist."""
    contents_blocks = {}

    # Walk through the wrapper nodelist recursively to find ContentsNode instances
    def extract_contents_nodes(nodes):
        for node in nodes:
            if isinstance(node, ContentsNode):
                name = node.name or "default"
                contents_blocks[name] = node.nodelist
            # Check if node has child nodelists
            if hasattr(node, "nodelist") and node.nodelist:
                extract_contents_nodes(node.nodelist)
            # Check for other nodelist attributes
            for attr in dir(node):
                if attr.startswith("nodelist_") and hasattr(node, attr):
                    child_nodelist = getattr(node, attr)
                    if isinstance(child_nodelist, NodeList):
                        extract_contents_nodes(child_nodelist)

    extract_contents_nodes(wrapper_nodelist)

    # If no contents blocks found, this means the wrapper doesn't use contents
    # In this case, we should have parsed the content separately
    if not contents_blocks:
        contents_blocks["default"] = NodeList()

    return contents_blocks


@register.tag("wrapif")
def do_wrapif(parser, token):
    """
    Conditionally wrap content with HTML elements.

    Basic syntax:
        {% wrapif condition %}
        <tag>{% contents %}content here{% endcontents %}</tag>
        {% endwrapif %}

    Shorthand syntax:
        {% wrapif condition then "tag" attr=value %}
          content
        {% endwrapif %}

    With else:
        {% wrapif condition then "a" href=url %}
        {% wrapelse "span" %}
          content
        {% endwrapif %}
    """
    bits = token.split_contents()[1:]

    if not bits:
        raise TemplateSyntaxError("wrapif tag requires at least one argument")

    # Determine if we're using shorthand or full syntax by looking ahead
    using_shorthand = "then" in bits

    # Parse all conditions and wrappers first
    conditions_and_wrappers = []

    # Parse first condition
    if using_shorthand:
        then_index = bits.index("then")
        condition_bits = bits[:then_index]
        wrapper_bits = bits[then_index + 1 :]

        condition = TemplateIfParser(parser, condition_bits).parse()
        wrapper = parse_wrapper_shorthand(wrapper_bits, parser)
    else:
        # Full template syntax
        condition = TemplateIfParser(parser, bits).parse()
        # We need to parse differently for full syntax
        # Save the current position
        parser.tokens[:]
        wrapper_nodelist = parser.parse(("wrapelif", "wrapelse", "endwrapif"))
        parser.tokens[:]

        # Extract the contents from the wrapper
        contents_info = extract_contents_from_wrapper(wrapper_nodelist)
        if contents_info:
            wrapper = WrapperSpec(nodelist=wrapper_nodelist)
        else:
            # No contents tags found, treat as simple wrapper
            wrapper = WrapperSpec(nodelist=wrapper_nodelist)

    conditions_and_wrappers.append((condition, wrapper))

    # Now we need to handle the content parsing differently for shorthand vs full syntax
    if using_shorthand:
        # For shorthand, parse through all conditions first, then get the content
        nodelist = parser.parse(("wrapelif", "wrapelse", "endwrapif"))

        # Process any wrapelif/wrapelse
        token = parser.next_token()

        while token.contents.startswith("wrapelif"):
            bits = token.split_contents()[1:]

            if "then" in bits:
                then_index = bits.index("then")
                condition_bits = bits[:then_index]
                wrapper_bits = bits[then_index + 1 :]

                condition = TemplateIfParser(parser, condition_bits).parse()
                wrapper = parse_wrapper_shorthand(wrapper_bits, parser)
            else:
                # Mixed syntax not allowed
                raise TemplateSyntaxError(
                    "Cannot mix shorthand and full syntax in wrapif"
                )

            conditions_and_wrappers.append((condition, wrapper))

            # Skip to next clause
            nodelist = parser.parse(("wrapelif", "wrapelse", "endwrapif"))
            token = parser.next_token()

        # Handle wrapelse
        default_wrapper = None
        if token.contents.startswith("wrapelse"):
            bits = token.split_contents()[1:]

            if bits:
                # Shorthand else
                default_wrapper = parse_wrapper_shorthand(bits, parser)
            else:
                # Mixed syntax not allowed
                raise TemplateSyntaxError(
                    "Cannot mix shorthand and full syntax in wrapif"
                )

            # Parse the final content
            nodelist = parser.parse(("endwrapif",))
            parser.delete_first_token()

        # For shorthand, the content is the last parsed nodelist
        contents_blocks = {"default": nodelist}
    else:
        # Full template syntax - need to extract contents from wrapper
        # The actual content needs to be parsed from within the wrapper templates
        # For now, we'll parse it as empty and handle it during rendering
        contents_blocks = parse_contents_from_full_syntax(wrapper_nodelist)

        token = parser.next_token()

        while token.contents.startswith("wrapelif"):
            bits = token.split_contents()[1:]

            if "then" in bits:
                # Mixed syntax not allowed
                raise TemplateSyntaxError(
                    "Cannot mix shorthand and full syntax in wrapif"
                )
            else:
                condition = TemplateIfParser(parser, bits).parse()
                nodelist = parser.parse(("wrapelif", "wrapelse", "endwrapif"))
                wrapper = WrapperSpec(nodelist=nodelist)

            conditions_and_wrappers.append((condition, wrapper))
            token = parser.next_token()

        # Handle wrapelse
        default_wrapper = None
        if token.contents.startswith("wrapelse"):
            bits = token.split_contents()[1:]

            if bits:
                # Mixed syntax not allowed
                raise TemplateSyntaxError(
                    "Cannot mix shorthand and full syntax in wrapif"
                )
            else:
                # Full template else
                nodelist = parser.parse(("endwrapif",))
                default_wrapper = WrapperSpec(nodelist=nodelist)

            parser.delete_first_token()

    return WrapIfNode(conditions_and_wrappers, default_wrapper, contents_blocks)


@register.tag("contents")
def do_contents(parser, token):
    """
    Used within {% wrapif %} blocks to mark content placement.

    Usage:
        {% contents %}content here{% endcontents %}
        {% contents name %}named content{% endcontents %}
    """
    bits = token.split_contents()
    if len(bits) > 2:
        raise TemplateSyntaxError(f"Invalid contents tag format: {token.contents}")

    name = bits[1] if len(bits) == 2 else None
    nodelist = parser.parse(("endcontents",))
    parser.delete_first_token()

    return ContentsNode(name, nodelist)


class ContentsNode(Node):
    """Node for contents blocks within wrapif."""

    def __init__(self, name, nodelist):
        self.name = name
        self.nodelist = nodelist

    def render(self, context):
        # Contents nodes are handled specially by WrapIfNode
        # If rendered directly, just return the content
        return self.nodelist.render(context)
