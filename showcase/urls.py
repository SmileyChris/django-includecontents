from django.urls import path

from . import views

app_name = "showcase"

urlpatterns = [
    path("", views.index, name="index"),
    path("search/", views.search_view, name="search"),

    # Design tokens URLs
    path("tokens/", views.tokens_index, name="tokens_index"),
    path("tokens/search/", views.tokens_search_view, name="tokens_search"),
    path("tokens/<str:category>/", views.token_category_view, name="token_category"),
    path("tokens/<str:category>/<str:token_path>/", views.token_detail_view, name="token_detail"),

    # Component URLs (must come after tokens to avoid conflicts)
    path("<str:category>/", views.category_view, name="category"),
    path("<str:category>/<str:name>/", views.component_view, name="component"),
    path(
        "<str:category>/<str:name>/preview/",
        views.ComponentPreviewView.as_view(),
        name="component_preview"
    ),
    path(
        "<str:category>/<str:name>/iframe-preview/",
        views.ComponentIframePreviewView.as_view(),
        name="component_iframe_preview"
    ),
]