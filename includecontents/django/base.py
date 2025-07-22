import re

import django.template.base
from django.utils.text import smart_split


def process_component_with_template_tags(token_string, position, lineno):
    """
    Process a component token that may contain template tags in attribute values.
    Returns a list of tokens to be inserted into the token stream.
    """
    # Parse the component normally first
    content = token_string[1:-1].strip()
    self_closing = content.endswith("/")
    if self_closing:
        content = content[:-1].strip()
    
    bits = list(smart_split(content))
    tag_name = bits.pop(0)
    
    # Check if any attributes contain template tags
    has_template_tags = False
    processed_attrs = []
    
    for attr in bits:
        if '=' in attr and ('"' in attr or "'" in attr):
            # Check for template tags in this attribute
            attr_name, quoted_value = attr.split('=', 1)
            if ((quoted_value.startswith('"') and quoted_value.endswith('"')) or 
                (quoted_value.startswith("'") and quoted_value.endswith("'"))):
                
                inner_content = quoted_value[1:-1]
                template_tag_re = re.compile(r"({%.*?%}|{{.*?}}|{#.*?#})", re.DOTALL)
                
                if template_tag_re.search(inner_content):
                    has_template_tags = True
                    # For now, keep the attribute as-is - Django will process the template tags
                    processed_attrs.append(attr)
                else:
                    processed_attrs.append(attr)
            else:
                processed_attrs.append(attr)
        else:
            # Handle deprecated {} syntax
            if group := re.match(r"([-:.\w]+)=\{(.+)\}", attr):
                attr = f"{group[1]}={group[2]}"
            processed_attrs.append(attr)
    
    # Build the includecontents tag
    content_parts = [
        "includecontents",
        f"_{tag_name}{'/' if self_closing else ''}",
        f'"components/{tag_name[8:].replace(":", "/")}.html"',
    ]
    if processed_attrs:
        content_parts.append("with")
        content_parts.extend(processed_attrs)
    
    return django.template.base.Token(
        django.template.base.TokenType.BLOCK,
        " ".join(content_parts),
        position,
        lineno,
    )


class Template(django.template.base.Template):
    first_comment: str | None

    def compile_nodelist(self):
        """
        Parse and compile the template source into a nodelist. If debug
        is True and an exception occurs during parsing, the exception is
        annotated with contextual line information where it occurred in the
        template source.
        """
        if self.engine.debug:
            lexer = DebugLexer(self.source)
        else:
            lexer = Lexer(self.source)

        tokens = lexer.tokenize()
        parser = Parser(
            tokens,
            self.engine.template_libraries,
            self.engine.template_builtins,
            self.origin,
        )

        try:
            nodelist = parser.parse()
            self.first_comment = parser.first_comment
            self.extra_data = getattr(parser, "extra_data", None)  # Django 5.1+
            return nodelist
        except Exception as e:
            if self.engine.debug:
                e.template_debug = self.get_exception_info(e, e.token)  # type: ignore
            raise


tag_re = re.compile(
    r"({%.*?%}|{{.*?}}|{#.*?#}|</?include:(?:\"[^\"]*\"|'[^']*'|[^>])*?>|</?content:[-\w]+\s*>)", re.DOTALL
)


class Lexer(django.template.base.Lexer):
    def tokenize(self):
        """
        Return a list of tokens from a given template_string.
        """
        in_tag = False
        lineno = 1
        result = []
        for token_string in tag_re.split(self.template_string):
            if token_string:
                result.append(self.create_token(token_string, None, lineno, in_tag))
                lineno += token_string.count("\n")
            in_tag = not in_tag
        return result

    def create_token(self, token_string, position, lineno, in_tag):
        """
        Convert the given token string into a new Token object and return it.
        If in_tag is True, we are processing something that matched a tag,
        otherwise it should be treated as a literal string.

        Extends the default implementation to convert include: tags into
        includecontents tags and content: tags into contents blocks.
        """
        if in_tag and token_string.startswith("</content:"):
            # Convert </content:name> to {% endcontents %}
            return django.template.base.Token(
                django.template.base.TokenType.BLOCK,
                "endcontents",
                position,
                lineno,
            )
        elif in_tag and token_string.startswith("<content:"):
            # Convert <content:name> to {% contents name %}
            content_name = token_string[9:-1]  # Remove <content: and >
            return django.template.base.Token(
                django.template.base.TokenType.BLOCK,
                f"contents {content_name}",
                position,
                lineno,
            )
        elif in_tag and token_string.startswith("</include:"):
            # Normalize closing tags by removing any whitespace before the closing >
            # Handle cases like "</include:item\n>" -> "</include:item>"
            if token_string.endswith('>'):
                # Find the position of > and remove any whitespace before it
                content = token_string[:-1].rstrip()  # Everything except the >
                cleaned = content + '>'
            else:
                cleaned = token_string
            return django.template.base.Token(
                django.template.base.TokenType.BLOCK,
                cleaned,
                position,
                lineno,
            )
        elif in_tag and token_string.startswith("<include:"):
            return process_component_with_template_tags(token_string, position, lineno)
        return super().create_token(token_string, position, lineno, in_tag)


class DebugLexer(django.template.base.DebugLexer, Lexer):
    def _tag_re_split_positions(self):
        last = 0
        for match in tag_re.finditer(self.template_string):
            start, end = match.span()
            yield last, start
            yield start, end
            last = end
        yield last, len(self.template_string)


class Parser(django.template.base.Parser):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.tags = TagsDict(self.tags)
        self.first_comment = None

    def next_token(self) -> django.template.base.Token:
        token = super().next_token()
        if (
            self.first_comment is None and token.token_type.value == 3
        ):  # TokenType.COMMENT:
            self.first_comment = token.contents.strip()
        return token


class TagsDict(dict):
    """
    A dictionary that allows access to tags with a dot-separated suffix that the
    tag could use to change behavior.
    """

    def __getitem__(self, key):
        if isinstance(key, str) and "." in key:
            key = key.split(".", maxsplit=1)[0]
        return super().__getitem__(key)
