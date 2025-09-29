"""Tests for Jinja2 context isolation in components."""

from jinja2 import DictLoader, Environment

from includecontents.jinja2 import IncludeContentsExtension


def test_context_isolation_preserves_essential_keys() -> None:
    """Test that context isolation preserves essential keys like request and csrf_token."""
    env = Environment(
        loader=DictLoader(
            {
                "components/form.html": (
                    "{# props action #}"
                    '<form action="{{ action }}">'
                    '{% if csrf_token %}<input type="hidden" name="csrf" value="{{ csrf_token }}">{% endif %}'
                    "{{ contents }}"
                    "</form>"
                )
            }
        ),
        extensions=[IncludeContentsExtension],
    )

    template = env.from_string(
        '{% includecontents "form" action="/submit" %}Fields{% endincludecontents %}'
    )

    # Render with context that includes both preserved and non-preserved keys
    context = {
        "csrf_token": "abc123",
        "request": {"user": "testuser"},
        "non_preserved_key": "should_not_leak",
        "another_key": "also_should_not_leak",
    }

    rendered = template.render(context)

    # csrf_token should be preserved
    assert 'value="abc123"' in rendered
    assert 'action="/submit"' in rendered
    # Component should not have access to non-preserved keys
    assert "should_not_leak" not in rendered
    assert "also_should_not_leak" not in rendered


def test_context_isolation_disabled() -> None:
    """Test that context isolation can be disabled."""
    env = Environment(
        loader=DictLoader(
            {
                "components/debug.html": (
                    '<div>custom_var: {{ custom_var|default("not found") }}</div>'
                )
            }
        ),
        extensions=[IncludeContentsExtension],
    )

    # Disable context isolation
    extension = env.extensions[IncludeContentsExtension.identifier]
    extension.use_context_isolation = False

    template = env.from_string(
        '{% includecontents "debug" %}Test{% endincludecontents %}'
    )

    context = {"custom_var": "leaked_value"}
    rendered = template.render(context)

    # With isolation disabled, all context should be available
    assert "custom_var: leaked_value" in rendered


def test_context_isolation_enabled_by_default() -> None:
    """Test that context isolation is enabled by default for components with props."""
    env = Environment(
        loader=DictLoader(
            {
                "components/debug.html": (
                    '{# props message="" #}'
                    "<div>Message: {{ message }}</div>"
                    '<div>custom_var: {{ custom_var|default("not found") }}</div>'
                )
            }
        ),
        extensions=[IncludeContentsExtension],
    )

    template = env.from_string(
        '{% includecontents "debug" message="Hello" %}Test{% endincludecontents %}'
    )

    context = {"custom_var": "should_not_leak"}
    rendered = template.render(context)

    # With isolation enabled (default), custom_var should not be available
    assert "Message: Hello" in rendered
    assert "custom_var: not found" in rendered


def test_props_override_preserved_keys() -> None:
    """Test that component props can override preserved keys."""
    env = Environment(
        loader=DictLoader(
            {"components/user.html": ("{# props user #}<div>User: {{ user }}</div>")}
        ),
        extensions=[IncludeContentsExtension],
    )

    template = env.from_string(
        '{% includecontents "user" user="component_user" %}Test{% endincludecontents %}'
    )

    context = {"user": "context_user"}
    rendered = template.render(context)

    # Component prop should override the preserved key
    assert "User: component_user" in rendered


def test_nested_components_context_isolation() -> None:
    """Test that nested components maintain proper context isolation."""
    env = Environment(
        loader=DictLoader(
            {
                "components/outer.html": (
                    "{# props title #}"
                    '<div class="outer">'
                    "<h1>{{ title }}</h1>"
                    '<p>Secret: {{ secret|default("not found") }}</p>'
                    "{{ contents }}"
                    "</div>"
                ),
                "components/inner.html": (
                    '{# props dummy="" #}'
                    '<div class="inner">'
                    '<p>Secret: {{ secret|default("not found") }}</p>'
                    "{{ contents }}"
                    "</div>"
                ),
            }
        ),
        extensions=[IncludeContentsExtension],
    )

    template = env.from_string(
        '{% includecontents "outer" title="Outer Title" %}'
        '{% includecontents "inner" %}Inner content{% endincludecontents %}'
        "{% endincludecontents %}"
    )

    context = {"secret": "should_not_leak"}
    rendered = template.render(context)

    # Both components should not see the secret
    assert rendered.count("Secret: not found") == 2
    assert "should_not_leak" not in rendered
    assert "Outer Title" in rendered
