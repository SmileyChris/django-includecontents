from django.http import HttpResponse
from django.test import TestCase, override_settings
from django.urls import path
from django.template.loader import render_to_string


def simple_context_processor(request):
    return {"processor_var": "from_processor"}


def context_processor_view(request):
    # Use render_to_string which properly applies context processors
    content = render_to_string(
        'test_context_processor.html',
        context={},
        request=request
    )
    return HttpResponse(content)

urlpatterns = [
    path('test/', context_processor_view, name='test'),
]


@override_settings(
    ROOT_URLCONF='tests.test_context_processors',
    TEMPLATES=[{
        "BACKEND": "includecontents.django.DjangoTemplates",
        "DIRS": ["tests/templates"],
        "OPTIONS": {
            "context_processors": [
                "tests.test_context_processors.simple_context_processor",
            ],
        },
    }]
)
class ContextProcessorTest(TestCase):
    def test_context_processor_in_html_component(self):
        """Test that context processors are available in HTML components."""
        response = self.client.get('/test/')
        content = response.content.decode()
        
        # The component template should have access to processor_var
        self.assertIn("from_processor", content)
        # It should also render the content we passed
        self.assertIn("<p>Content here</p>", content)


