from django.urls import path

from . import views

app_name = "showcase"

urlpatterns = [
    path("", views.index, name="index"),
    path("search/", views.search_view, name="search"),

    # Design tokens URLs (Style Dictionary)
    path("tokens/", views.tokens_index, name="tokens_index"),
    path("tokens/search/", views.tokens_search_view, name="tokens_search"),
    path("tokens/<str:category>/", views.token_category_view, name="token_category"),

    # Tailwind tokens URLs
    path("tailwind/", views.tailwind_tokens_index, name="tailwind_tokens_index"),
    path("tailwind/search/", views.tailwind_tokens_search_view, name="tailwind_tokens_search"),
    path("tailwind/<str:category>/", views.tailwind_token_category_view, name="tailwind_token_category"),

    # Component URLs
    path("component/<str:component_name>/", views.component_view, name="component"),
    path(
        "component/<str:component_name>/preview/",
        views.ComponentPreviewView.as_view(),
        name="component_preview",
    ),
    path(
        "component/<str:component_name>/iframe-preview/",
        views.ComponentIframePreviewView.as_view(),
        name="component_iframe_preview",
    ),

    # Category URL must come after more specific component URLs.
    path("<str:category>/", views.category_view, name="category"),
]