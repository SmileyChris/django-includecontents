import re
from collections import abc
from collections.abc import MutableMapping

from django import template
from django.template import TemplateSyntaxError
from django.template.base import NodeList, Parser, Token, TokenType
from django.template.context import Context
from django.template.loader_tags import construct_relative_path, do_include
from django.utils.html import escape
from django.utils.safestring import mark_safe

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
    token.contents = re_tag.sub(r"<\1>", token.contents)
    token_name = token.contents.split(maxsplit=1)[0]
    if token_name.startswith("<"):
        if not token_name.endswith(">"):
            token_name = f"{token_name}>"
        parser.command_stack[-1] = (token_name,) + parser.command_stack[-1][1:]
    nodelist, named_nodelists = get_contents_nodelists(parser, token_name)
    include_node = do_include(parser, token)
    include_node.origin = parser.origin
    isolated_context = include_node.isolated_context
    include_node.isolated_context = False
    return IncludeContentsNode(
        token_name=token_name,
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
        include_node,
        nodelist,
        named_nodelists,
        isolated_context,
    ):
        self.token_name = token_name
        self.include_node = include_node
        self.nodelist = nodelist
        self.named_nodelists = named_nodelists
        self.isolated_context = isolated_context

    def render(self, context):
        new_context = context.new() if self.isolated_context else context
        with new_context.push():
            if self.token_name.startswith("<"):
                defined_attrs = self.get_defined_attrs(self.get_template(context))
                if defined_attrs is not None:
                    used_attrs = self.include_node.extra_context or {}
                    for attr, value in defined_attrs.items():
                        if attr not in used_attrs:
                            if value is None:
                                raise TemplateSyntaxError(
                                    "Missing required attribute in "
                                    f"{self.token_name}: {attr}"
                                )
                            new_context[attr] = value
                    attrs = Attrs()
                    for key, value in used_attrs.items():
                        if key not in defined_attrs:
                            attrs[key] = value.resolve(context)
                    new_context["attrs"] = attrs
            new_context["contents"] = RenderedContents(
                # Contents aren't rendered with isolation, hence the use of context
                # rather than new_context.
                context,
                nodelist=self.nodelist,
                named_nodelists=self.named_nodelists,
            )
            rendered = self.include_node.render(new_context)
            if self.token_name.startswith("<"):
                rendered = rendered.strip()
        return rendered

    def get_template(self, context):
        template = self.include_node.template.resolve(context)
        # Does this quack like a Template?
        if not callable(getattr(template, "render", None)):
            # If not, try the cache and select_template().
            template_name = template or ()
            if isinstance(template_name, str):
                template_name = (
                    construct_relative_path(
                        self.origin.template_name,
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

    def get_defined_attrs(self, template):
        if not template.first_comment or not template.first_comment.startswith("def "):
            return
        return Attrs(template.first_comment[4:].strip())


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


class Attrs(MutableMapping):
    def __init__(self, attr_string: str = ""):
        self._attrs = {}
        if attr_string:
            self.set_attr(attr_string)

    def set_attr(self, value: str, only_if_unset=False):
        parser = Parser([])
        for bit in Token(TokenType.COMMENT, value).split_contents():
            if match := re.match(r"^(\w+)(?:=(.+?))?,?$", bit):
                if only_if_unset and match.group(1) in self:
                    continue
                self[match.group(1)] = (
                    parser.compile_filter(match.group(2)).resolve({})
                    if match.group(2)
                    else None
                )

    def __getitem__(self, key):
        return self._attrs[key]

    def __setitem__(self, key, value):
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
                (f'{key}="{escape(value)}"' if value is not None else key)
                for key, value in self._attrs.items()
            )
        )


@register.filter
def default_attr(attrs: Attrs, default: str):
    attrs.set_attr(default, only_if_unset=True)
    return attrs
