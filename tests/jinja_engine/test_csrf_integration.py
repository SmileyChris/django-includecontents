"""Tests for CSRF token handling in Jinja2 components."""

from jinja2 import DictLoader, Environment

from includecontents.jinja2 import IncludeContentsExtension


def test_csrf_token_available_in_components() -> None:
    """Test that CSRF tokens are available in components when provided in context."""
    env = Environment(
        loader=DictLoader(
            {
                "components/form.html": (
                    "{# props action #}"
                    '<form action="{{ action }}" method="post">'
                    "{% if csrf_input %}{{ csrf_input }}{% endif %}"
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

    # Simulate Django's automatic CSRF context injection
    context = {
        "csrf_token": "test-csrf-token-123",
        "csrf_input": '<input type="hidden" name="csrfmiddlewaretoken" value="test-csrf-token-123">',
    }

    rendered = template.render(context)

    # CSRF token should be available in the component
    assert 'value="test-csrf-token-123"' in rendered
    assert 'name="csrfmiddlewaretoken"' in rendered
    assert 'action="/submit"' in rendered


def test_csrf_token_preserved_in_isolated_context() -> None:
    """Test that CSRF tokens are preserved even with context isolation."""
    env = Environment(
        loader=DictLoader(
            {
                "components/secure-form.html": (
                    "{# props title #}"
                    '<div class="form-container">'
                    "<h2>{{ title }}</h2>"
                    '<form method="post">'
                    '{% if csrf_token %}<input type="hidden" name="csrfmiddlewaretoken" value="{{ csrf_token }}">{% endif %}'
                    "{{ contents }}"
                    "</form>"
                    "</div>"
                )
            }
        ),
        extensions=[IncludeContentsExtension],
    )

    template = env.from_string(
        '{% includecontents "secure-form" title="Login" %}Username: <input name="username">{% endincludecontents %}'
    )

    # Context with CSRF token and other data that should be isolated
    context = {
        "csrf_token": "secure-token-456",
        "sensitive_data": "should-not-leak",
        "user_id": 123,
    }

    rendered = template.render(context)

    # CSRF token should be preserved in component
    assert 'value="secure-token-456"' in rendered
    assert "<h2>Login</h2>" in rendered
    assert "Username:" in rendered

    # Other context should not leak
    assert "should-not-leak" not in rendered
    assert "123" not in rendered


def test_csrf_token_in_nested_components() -> None:
    """Test that CSRF tokens work correctly in nested components."""
    env = Environment(
        loader=DictLoader(
            {
                "components/page.html": (
                    "{# props title #}"
                    '<div class="page">'
                    "<h1>{{ title }}</h1>"
                    "{{ contents }}"
                    "</div>"
                ),
                "components/contact-form.html": (
                    '<form class="contact-form" method="post">'
                    '{% if csrf_token %}<input type="hidden" name="csrfmiddlewaretoken" value="{{ csrf_token }}">{% endif %}'
                    '<input name="email" placeholder="Email">'
                    '<button type="submit">Send</button>'
                    "</form>"
                ),
            }
        ),
        extensions=[IncludeContentsExtension],
    )

    template = env.from_string("""
    {% includecontents "page" title="Contact Us" %}
        {% includecontents "contact-form" %}{% endincludecontents %}
    {% endincludecontents %}
    """)

    context = {
        "csrf_token": "nested-csrf-789",
    }

    rendered = template.render(context)

    # Both components should have access to CSRF token
    assert 'value="nested-csrf-789"' in rendered
    assert "<h1>Contact Us</h1>" in rendered
    assert 'class="contact-form"' in rendered


def test_no_csrf_token_when_not_provided() -> None:
    """Test that components handle missing CSRF tokens gracefully."""
    env = Environment(
        loader=DictLoader(
            {
                "components/optional-csrf.html": (
                    '<form method="post">'
                    "{% if csrf_token %}"
                    '<input type="hidden" name="csrfmiddlewaretoken" value="{{ csrf_token }}">'
                    "{% else %}"
                    "<!-- CSRF token not available -->"
                    "{% endif %}"
                    "{{ contents }}"
                    "</form>"
                )
            }
        ),
        extensions=[IncludeContentsExtension],
    )

    template = env.from_string(
        '{% includecontents "optional-csrf" %}Content{% endincludecontents %}'
    )

    # No CSRF token in context
    context = {}

    rendered = template.render(context)

    # Should render without CSRF token
    assert "<!-- CSRF token not available -->" in rendered
    assert "Content" in rendered
    assert "csrfmiddlewaretoken" not in rendered


def test_csrf_input_vs_csrf_token() -> None:
    """Test that both csrf_input and csrf_token variables work correctly."""
    env = Environment(
        loader=DictLoader(
            {
                "components/dual-csrf.html": (
                    '<form method="post">'
                    "<!-- Using csrf_input for complete input -->"
                    "{% if csrf_input %}{{ csrf_input }}{% endif %}"
                    "<!-- Using csrf_token for custom input -->"
                    '{% if csrf_token %}<input type="hidden" name="custom_csrf" value="{{ csrf_token }}">{% endif %}'
                    "{{ contents }}"
                    "</form>"
                )
            }
        ),
        extensions=[IncludeContentsExtension],
    )

    template = env.from_string(
        '{% includecontents "dual-csrf" %}Test{% endincludecontents %}'
    )

    # Both csrf_input and csrf_token provided (as Django would)
    context = {
        "csrf_token": "token-value-999",
        "csrf_input": '<input type="hidden" name="csrfmiddlewaretoken" value="token-value-999">',
    }

    rendered = template.render(context)

    # Both should be present
    assert (
        'name="csrfmiddlewaretoken" value="token-value-999"' in rendered
    )  # From csrf_input
    assert 'name="custom_csrf" value="token-value-999"' in rendered  # From csrf_token
    assert "Test" in rendered
