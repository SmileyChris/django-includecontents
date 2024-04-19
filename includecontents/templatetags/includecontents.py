import re
from collections import abc
from collections.abc import MutableMapping
from typing import Any

from django import template
from django.template import TemplateSyntaxError, Variable
from django.template.base import FilterExpression, NodeList, Parser, TokenType
from django.template.context import Context
from django.template.loader_tags import IncludeNode, construct_relative_path, do_include
from django.utils.html import escape
from django.utils.safestring import mark_safe
from django.utils.text import smart_split

from includecontents.base import Template

register = template.Library()

re_tag = re.compile(r"^includecontents _([A-Z]\w+)")


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
    bits = token.split_contents()
    # If this was an HTML tag, it's second element is the tag name prefixed with an
    # underscore.
    if len(bits) >= 2 and bits[1].startswith("_"):
        token_name = f"<{bits[1][1:]}>"
        # Rewrite the token name on the command stack for better error messages.
        parser.command_stack[-1] = (token_name,) + parser.command_stack[-1][1:]
        # Replace the token contents to use the rewritten token name.
        bits[1] = token_name
        del bits[0]
        # In tag mode, allow boolean attributes to be set without a value.
        for i, bit in enumerate(bits[3:], start=3):
            if "=" not in bit:
                bits[i] = f"{bit}=True"
        # Split out nested attributes (those with a dot in the name).
        new_bits = []
        nested_attrs = {}
        for bit in bits:
            if match := re.match(r"(^\w+[.:][-.\w:]+)(?:=(.+))?", bit):
                attr, value = match.groups()
                nested_attrs[attr] = parser.compile_filter(value or "True")
            else:
                new_bits.append(bit)
        bits = new_bits
        token.contents = " ".join(bits)
    else:
        token_name = bits[0]
        nested_attrs = {}
    if len(bits) < 2:
        raise TemplateSyntaxError(
            f"{token_name} tag takes at least one argument: the name of the template"
        )
    nodelist, named_nodelists = get_contents_nodelists(parser, token_name)
    include_node = do_include(parser, token)
    include_node.origin = parser.origin
    isolated_context = (
        False if token_name.startswith("<") else include_node.isolated_context
    )
    include_node.isolated_context = False
    return IncludeContentsNode(
        token_name=token_name,
        nested_attrs=nested_attrs,
        include_node=include_node,
        nodelist=nodelist,
        named_nodelists=named_nodelists,
        isolated_context=isolated_context,
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
        nested_attrs,
        include_node,
        nodelist,
        named_nodelists,
        isolated_context,
    ):
        self.token_name = token_name
        self.nested_attrs = nested_attrs
        self.include_node = include_node
        self.nodelist = nodelist
        self.named_nodelists = named_nodelists
        self.isolated_context = isolated_context

    def render(self, context):
        new_context = context.new() if self.isolated_context else context
        with new_context.push():
            new_context["contents"] = RenderedContents(
                # Contents aren't rendered with isolation, hence the use of context
                # rather than new_context.
                context,
                nodelist=self.nodelist,
                named_nodelists=self.named_nodelists,
            )
            if self.set_component_attrs(context, new_context):
                # Don't use the extra context for the include tag if it's a component
                # with defined props.
                node = IncludeNode(self.include_node.template)
                node.origin = self.origin
                rendered = node.render(new_context)
            else:
                rendered = self.include_node.render(new_context)
            if self.token_name.startswith("<"):
                rendered = rendered.strip()
        return rendered

    def set_component_attrs(self, context: Context, new_context: Context):
        """
        Set the attributes of the component tag in the new context.
        """
        if not self.token_name.startswith("<"):
            return False
        template = self.get_template(context)
        if not template.first_comment:
            return False
        if template.first_comment.startswith("props "):
            first_comment = template.first_comment[6:]
        elif template.first_comment.startswith("def "):
            first_comment = template.first_comment[4:]
        else:
            return False
        used_attrs = self.include_node.extra_context or {}
        defined_attrs = []
        for bit in smart_split(first_comment.strip()):
            if match := re.match(r"^(\w+)(?:=(.+?))?,?$", bit):
                attr, value = match.groups()
                defined_attrs.append(attr)
                if attr not in used_attrs:
                    if value is None:
                        raise TemplateSyntaxError(
                            f'Missing required attribute "{attr}" in '
                            f"{self.token_name}"
                        )
                    new_context[attr] = Variable(value).resolve(context)
        attrs = Attrs()
        for key, value in used_attrs.items():
            if key not in defined_attrs:
                attrs[key] = value.resolve(context)
            else:
                new_context[key] = value.resolve(context)
        for key, value in self.nested_attrs.items():
            attrs[key] = value.resolve(context)
        new_context["attrs"] = attrs
        return True

    def get_template(self, context) -> Template:
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
            cache = context.render_context.dicts[0].setdefault(self, {})
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
        return self._nested_attrs[key]

    def __getitem__(self, key):
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
                (f'{key}="{escape(value)}"' if value is not True else key)
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
            context_attrs = context_attrs.get(self.sub_key)
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
