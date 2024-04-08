import re

import django.template.base
from django.utils.text import smart_split


class TemplateX(django.template.base.Template):
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
                e.template_debug = self.get_exception_info(e, e.token)
            raise


tag_re = re.compile(r"({%.*?%}|{{.*?}}|{#.*?#}|</?[A-Z].*?>)")


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
        """
        if in_tag and token_string.startswith("<"):
            content = token_string[1:-1].strip()
            if content.startswith("/"):
                return django.template.base.Token(
                    django.template.base.TokenType.BLOCK,
                    token_string,
                    position,
                    lineno,
                )
            # Strip {} from attributes
            bits = list(smart_split(content))
            template_name = bits.pop(0)
            attrs = []
            for attr in bits:
                if group := re.match(r"(\w+)=\{(.+)\}", attr):
                    attr = f"{group[1]}={group[2]}"
                attrs.append(attr)
            content = [
                f"includecontents _{content.split(maxsplit=1)[0]}",
                f'"components/{template_name}.html"',
                "only",
            ]
            if attrs:
                content.append(f"with {' '.join(attrs)}")
            return django.template.base.Token(
                django.template.base.TokenType.BLOCK,
                " ".join(content),
                position,
                lineno,
            )
        return super().create_token(token_string, position, lineno, in_tag)


class DebugLexer(django.template.base.DebugLexer):

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
        self.first_comment = None

    def next_token(self) -> django.template.base.Token:
        token = super().next_token()
        if (
            self.first_comment is None and token.token_type.value == 3
        ):  # TokenType.COMMENT:
            self.first_comment = token.contents.strip()
        return token
