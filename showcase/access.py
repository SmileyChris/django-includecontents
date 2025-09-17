from functools import wraps

from django.conf import settings
from django.http import Http404, HttpRequest, HttpResponse


def check_showcase_access(request: HttpRequest) -> HttpResponse | None:
    """Return an HTTP response if the request should be blocked."""

    debug_only = getattr(settings, "SHOWCASE_DEBUG_ONLY", False)
    require_login = getattr(settings, "SHOWCASE_REQUIRE_LOGIN", False)

    if debug_only and not settings.DEBUG:
        raise Http404()

    if require_login and not request.user.is_authenticated:
        from django.contrib.auth.views import redirect_to_login

        return redirect_to_login(request.get_full_path())

    return None


def showcase_view(view_func):
    """Decorator that enforces showcase access controls."""

    @wraps(view_func)
    def _wrapped(request: HttpRequest, *args, **kwargs):
        response = check_showcase_access(request)
        if response:
            return response
        return view_func(request, *args, **kwargs)

    return _wrapped


class ShowcaseAccessMixin:
    """Mixin that enforces showcase access controls for class-based views."""

    def dispatch(self, request: HttpRequest, *args, **kwargs):
        response = check_showcase_access(request)
        if response:
            return response
        return super().dispatch(request, *args, **kwargs)
