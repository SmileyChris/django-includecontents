from django.middleware.csrf import get_token
from django.template.loader import render_to_string


def test_csrf_token_passing(rf):
    """Test that CSRF token is properly passed through includecontents."""
    request = rf.get("/")
    csrf_token = get_token(request)

    context = {
        "request": request,
        "csrf_token": csrf_token,
    }

    rendered = render_to_string("test_csrf/base.html", context)
    assert csrf_token in rendered
    assert '<input type="hidden" name="csrfmiddlewaretoken"' in rendered


def test_csrf_token_in_component(rf):
    """Test that CSRF token works in component-style includecontents."""
    request = rf.get("/")
    csrf_token = get_token(request)

    context = {
        "request": request,
        "csrf_token": csrf_token,
    }

    rendered = render_to_string("test_csrf/component.html", context)
    assert csrf_token in rendered
    assert '<input type="hidden" name="csrfmiddlewaretoken"' in rendered


def test_csrf_token_isolated_context(rf):
    """Test that CSRF token is passed even with isolated context."""
    request = rf.get("/")
    csrf_token = get_token(request)

    context = {
        "request": request,
        "csrf_token": csrf_token,
        "isolated_context": True,
    }

    rendered = render_to_string("test_csrf/base.html", context)
    assert csrf_token in rendered
    assert '<input type="hidden" name="csrfmiddlewaretoken"' in rendered
