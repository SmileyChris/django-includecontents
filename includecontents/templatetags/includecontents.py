import re
from collections import abc
from collections.abc import MutableMapping
from contextlib import contextmanager
from typing import Any

from django import template
from django.template import TemplateSyntaxError, Variable
from django.template.base import FilterExpression, Node, NodeList, Parser, TokenType
from django.template.context import Context
from django.template.defaulttags import TemplateIfParser
from django.template.loader_tags import construct_relative_path, do_include
from django.utils.html import conditional_escape
from django.utils.safestring import mark_safe
from django.utils.text import smart_split

from includecontents.django.base import Template

register = template.Library()


@register.filter(name="not")
def not_filter(value):
    """Template filter to negate a boolean value."""
    return not value


re_camel_case = re.compile(r"(?<=.)([A-Z])")


class EnumVariable:
    """A variable that validates against a list of allowed values."""

    def __init__(self, allowed_values, required=True):
        self.allowed_values = allowed_values
        self.required = required

    def resolve(self, context):
        # This should not be called for enum validation
        # The actual value comes from the component usage
        return None


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
    # Remove template {{ }}.
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
        for i, bit in enumerate(bits):
            if i < 3:
                new_bits.append(bit)
            elif match := re.match(r"(^\w+[.:][-.\w:]+)(?:=(.+))?$", bit):
                # Nested attrs can't be handled by the standard include tag.
                attr, value = match.groups()
                advanced_attrs[attr] = parser.compile_filter(value or "True")
            elif "-" in bit:
                # Attributes with a dash also can't be handled by the standard include.
                if "=" in bit:
                    attr, value = bit.split("=", 1)
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
    def __init__(
        self, context: Context, nodelist: NodeList, named_nodelists: dict[str, NodeList]
    ):
        self.rendered_contents = self.render(nodelist, context)
        self.rendered_areas = {}
        for key, named_nodelist in named_nodelists.items():
            self.rendered_areas[key] = self.render(named_nodelist, context)

    @staticmethod
    def render(nodelist, context):
        with context.push():
            rendered = nodelist.render(context)
        if not rendered.strip():
            rendered = ""
        return mark_safe(rendered)

    def __str__(self):
        return self.rendered_contents

    def __getitem__(self, key):
        return self.rendered_areas[key]

    def __iter__(self):
        return iter(self.rendered_areas)

    def __len__(self):
        return len(self.rendered_contents)


class IncludeContentsNode(template.Node):
    def __init__(
        self,
        token_name,
        advanced_attrs,
        include_node,
        nodelist,
        named_nodelists,
    ):
        self.token_name = token_name
        self.advanced_attrs = advanced_attrs
        self.include_node = include_node
        self.nodelist = nodelist
        self.named_nodelists = named_nodelists

        self.is_component = token_name.startswith("<")

        # We'll handle the include_node context isolation ourselves.
        isolated_context = True if self.is_component else include_node.isolated_context
        include_node.isolated_context = False
        self.isolated_context = isolated_context

    def render(self, context):
        if self.isolated_context:
            # If we have a RequestContext with processor data, grab it before creating new context
            processor_data = {}
            processors_index = getattr(context, "_processors_index", None)
            if processors_index is not None and hasattr(context, "dicts"):
                # Get the already-computed processor values from Django's RequestContext
                processor_data = context.dicts[processors_index].copy()

            # Ensure request and csrf_token are available (if not already provided by processors)
            if request := context.get("request"):
                processor_data.setdefault("request", request)
            if csrf_token := context.get("csrf_token"):
                processor_data.setdefault("csrf_token", csrf_token)

            # Create new isolated context and inject all processor data at once
            new_context = context.new()
            new_context.update(processor_data)
        else:
            new_context = context
        with new_context.push():
            new_context["contents"] = RenderedContents(
                # Contents aren't rendered with isolation, hence the use of context
                # rather than new_context.
                context,
                nodelist=self.nodelist,
                named_nodelists=self.named_nodelists,
            )
            with self.set_component_attrs(context, new_context):
                rendered = self.include_node.render(new_context)
            if self.is_component:
                rendered = rendered.strip()
        return rendered

    @contextmanager
    def set_component_attrs(self, context: Context, new_context: Context):
        """
        Set the attributes of the component tag in the new context.

        Use as a context manager around rendering the include node so that when in
        component "props" mode, the non-listed attributes will be set as in the
        ``attrs`` variable rather than directly in the new context.
        """
        if not self.is_component:
            yield
            return
        template = self.get_component_template(context)
        component_props = self.get_component_props(template)
        if component_props is not None:
            undefined_attrs = Attrs()
        for key, value in self.all_attrs():
            if component_props is None:
                if "." in key or ":" in key:
                    raise TemplateSyntaxError(
                        f"Advanced attribute {key!r} only allowed if component template"
                        " defines props"
                    )
                new_context[key] = value.resolve(context)
            else:
                if key in component_props:
                    resolved_value = value.resolve(context)
                    prop_def = component_props[key]
                    # Validate enum values
                    if isinstance(prop_def, EnumVariable):
                        # Support multiple space-separated enum values
                        enum_values = resolved_value.split() if resolved_value else []

                        # Validate each value
                        for enum_value in enum_values:
                            if enum_value not in prop_def.allowed_values:
                                raise TemplateSyntaxError(
                                    f'Invalid value "{enum_value}" for attribute "{key}" in {self.token_name}. '
                                    f"Allowed values: {', '.join(repr(v) for v in prop_def.allowed_values)}"
                                )

                        # Set the original value as-is
                        new_context[key] = resolved_value

                        # Set boolean attributes for each enum value
                        # e.g., variant="primary icon" sets variantPrimary=True and variantIcon=True
                        for enum_value in enum_values:
                            if enum_value:  # Don't set True for empty string
                                # CamelCase version: variantPrimary or variantDarkMode (from dark-mode)
                                # Convert hyphens to camelCase
                                parts = enum_value.split("-")
                                camel_value = parts[0] + "".join(
                                    p.capitalize() for p in parts[1:]
                                )
                                camel_key = (
                                    key + camel_value[0].upper() + camel_value[1:]
                                )
                                new_context[camel_key] = True
                    else:
                        new_context[key] = resolved_value
                else:
                    undefined_attrs[key] = value.resolve(context)

        if component_props is not None:
            new_context["attrs"] = undefined_attrs

            # Put default values in the new context.
            for key, value in component_props.items():
                if value:
                    if key in new_context:
                        continue
                    # Check if it's a required enum that wasn't provided
                    if isinstance(value, EnumVariable) and value.required:
                        raise TemplateSyntaxError(
                            f'Missing required attribute "{key}" in {self.token_name}'
                        )
                    elif not isinstance(value, EnumVariable):
                        new_context[key] = value.resolve(context)

        # Don't use the extra context for the include tag if it's a component
        # since we've handled adding it to the new context ourselves.
        extra_context = self.include_node.extra_context
        self.include_node.extra_context = {}
        yield
        self.include_node.extra_context = extra_context

    def all_attrs(self):
        for key, value in self.include_node.extra_context.items():
            yield key, value
        for key, value in self.advanced_attrs.items():
            yield key, value

    def get_component_props(self, template):
        if not template.first_comment:
            return None
        if (
            template.first_comment.startswith("props ")
            or template.first_comment == "props"
        ):
            first_comment = template.first_comment[6:]
        elif (
            template.first_comment.startswith("def ") or template.first_comment == "def"
        ):
            first_comment = template.first_comment[4:]
        else:
            return None
        props = {}
        for bit in smart_split(first_comment.strip()):
            if match := re.match(r"^(\w+)(?:=(.+?))?,?$", bit):
                attr, value = match.groups()
                if value is None:
                    # Check both extra_context and advanced_attrs for required attributes
                    if (
                        attr not in self.include_node.extra_context
                        and attr not in self.advanced_attrs
                    ):
                        raise TemplateSyntaxError(
                            f'Missing required attribute "{attr}" in {self.token_name}'
                        )
                    props[attr] = None
                else:
                    # Check if value contains comma-separated values (enum) without spaces
                    if "," in value and " " not in value:
                        # Strip quotes if present
                        if (value.startswith('"') and value.endswith('"')) or (
                            value.startswith("'") and value.endswith("'")
                        ):
                            value = value[1:-1]
                        # Parse enum values
                        enum_values = value.split(",")
                        # First value empty means optional
                        required = bool(enum_values[0])
                        props[attr] = EnumVariable(enum_values, required)
                    else:
                        props[attr] = Variable(value)
        return props

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


class Attrs(MutableMapping):
    def __init__(self):
        self._attrs: dict[str, Any] = {}
        self._nested_attrs: dict[str, Attrs] = {}
        self._extended: dict[str, dict[str, bool]] = {}
        self._prepended: dict[str, dict[str, bool]] = {}

    def __getattr__(self, key):
        if key not in self._nested_attrs:
            raise AttributeError(key)
        return self._nested_attrs[key]

    def __getitem__(self, key):
        if key not in self._attrs:
            key = re_camel_case.sub(r"-\1", key).lower()
        return self._attrs[key]

    def __setitem__(self, key, value):
        if "." in key:
            nested_key, key = key.split(".", 1)
            nested_attrs = self._nested_attrs.setdefault(nested_key, Attrs())
            nested_attrs[key] = value
            return
        if ":" in key:
            key, extend = key.split(":", 1)
            extended = self._extended.setdefault(key, {})
            extended[extend] = value
            return
        if key == "class" and value.startswith("& "):
            extended = self._extended.setdefault(key, {})
            for bit in value[2:].split(" "):
                extended[bit] = True
            return
        if key == "class" and value.endswith(" &"):
            prepended = self._prepended.setdefault(key, {})
            for bit in value[:-2].strip().split(" "):
                if bit:
                    prepended[bit] = True
            return
        self._attrs[key] = value

    def __delitem__(self, key):
        del self._attrs[key]

    def __iter__(self):
        return iter(self._attrs)

    def __len__(self):
        return len(self._attrs)

    def __str__(self):
        return mark_safe(
            " ".join(
                (f'{key}="{conditional_escape(value)}"' if value is not True else key)
                for key, value in self.all_attrs()
                if value is not None
            )
        )

    def all_attrs(self):
        extended = {}
        prepended = {}

        # Collect extended and prepended values
        for key, parts in self._extended.items():
            parts = [key for key, value in parts.items() if value]
            if parts:
                extended[key] = parts

        for key, parts in self._prepended.items():
            parts = [key for key, value in parts.items() if value]
            if parts:
                prepended[key] = parts

        # Process all keys (from attrs, extended, and prepended)
        # Maintain order: attrs keys first, then any additional extended/prepended keys
        seen = set()

        for key in self._attrs:
            seen.add(key)
            value = self._attrs[key]
            # Handle class merging
            if key in extended or key in prepended:
                if value is True or not value:
                    value_parts = []
                else:
                    value_parts = str(value).split(" ")

                # Prepend parts come first
                if key in prepended:
                    value_parts = prepended[key] + [
                        p for p in value_parts if p not in prepended[key]
                    ]

                # Extended parts come last
                if key in extended:
                    for part in extended[key]:
                        if part not in value_parts:
                            value_parts.append(part)

                value = " ".join(value_parts) if value_parts else None

            yield key, value

        # Handle keys that only exist in extended/prepended
        for key in list(extended.keys()) + list(prepended.keys()):
            if key not in seen:
                seen.add(key)
                value_parts = prepended.get(key, []) + extended.get(key, [])
                value = " ".join(value_parts) if value_parts else None
                yield key, value

    def update(self, attrs):
        super().update(attrs)
        if isinstance(attrs, Attrs):
            for key, extended in attrs._extended.items():
                self._extended.setdefault(key, {}).update(extended)
            for key, prepended in attrs._prepended.items():
                self._prepended.setdefault(key, {}).update(prepended)
            for key, nested_attrs in attrs._nested_attrs.items():
                self._nested_attrs.setdefault(key, Attrs()).update(nested_attrs)


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
        match = re.match(r"^(\w+(?::[-\w]+)?)(?:=(.+?))?$", bit)
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
        if not isinstance(context_attrs, Attrs):
            raise TemplateSyntaxError(
                "The attrs tag requires an attrs variable in the context"
            )
        if self.sub_key:
            context_attrs = getattr(context_attrs, self.sub_key, None)
        attrs = Attrs()
        attrs.update(
            {
                key: (
                    value.resolve(context)  # type: ignore
                    if isinstance(value, FilterExpression)
                    else value
                )
                for key, value in self.fallbacks.items()
            }
        )
        if isinstance(context_attrs, Attrs):
            attrs.update(context_attrs)
        return str(attrs)


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
    child_nodelists = ("contents_nodelists",)

    def __init__(self, conditions_and_wrappers, default_wrapper, contents_nodelists):
        self.conditions_and_wrappers = (
            conditions_and_wrappers  # [(condition, wrapper_spec), ...]
        )
        self.default_wrapper = default_wrapper  # For wrapelse
        self.contents_nodelists = (
            contents_nodelists  # {'default': nodelist, 'header': nodelist, ...}
        )

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
        wrapper_start = parser.tokens[:]
        wrapper_nodelist = parser.parse(("wrapelif", "wrapelse", "endwrapif"))
        wrapper_end = parser.tokens[:]

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
