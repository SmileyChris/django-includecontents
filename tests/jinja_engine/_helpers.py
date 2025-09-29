from __future__ import annotations

from textwrap import dedent
from typing import Any, Iterable, Mapping

from jinja2 import DictLoader, Environment

from includecontents.jinja2.extension import IncludeContentsExtension

__all__ = ["render_component", "captures_for", "first_capture"]

_COMPONENT_LIBRARY: dict[str, str] = {
    "card": dedent(
        """
        {# props title="" #}
        {% set final_attrs = attrs(class_='& card') %}
        {{ record(
            component="card",
            title=title|default(""),
            attrs=final_attrs,
            default=contents.default|trim,
            oldstyle=contents.oldstyle|trim,
            newstyle=contents.newstyle|trim,
            contents=contents,
        ) }}
        <section {{ final_attrs }}>{{ contents }}</section>
        """
    ),
    "card-extend": dedent(
        """
        {# props title="" #}
        {% set final_attrs = attrs(class_='& card-extend') %}
        {{ record(component="card-extend", attrs=final_attrs) }}
        <section {{ final_attrs }}>{{ contents }}</section>
        """
    ),
    "card-prepend": dedent(
        """
        {# props title="" #}
        {% set final_attrs = attrs(class_='card-prepend &') %}
        {{ record(component="card-prepend", attrs=final_attrs) }}
        <section {{ final_attrs }}>{{ contents }}</section>
        """
    ),
    "card-conditional": dedent(
        """
        {# props title="" #}
        {% set final_attrs = attrs(class_='& card') %}
        {{ record(component="card-conditional", attrs=final_attrs) }}
        <section {{ final_attrs }}>{{ contents }}</section>
        """
    ),
    "button": dedent(
        """
        {# props text="" variant=primary,secondary #}
        {{ record(component="button", attrs=attrs, variant=variant, variantPrimary=variantPrimary, variantSecondary=variantSecondary) }}
        <button {{ attrs }}>{{ contents }}</button>
        """
    ),
    "button-props": dedent(
        """
        {# props text, size #}
        {{ record(component="button-props", text=text, size=size) }}
        <button>{{ contents }}</button>
        """
    ),
    "nested-attrs": dedent(
        """
        {{ record(component="nested-attrs", attrs=attrs, inner=attrs.inner) }}
        <div {{ attrs }}></div>
        <div {{ attrs.inner }}></div>
        """
    ),
    "form-with-button": dedent(
        """
        {% set button_group = attrs._nested_attrs.get('button') %}
        {{ record(component="form-with-button", attrs=attrs, button=button_group) }}
        <form {{ attrs }}>{{ contents }}</form>
        """
    ),
    "body_text": dedent(
        """
        {# props alignment, size #}
        {{ record(component="body_text", alignment=alignment, size=size) }}
        <div class="body{% if alignment %} text-{{ alignment }}{% endif %}{% if size %} body-{{ size }}{% endif %}">
          {{ contents }}
        </div>
        """
    ),
    "nested-component": dedent(
        """
        {% set inner_group = attrs._nested_attrs.get('inner') %}
        {{ record(component="nested-component", attrs=attrs, inner=inner_group, contents=contents) }}
        <div {{ attrs }}>{{ contents }}</div>
        """
    ),
    "flexible-card": dedent(
        """
        {# props title="" #}
        {% set data_attrs = {} %}
        {% for key, value in attrs._attrs.items() %}
            {% if key.startswith('data-') %}
                {% set data_key = key[5:] %}
                {% do data_attrs.update({data_key: value}) %}
            {% endif %}
        {% endfor %}
        {% set regular_attrs = {} %}
        {% for key, value in attrs._attrs.items() %}
            {% if not key.startswith('data-') %}
                {% do regular_attrs.update({key: value}) %}
            {% endif %}
        {% endfor %}
        {{ record(
            component="flexible-card",
            title=title|default(""),
            attrs=regular_attrs,
            data_attrs=data_attrs,
            default=contents.default|trim,
            header=contents.header|trim,
        ) }}
        <div {{ attrs }}>{{ contents }}</div>
        """
    ),
    "card-with-footer": dedent(
        """
        {# props title #}
        {{ record(
            component="card-with-footer",
            title=title,
            default=contents.default|trim,
            footer=contents.footer|trim,
            sidebar=contents.sidebar|trim,
        ) }}
        <card title="{{ title }}">
            <main>{{ contents }}</main>
            <footer>{{ contents.footer }}</footer>
            <aside>{{ contents.sidebar }}</aside>
        </card>
        """
    ),
    "outer-card": dedent(
        """
        {# props title #}
        {{ record(
            component="outer-card",
            title=title,
            main=contents.main|trim,
            footer=contents.footer|trim,
        ) }}
        <card title="{{ title }}">
            <main>{{ contents.main }}</main>
            <footer>{{ contents.footer }}</footer>
        </card>
        """
    ),
    "test_undefined": dedent(
        """
        {# props defined_var #}
        {{ record(component="test_undefined", defined_var=defined_var) }}
        Component with undefined variables:
        {{ defined_var }}
        {{ undefined_var }}
        {{ another_undefined }}
        """
    ),
    "inner-card": dedent(
        """
        {# props title #}
        {{ record(
            component="inner-card",
            title=title,
            body=contents.default|trim,
            footer=contents.footer|trim,
        ) }}
        <inner>{{ contents }}</inner>
        """
    ),
    "card-with-props": dedent(
        """
        {# props title, variant, size #}
        {{ record(
            component="card-with-props",
            title=title,
            variant=variant,
            size=size,
            body=contents.body|trim,
        ) }}
        <card>{{ contents.body }}</card>
        """
    ),
    "button-optional": dedent(
        """
        {# props variant=,primary,secondary,dark-mode,icon-only #}
        {{ record(component="button-optional", variant=variant) }}
        <button>{{ contents }}</button>
        """
    ),
    "button-multi": dedent(
        """
        {# props variant=primary,secondary,accent,icon,large #}
        {{ record(
            component="button-multi",
            variant=variant,
            primary_flag=variantPrimary,
            icon_flag=variantIcon,
        ) }}
        <button>{{ contents }}</button>
        """
    ),
    "enum-edge-cases": dedent(
        """
        {# props status=,pending,complete,failed special=,@,#,$,% single=,a numbers=,1,2,3 mixed=,test,other #}
        {{ record(
            component="enum-edge-cases",
            status=status,
            special=special,
            single=single,
            numbers=numbers,
            mixed=mixed,
        ) }}
        <div>{{ contents }}</div>
        """
    ),
    "enum-whitespace": dedent(
        """
        {# props variant=,a,b,c #}
        {{ record(component="enum-whitespace", variant=variant) }}
        <div>{{ contents }}</div>
        """
    ),
    "complex-component": dedent(
        """
        {% set inner_group = attrs._nested_attrs.get('inner') %}
        {% set inner_attrs = {} %}
        {% set inner_data_attrs = {} %}
        {% if inner_group %}
            {% for key, value in inner_group._attrs.items() %}
                {% if key.startswith('data-') %}
                    {% set data_key = key[5:] %}
                    {% do inner_data_attrs.update({data_key: value}) %}
                {% else %}
                    {% do inner_attrs.update({key: value}) %}
                {% endif %}
            {% endfor %}
        {% endif %}
        {{ record(
            component="complex-component",
            attrs=attrs._attrs,
            inner=inner_attrs,
            inner_data=inner_data_attrs,
            class_value=attrs._attrs.get('class', ''),
        ) }}
        <div>{{ contents }}</div>
        """
    ),
    "simple-button": dedent(
        """
        {# props variant=primary,secondary size=small,large #}
        {{ record(component="simple-button", variant=variant, size=size, text=contents.default|trim) }}
        <button class="btn-{{ variant }} btn-{{ size }}">{{ contents }}</button>
        """
    ),
    "simple-card": dedent(
        """
        {# props title="" #}
        {{ record(component="simple-card", title=title|default(""), attrs=attrs) }}
        <section {{ attrs }}>{{ contents }}</section>
        """
    ),
    "container": dedent(
        """
        {% for name, value in contents.items() %}
            {{ record(component="container", slot=name, value=value|trim) }}
        {% endfor %}
        {{ record(component="container", slot=None, value=contents.default|trim) }}
        <div>{{ contents }}</div>
        """
    ),
    "section": dedent(
        """
        {# props name #}
        {{ record(component="section", name=name, body=contents.default|trim) }}
        <section>{{ contents }}</section>
        """
    ),
}

for i in range(1, 11):
    _COMPONENT_LIBRARY[f"level{i}"] = dedent(
        f"""
        {{{{ record(component='level{i}', level={i}, payload=contents.default|trim) }}}}
        {{{{ contents }}}}
        """
    )


def _select_components(names: Iterable[str]) -> dict[str, str]:
    selected: dict[str, str] = {}
    missing: list[str] = []
    for name in names:
        try:
            selected[name] = _COMPONENT_LIBRARY[name]
        except KeyError:
            missing.append(name)
    if missing:
        raise KeyError(f"No component templates registered for: {', '.join(missing)}")
    return selected


def _normalize_components(components: Mapping[str, str]) -> dict[str, str]:
    return {
        f"components/{name}.html": dedent(template).strip()
        for name, template in components.items()
    }


def render_component(
    template_source: str,
    *,
    use: Iterable[str] = (),
    components: Mapping[str, str] | None = None,
    context: Mapping[str, Any] | None = None,
    autoescape: bool = False,
    use_do: bool = True,
    extra_extensions: Iterable[Any] | None = None,
) -> tuple[str, list[dict[str, Any]]]:
    templates = {"page.html": dedent(template_source).strip()}

    merged_components: dict[str, str] = {}
    if use:
        merged_components.update(_select_components(use))
    if components:
        merged_components.update(components)

    templates.update(_normalize_components(merged_components))

    extensions: list[Any] = [IncludeContentsExtension]
    if use_do:
        extensions.append("jinja2.ext.do")
    if extra_extensions:
        extensions.extend(extra_extensions)

    env = Environment(
        loader=DictLoader(templates),
        extensions=extensions,
        autoescape=autoescape,
    )

    captures: list[dict[str, Any]] = []

    def record(**payload: Any) -> str:
        captures.append(payload)
        return ""

    env.globals.setdefault("record", record)

    rendered = env.get_template("page.html").render(**(dict(context or {})))
    return rendered, captures


def captures_for(
    captures: Iterable[dict[str, Any]], component: str
) -> list[dict[str, Any]]:
    return [entry for entry in captures if entry.get("component") == component]


def first_capture(captures: Iterable[dict[str, Any]], component: str) -> dict[str, Any]:
    matches = captures_for(captures, component)
    if not matches:
        raise AssertionError(f"No capture recorded for component {component!r}")
    return matches[0]
