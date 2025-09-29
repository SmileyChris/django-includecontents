"""Component rendering tests for the experimental Jinja2 extension."""

from __future__ import annotations

import pytest
from jinja2 import DictLoader, Environment
from jinja2.exceptions import TemplateRuntimeError

from includecontents.jinja2 import IncludeContentsExtension


def _environment() -> Environment:
    loader = DictLoader(
        {
            "components/card.html": (
                "{# props title, active=False #}\n"
                "{{ title }}::{{ contents }}::{{ active }}::{{ attrs }}"
            ),
            "components/modal.html": (
                '{# props title="", size="md" #}\n'
                "<header>{{ contents.get('header') }}</header>"
                "<main>{{ contents }}</main>"
            ),
            "components/section.html": "<section>{{ contents }}</section>",
            "components/inside/cat.html": "Meow",
        }
    )
    return Environment(loader=loader, extensions=[IncludeContentsExtension])


def test_extension_can_be_registered() -> None:
    env = _environment()
    assert IncludeContentsExtension.identifier in env.extensions


def test_preprocess_translates_html_syntax() -> None:
    env = _environment()
    extension = env.extensions[IncludeContentsExtension.identifier]
    source = '<include:card title="Hi">Body</include:card>'
    processed = extension.preprocess(source, name=None)
    assert '{% includecontents "card" title="Hi" %}' in processed
    assert "{% endincludecontents %}" in processed


def test_preprocess_supports_self_closing_tag() -> None:
    env = _environment()
    extension = env.extensions[IncludeContentsExtension.identifier]
    source = '<include:icon name="check" />'
    processed = extension.preprocess(source, name=None)
    assert processed.count('{% includecontents "icon"') == 1
    assert processed.count("{% endincludecontents %}") == 1


def test_component_attrs_filter_present() -> None:
    env = _environment()
    assert "component_attrs" in env.filters
    assert env.filters["component_attrs"]("value") == "value"


def test_component_renders_template() -> None:
    env = _environment()
    template = env.from_string(
        '{% includecontents "card" title="Hello" active=True class="box" %}Body{% endincludecontents %}'
    )
    rendered = template.render()
    assert "Hello::Body::True::" in rendered
    attrs_segment = rendered.split("::")[-1]
    assert 'class="box"' in attrs_segment
    assert "title=" not in attrs_segment


def test_named_contents_are_exposed() -> None:
    env = _environment()
    template = env.from_string(
        '{% includecontents "modal" %}\n'
        "{% contents header %}Header{% endcontents %}\n"
        "Content body\n"
        "{% endincludecontents %}"
    )
    rendered = template.render()
    assert "<header>Header</header>" in rendered
    assert "Content body" in rendered


def test_html_syntax_renders() -> None:
    env = _environment()
    template = env.from_string('<include:card title="Hi">Body</include:card>')
    rendered = template.render()
    assert "Hi::Body::False::" in rendered


def test_component_attrs_and_expressions() -> None:
    env = _environment()
    template = env.from_string(
        '{% includecontents "card" title=user_title active class="box" %}Body{% endincludecontents %}'
    )
    rendered = template.render(user_title="Hola")
    assert "Hola::Body::True::" in rendered
    attrs_segment = rendered.split("::")[-1]
    assert "active" in attrs_segment
    assert 'class="box"' in attrs_segment
    assert "title=" not in attrs_segment


def test_html_syntax_binds_expressions() -> None:
    env = _environment()
    template = env.from_string(
        '<include:card :title="{{ greeting }}" class="box">Body</include:card>'
    )
    rendered = template.render(greeting="Bonjour")
    assert "Bonjour::Body::False::" in rendered
    attrs_segment = rendered.split("::")[-1]
    assert 'class="box"' in attrs_segment
    assert "title=" not in attrs_segment


def test_html_component_prefix_supported() -> None:
    env = _environment()
    template = env.from_string(
        '<html-component:card title="Hi">Body</html-component:card>'
    )
    rendered = template.render()
    assert "Hi::Body::False::" in rendered


def test_nested_components_share_render_stack() -> None:
    env = _environment()
    template = env.from_string(
        '{% includecontents "card" title="Outer" %}'
        '{% includecontents "section" %}Inner{% endincludecontents %}'
        "{% endincludecontents %}"
    )
    rendered = template.render()
    assert "Outer::" in rendered
    assert "<section>Inner</section>" in rendered


def test_missing_required_prop_raises() -> None:
    env = _environment()
    template = env.from_string(
        '{% includecontents "card" class="box" %}Body{% endincludecontents %}'
    )
    with pytest.raises(TemplateRuntimeError):
        template.render()


def test_default_prop_applied_when_missing() -> None:
    env = _environment()
    template = env.from_string(
        '{% includecontents "card" title="Hi" %}Body{% endincludecontents %}'
    )
    rendered = template.render()
    assert "Hi::Body::False::" in rendered


def test_unknown_attributes_flow_into_attrs() -> None:
    env = _environment()
    # Test that unknown attributes (not props) flow into attrs object
    template = env.from_string(
        '{% includecontents "card" title="Hi" class="test-class" %}Body{% endincludecontents %}'
    )
    rendered = template.render()
    attrs_segment = rendered.split("::")[-1]
    assert 'class="test-class"' in attrs_segment


def test_props_with_defaults() -> None:
    """Test component with props that have default values."""
    env = Environment(
        loader=DictLoader(
            {
                "components/button.html": (
                    '{# props variant="primary" size="md" #}'
                    '<button class="btn-{{ variant }} btn-{{ size }}">{{ contents }}</button>'
                )
            }
        ),
        extensions=[IncludeContentsExtension],
    )
    template = env.from_string(
        '{% includecontents "button" %}Click me{% endincludecontents %}'
    )
    rendered = template.render()
    assert "btn-primary" in rendered
    assert "btn-md" in rendered
    assert "Click me" in rendered


def test_enum_validation_accepts_valid_values() -> None:
    """Test that enum validation accepts valid values."""
    env = Environment(
        loader=DictLoader(
            {
                "components/button.html": (
                    "{# props variant=primary,secondary,danger #}"
                    '<button class="btn-{{ variant }}">{{ contents }}</button>'
                )
            }
        ),
        extensions=[IncludeContentsExtension],
    )

    # Test all valid enum values
    for variant in ["primary", "secondary", "danger"]:
        template_str = f'{{% includecontents "button" variant="{variant}" %}}Click{{% endincludecontents %}}'
        template = env.from_string(template_str)
        rendered = template.render()
        assert f"btn-{variant}" in rendered
        assert "Click" in rendered


def test_enum_validation_rejects_invalid_values() -> None:
    """Test that enum validation rejects invalid values with helpful errors."""
    env = Environment(
        loader=DictLoader(
            {
                "components/button.html": (
                    "{# props variant=primary,secondary,danger #}"
                    '<button class="btn-{{ variant }}">{{ contents }}</button>'
                )
            }
        ),
        extensions=[IncludeContentsExtension],
    )

    template = env.from_string(
        '{% includecontents "button" variant="invalid" %}Click{% endincludecontents %}'
    )
    with pytest.raises(TemplateRuntimeError) as exc_info:
        template.render()

    error_message = str(exc_info.value)
    assert 'Invalid value "invalid"' in error_message
    assert "Allowed values:" in error_message
    assert "'primary'" in error_message
    assert "'secondary'" in error_message
    assert "'danger'" in error_message


def test_enum_validation_with_suggestion() -> None:
    """Test that enum validation provides close match suggestions."""
    env = Environment(
        loader=DictLoader(
            {
                "components/button.html": (
                    "{# props variant=primary,secondary,danger #}"
                    '<button class="btn-{{ variant }}">{{ contents }}</button>'
                )
            }
        ),
        extensions=[IncludeContentsExtension],
    )

    template = env.from_string(
        '{% includecontents "button" variant="primery" %}Click{% endincludecontents %}'
    )
    with pytest.raises(TemplateRuntimeError) as exc_info:
        template.render()

    error_message = str(exc_info.value)
    assert "Did you mean 'primary'?" in error_message


def test_enum_flag_generation() -> None:
    """Test that enum values generate flag variables."""
    env = Environment(
        loader=DictLoader(
            {
                "components/test.html": (
                    "{# props variant=primary,danger #}"
                    "variant={{ variant }} "
                    "{% if variantPrimary %}primary-flag{% endif %} "
                    "{% if variantDanger %}danger-flag{% endif %}"
                )
            }
        ),
        extensions=[IncludeContentsExtension],
    )

    # Test primary variant
    template = env.from_string(
        '{% includecontents "test" variant="primary" %}{% endincludecontents %}'
    )
    rendered = template.render()
    assert "variant=primary" in rendered
    assert "primary-flag" in rendered
    assert "danger-flag" not in rendered

    # Test danger variant
    template = env.from_string(
        '{% includecontents "test" variant="danger" %}{% endincludecontents %}'
    )
    rendered = template.render()
    assert "variant=danger" in rendered
    assert "danger-flag" in rendered
    assert "primary-flag" not in rendered


def test_icon_html_syntax_preprocessing() -> None:
    """Test that icon HTML syntax is preprocessed correctly."""
    env = _environment()
    extension = env.extensions[IncludeContentsExtension.identifier]

    # Test simple icon
    source = '<icon:home class="nav-icon" />'
    processed = extension.preprocess(source, name=None)
    assert 'icon("home"' in processed
    assert '{"class": "nav-icon"}' in processed

    # Test icon with multiple attributes
    source = '<icon:user class="avatar" size="24" />'
    processed = extension.preprocess(source, name=None)
    assert 'icon("user"' in processed
    assert '{"class": "avatar", "size": "24"}' in processed


def test_icon_html_syntax_no_closing_tag() -> None:
    """Test that icon closing tags are ignored."""
    env = _environment()
    extension = env.extensions[IncludeContentsExtension.identifier]

    # Icons should not have closing tags
    source = '<icon:home class="icon" /></icon:home>'
    processed = extension.preprocess(source, name=None)

    # Should have one icon function call and no closing content
    assert processed.count('icon("home"') == 1
    assert "</icon:home>" not in processed


def test_mixed_component_and_icon_syntax() -> None:
    """Test that components and icons can be mixed."""
    env = _environment()
    extension = env.extensions[IncludeContentsExtension.identifier]

    source = """
    <include:card title="Test">
        <icon:home class="card-icon" />
        Content here
    </include:card>
    """
    processed = extension.preprocess(source, name=None)

    # Should have both component and icon syntax
    assert 'includecontents "card"' in processed
    assert 'icon("home"' in processed
    assert "endincludecontents" in processed


def test_props_override_defaults() -> None:
    """Test that provided props override defaults."""
    env = Environment(
        loader=DictLoader(
            {
                "components/button.html": (
                    '{# props variant="primary" size="md" #}'
                    '<button class="btn-{{ variant }} btn-{{ size }}">{{ contents }}</button>'
                )
            }
        ),
        extensions=[IncludeContentsExtension],
    )
    template = env.from_string(
        '{% includecontents "button" variant="danger" %}Delete{% endincludecontents %}'
    )
    rendered = template.render()
    assert "btn-danger" in rendered
    assert "btn-md" in rendered  # Default still used for size


def test_props_attrs_separation() -> None:
    """Test that props and attrs are properly separated."""
    env = Environment(
        loader=DictLoader(
            {
                "components/button.html": (
                    '{# props variant="primary" #}'
                    '<button class="btn-{{ variant }}" {{ attrs }}>{{ contents }}</button>'
                )
            }
        ),
        extensions=[IncludeContentsExtension],
    )
    template = env.from_string(
        '{% includecontents "button" variant="success" onclick="handleClick()" dataid="123" %}'
        "Save"
        "{% endincludecontents %}"
    )
    rendered = template.render()
    assert "btn-success" in rendered
    assert 'onclick="handleClick()"' in rendered
    assert 'dataid="123"' in rendered


def test_no_props_all_attrs() -> None:
    """Test component without props definition - all attributes are passed as context."""
    env = Environment(
        loader=DictLoader(
            {"components/simple.html": "<div>{{ title }} - {{ contents }}</div>"}
        ),
        extensions=[IncludeContentsExtension],
    )
    template = env.from_string(
        '{% includecontents "simple" title="Hello" %}World{% endincludecontents %}'
    )
    rendered = template.render()
    assert "Hello - World" in rendered


def test_subdirectory_component() -> None:
    """Test that subdirectory components work with colon syntax."""
    env = _environment()
    template = env.from_string("<include:inside:cat />")
    rendered = template.render()
    assert rendered == "Meow"
