import re
from collections import abc
from collections.abc import MutableMapping
from contextlib import contextmanager
from typing import Any

from django import template
from django.template import TemplateSyntaxError, Variable
from django.template.base import FilterExpression, NodeList, Parser, TokenType
from django.template.context import Context
from django.template.loader_tags import construct_relative_path, do_include
from django.utils.html import conditional_escape
from django.utils.safestring import mark_safe
from django.utils.text import smart_split

from includecontents.django.base import Template

register = template.Library()

re_camel_case = re.compile(r"(?<=.)([A-Z])")


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
            new_context = context.new()
            if request := getattr(context, "request", None):
                new_context.request = request
            if csrf_token := context.get("csrf_token"):
                new_context["csrf_token"] = csrf_token
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
                    new_context[key] = value.resolve(context)
                else:
                    undefined_attrs[key] = value.resolve(context)

        if component_props is not None:
            new_context["attrs"] = undefined_attrs

            # Put default values in the new context.
            for key, value in component_props.items():
                if value:
                    if key in new_context:
                        continue
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

    while parser.tokens:
        token = parser.next_token()
        if token.token_type != TokenType.BLOCK:
            default.append(token)
            continue
        bits = token.split_contents()
        tag_name = bits[0]
        if tag_name == "contents":
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
        elif tag_name == end_tag:
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
        for key, parts in self._extended.items():
            parts = [key for key, value in parts.items() if value]
            if parts:
                extended[key] = parts
        for key, value in self._attrs.items():
            if key in extended:
                if value is True or not value:
                    value_parts = []
                else:
                    value_parts = str(value).split(" ")
                for part in extended[key]:
                    if part not in value_parts:
                        value_parts.append(part)
                value = " ".join(value_parts)
            yield key, value or None
        for key, parts in extended.items():
            if key not in self._attrs:
                yield key, " ".join(parts) or None

    def update(self, attrs):
        super().update(attrs)
        if isinstance(attrs, Attrs):
            for key, extended in attrs._extended.items():
                self._extended.setdefault(key, {}).update(extended)
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
