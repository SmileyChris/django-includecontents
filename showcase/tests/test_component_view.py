import json
from pathlib import Path

import pytest
from django.test import Client
from django.urls import reverse

from showcase.models import ComponentInfo, PropDefinition
from showcase.registry import registry


@pytest.fixture
def showcase_component(settings, tmp_path):
    original_dirs = list(settings.TEMPLATES[0]["DIRS"])
    showcase_template_dir = Path(__file__).resolve().parent.parent / "templates"
    settings.TEMPLATES[0]["DIRS"] = [
        str(tmp_path),
        str(showcase_template_dir),
        *original_dirs,
    ]

    import showcase
    from showcase.apps import ShowcaseConfig

    ShowcaseConfig("showcase", showcase).ready()

    had_root_urlconf = hasattr(settings, "ROOT_URLCONF")
    original_root_urlconf = getattr(settings, "ROOT_URLCONF", None)
    settings.ROOT_URLCONF = "showcase.tests.urls"

    component_template = tmp_path / "components" / "forms"
    component_template.mkdir(parents=True)
    (component_template / "button.html").write_text(
        "{# props label=\"Submit\" #}\n<button class=\"btn\">{{ label }}</button>\n",
        encoding="utf-8",
    )

    original_components = registry._components.copy()
    original_categories = {key: list(value) for key, value in registry._categories.items()}
    original_discovered = registry._discovered

    component = ComponentInfo(
        name="forms:button",
        path="forms/button.html",
        category="Forms",
        description="Test button component",
        props={
            "label": PropDefinition(name="label", default="Submit"),
        },
    )

    registry._components = {component.name: component}
    registry._categories = {component.category: [component.name]}
    registry._discovered = True

    try:
        yield component
    finally:
        settings.TEMPLATES[0]["DIRS"] = original_dirs
        if had_root_urlconf:
            settings.ROOT_URLCONF = original_root_urlconf
        else:
            delattr(settings, "ROOT_URLCONF")
        registry._components = original_components
        registry._categories = original_categories
        registry._discovered = original_discovered


def test_component_slug_strips_category():
    component = ComponentInfo(name="forms:button", path="forms/button.html")
    assert component.slug == "button"


@pytest.mark.django_db
def test_component_view_renders(client: Client, showcase_component):
    url = reverse("showcase:component", args=(showcase_component.name,))
    response = client.get(url)

    assert response.status_code == 200
    assert b"Test button component" in response.content
    assert showcase_component.slug == "button"


@pytest.mark.django_db
def test_component_preview_returns_html(client: Client, showcase_component):
    url = reverse("showcase:component_preview", args=(showcase_component.name,))
    payload = {
        "props": {"label": "Click me"},
        "content": "",
        "content_blocks": {},
    }

    response = client.post(url, data=json.dumps(payload), content_type="application/json")

    assert response.status_code == 200
    data = response.json()
    assert "<button" in data["html"]
    assert "Click me" in data["html"]


@pytest.mark.django_db
def test_category_view_renders_with_correct_component_links(client: Client, showcase_component):
    # Test that category view renders and has correct component links
    url = reverse("showcase:category", args=("forms",))
    response = client.get(url)

    assert response.status_code == 200
    assert b"Forms Components" in response.content

    # Check that component link uses correct URL pattern
    component_url = reverse("showcase:component", args=(showcase_component.name,))
    assert component_url.encode() in response.content


@pytest.mark.django_db
def test_component_preview_url_pattern_matches_js_expectations(client: Client, showcase_component):
    """Test that the JavaScript-generated preview URLs match the actual URL patterns"""
    # Test the iframe preview URL
    iframe_url = reverse("showcase:component_iframe_preview", args=(showcase_component.name,))
    assert iframe_url == f"/showcase/component/{showcase_component.name}/iframe-preview/"

    # Test the AJAX preview URL
    ajax_url = reverse("showcase:component_preview", args=(showcase_component.name,))
    assert ajax_url == f"/showcase/component/{showcase_component.name}/preview/"
