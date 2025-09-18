import json
import re
from typing import Any, Dict, Tuple

from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import redirect, render
from django.template import Template, Context
from django.views import View
from django.utils.decorators import method_decorator
from django.views.decorators.clickjacking import xframe_options_exempt

from .access import ShowcaseAccessMixin, showcase_view
from .registry import registry
from .forms import PropEditorForm
from includecontents.templatetags.includecontents import Attrs


def build_component_template(
    component: "ComponentInfo",
    props: Dict[str, Any],
    content: str,
    content_blocks: Dict[str, str],
) -> Tuple[str, Dict[str, Any]]:
    """Build the template string and context used for component previews."""
    parts = ["{% load includecontents %}"]

    tag_parts = ["{% includecontents"]
    tag_parts.append(f'"{component.template_name}"')

    sanitized_props: Dict[str, Any] = {}
    if props:
        assignments = []
        for key, value in props.items():
            if re.match(r"^[A-Za-z_][A-Za-z0-9_]*$", key):
                sanitized_props[key] = value
                # For template variable references, we need to quote string values properly
                if isinstance(value, str):
                    # Use literal string values for strings instead of variable references
                    escaped_value = value.replace("'", "\\'")
                    assignments.append(f"{key}='{escaped_value}'")
                else:
                    # For non-strings (booleans, numbers), use variable references
                    assignments.append(f"{key}=preview_props.{key}")
        if assignments:
            tag_parts.append("with")
            tag_parts.extend(assignments)

    tag_parts.append("%}")
    parts.append(" ".join(tag_parts))

    if content:
        parts.append(content)

    for block_name, block_content in content_blocks.items():
        if block_content:
            parts.append(f"{{% contents {block_name} %}}")
            parts.append(block_content)
            parts.append("{% endcontents %}")

    parts.append("{% endincludecontents %}")

    template_str = "\n".join(parts)
    context_data = {
        "preview_props": sanitized_props,
        "attrs": Attrs(),
    }

    return template_str, context_data


@showcase_view
def index(request: HttpRequest) -> HttpResponse:
    """Main showcase index page showing all categories."""
    categories = registry.get_categories()
    recent_components = registry.get_all_components()[:6]  # Show 6 most recent

    return render(request, "showcase/index.html", {
        "categories": categories,
        "recent_components": recent_components,
        "total_components": len(registry.get_all_components()),
        "token_categories": registry.get_token_categories(),
        "tailwind_token_categories": registry.get_tailwind_token_categories()
    })


@showcase_view
def category_view(request: HttpRequest, category: str) -> HttpResponse:
    """View all components in a specific category."""
    # Replace hyphens with spaces for category name
    category_name = category.replace("-", " ").title()
    components = registry.get_components_by_category(category_name)

    if not components:
        # Try without title case
        components = registry.get_components_by_category(category)

    return render(request, "showcase/category.html", {
        "category": category_name,
        "components": components,
        "categories": registry.get_categories(),
        "token_categories": registry.get_token_categories(),
        "tailwind_token_categories": registry.get_tailwind_token_categories()
    })


@showcase_view
def component_view(request: HttpRequest, category: str, name: str) -> HttpResponse:
    """View a specific component with interactive prop editor."""
    component_name = f"{category}:{name}" if category != "root" else name
    component = registry.get_component(component_name)

    if not component:
        # Try to find component by searching
        components = registry.search_components(name)
        if components:
            component = components[0]
        else:
            return redirect("showcase:index")

    # Get initial props (from query params or defaults)
    initial_props = component.get_default_props()
    for key in request.GET:
        if key in component.props:
            initial_props[key] = request.GET[key]

    # Create prop editor form
    form = PropEditorForm(component=component, initial=initial_props)

    # Render component preview with current props
    preview_props = initial_props.copy()
    if request.method == "POST":
        form = PropEditorForm(component=component, data=request.POST)
        if form.is_valid():
            preview_props = form.cleaned_data

    # Prepare examples as JSON-serializable data
    examples_json = []
    for example in component.examples:
        examples_json.append({
            "name": example.name,
            "code": example.code,
            "description": example.description,
            "props": example.props
        })

    # Also prepare individual examples with pre-serialized JSON for template buttons
    examples_with_json = []
    for example in component.examples:
        examples_with_json.append({
            "name": example.name,
            "code": example.code,
            "description": example.description,
            "props": example.props,
            "props_json": json.dumps(example.props)
        })

    # Resolve related components from names to actual component objects
    related_components = []
    for related_name in component.related:
        related_component = registry.get_component(related_name)
        if related_component:
            related_components.append(related_component)
        else:
            # Try to find by searching if exact name doesn't work
            search_results = registry.search_components(related_name)
            if search_results:
                related_components.append(search_results[0])

    return render(request, "showcase/component.html", {
        "component": component,
        "form": form,
        "preview_props": preview_props,
        "preview_props_json": json.dumps(preview_props),
        "examples_json": json.dumps(examples_json),
        "examples_with_json": examples_with_json,
        "related_components": related_components,
        "categories": registry.get_categories(),
        "token_categories": registry.get_token_categories(),
        "tailwind_token_categories": registry.get_tailwind_token_categories()
    })


class ComponentPreviewView(ShowcaseAccessMixin, View):
    """AJAX view for live component preview."""

    def post(self, request: HttpRequest, category: str, name: str) -> JsonResponse:
        """Render component with provided props."""
        component_name = f"{category}:{name}" if category != "root" else name
        component = registry.get_component(component_name)

        if not component:
            return JsonResponse({"error": "Component not found"}, status=404)

        try:
            data = json.loads(request.body)
            props = data.get("props", {})
            content = data.get("content", "")
            content_blocks = data.get("content_blocks", {})

            template_str, extra_context = build_component_template(
                component,
                props,
                content,
                content_blocks,
            )

            # Render template
            template = Template(template_str)
            context = Context({"request": request, **extra_context})
            rendered = template.render(context)

            return JsonResponse({
                "html": rendered,
                "template_code": template_str
            })
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)


@method_decorator(xframe_options_exempt, name="dispatch")
class ComponentIframePreviewView(ShowcaseAccessMixin, View):
    """View for rendering component in an iframe with project CSS."""

    def post(self, request: HttpRequest, category: str, name: str) -> HttpResponse:
        """Render component with provided props in iframe template."""
        component_name = f"{category}:{name}" if category != "root" else name
        component = registry.get_component(component_name)

        if not component:
            return render(request, "showcase/preview.html", {
                "error": "Component not found"
            })

        try:
            # Handle both JSON and form data
            if request.content_type == 'application/json':
                data = json.loads(request.body)
            else:
                # Form data from iframe submission
                data = json.loads(request.POST.get('data', '{}'))

            props = data.get("props", {})
            content = data.get("content", "")
            content_blocks = data.get("content_blocks", {})

            template_str, extra_context = build_component_template(
                component,
                props,
                content,
                content_blocks,
            )

            # Render template
            template = Template(template_str)
            context = Context({"request": request, **extra_context})
            rendered = template.render(context)

            return render(request, "showcase/preview.html", {
                "component_html": rendered
            })
        except Exception as e:
            return render(request, "showcase/preview.html", {
                "error": str(e)
            })

# Token views


@showcase_view
def search_view(request: HttpRequest) -> HttpResponse:
    """Search components."""
    query = request.GET.get("q", "")
    components = []

    if query:
        components = registry.search_components(query)

    return render(request, "showcase/search.html", {
        "query": query,
        "components": components,
        "categories": registry.get_categories(),
        "token_categories": registry.get_token_categories(),
        "tailwind_token_categories": registry.get_tailwind_token_categories()
    })


@showcase_view
def tokens_index(request: HttpRequest) -> HttpResponse:
    """Main design tokens index page showing all token categories."""
    token_categories = registry.get_token_categories()
    all_tokens = registry.get_all_tokens()

    # Count Style Dictionary tokens (JSON source)
    style_dictionary_token_count = sum(1 for token in all_tokens if token.source_type == "json")

    return render(request, "showcase/tokens/index.html", {
        "token_categories": token_categories,
        "total_tokens": len(all_tokens),
        "style_dictionary_token_count": style_dictionary_token_count,
        "categories": registry.get_categories(),
        "tailwind_token_categories": registry.get_tailwind_token_categories()
    })


@showcase_view
def token_category_view(request: HttpRequest, category: str) -> HttpResponse:
    """View all tokens in a specific category."""
    # Replace hyphens with spaces for category name
    category_name = category.replace("-", " ").lower()
    tokens = registry.get_tokens_by_category(category_name)

    if not tokens:
        # Try original category name
        tokens = registry.get_tokens_by_category(category)

    # Count Style Dictionary tokens in this category
    style_dictionary_token_count = sum(1 for token in tokens if token.source_type == "json")

    return render(request, "showcase/tokens/category.html", {
        "category": category_name.title(),
        "category_slug": category,
        "tokens": tokens,
        "style_dictionary_token_count": style_dictionary_token_count,
        "token_categories": registry.get_token_categories(),
        "categories": registry.get_categories(),
        "tailwind_token_categories": registry.get_tailwind_token_categories()
    })


@showcase_view
def tokens_search_view(request: HttpRequest) -> HttpResponse:
    """Search design tokens."""
    query = request.GET.get("q", "")
    tokens = []
    components = []

    if query:
        tokens = registry.search_tokens(query)
        components = registry.search_components(query)

    return render(request, "showcase/tokens/search.html", {
        "query": query,
        "tokens": tokens,
        "components": components,
        "token_categories": registry.get_token_categories(),
        "categories": registry.get_categories(),
        "tailwind_token_categories": registry.get_tailwind_token_categories()
    })


# Tailwind token views

@showcase_view
def tailwind_tokens_index(request: HttpRequest) -> HttpResponse:
    """Main Tailwind design tokens index page."""
    tailwind_token_categories = registry.get_tailwind_token_categories()
    recent_tailwind_tokens = registry.get_all_tailwind_tokens()[:12]  # Show 12 most recent
    all_tailwind_tokens = registry.get_all_tailwind_tokens()

    # Count tokens by source type
    css_token_count = sum(1 for token in all_tailwind_tokens if token.source_type == "css")
    js_token_count = sum(1 for token in all_tailwind_tokens if token.source_type == "js")

    return render(request, "showcase/tailwind/index.html", {
        "tailwind_token_categories": tailwind_token_categories,
        "recent_tailwind_tokens": recent_tailwind_tokens,
        "total_tailwind_tokens": len(all_tailwind_tokens),
        "css_token_count": css_token_count,
        "js_token_count": js_token_count,
        "categories": registry.get_categories(),
        "token_categories": registry.get_token_categories()
    })


@showcase_view
def tailwind_token_category_view(request: HttpRequest, category: str) -> HttpResponse:
    """View all Tailwind tokens in a specific category."""
    # Replace hyphens with spaces for category name
    category_name = category.replace("-", " ").lower()
    tokens = registry.get_tailwind_tokens_by_category(category_name)

    if not tokens:
        # Try original category name
        tokens = registry.get_tailwind_tokens_by_category(category)

    # Count tokens by source type in this category
    css_token_count = sum(1 for token in tokens if token.source_type == "css")
    js_token_count = sum(1 for token in tokens if token.source_type == "js")

    return render(request, "showcase/tailwind/category.html", {
        "category": category_name.title(),
        "category_slug": category,
        "tokens": tokens,
        "css_token_count": css_token_count,
        "js_token_count": js_token_count,
        "tailwind_token_categories": registry.get_tailwind_token_categories(),
        "categories": registry.get_categories(),
        "token_categories": registry.get_token_categories()
    })


@showcase_view
def tailwind_tokens_search_view(request: HttpRequest) -> HttpResponse:
    """Search Tailwind design tokens."""
    query = request.GET.get("q", "")
    tailwind_tokens = []
    components = []

    if query:
        tailwind_tokens = registry.search_tailwind_tokens(query)
        components = registry.search_components(query)

    return render(request, "showcase/tailwind/search.html", {
        "query": query,
        "tailwind_tokens": tailwind_tokens,
        "components": components,
        "tailwind_token_categories": registry.get_tailwind_token_categories(),
        "categories": registry.get_categories(),
        "token_categories": registry.get_token_categories()
    })
