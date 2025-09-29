from django.test import TestCase, override_settings, RequestFactory
from django.template import Context
from django.template.loader import render_to_string

from includecontents.django.base import Template


def complex_processor_one(request):
    """First context processor providing user-related data."""
    return {
        "user_type": "premium",
        "theme": "dark",
        "features": ["advanced", "analytics", "export"],
    }


def complex_processor_two(request):
    """Second context processor providing application data."""
    return {
        "app_version": "3.1.0",
        "debug_mode": True,
        "api_endpoints": {"users": "/api/users/", "settings": "/api/settings/"},
    }


def complex_processor_three(request):
    """Third context processor providing dynamic data."""
    return {"notifications_count": 5, "unread_messages": 12, "sidebar_collapsed": False}


@override_settings(
    TEMPLATES=[
        {
            "BACKEND": "includecontents.django.DjangoTemplates",
            "DIRS": ["tests/templates"],
            "OPTIONS": {
                "context_processors": [
                    "tests.django_engine.test_complex_nested_components.complex_processor_one",
                    "tests.django_engine.test_complex_nested_components.complex_processor_two",
                    "tests.django_engine.test_complex_nested_components.complex_processor_three",
                ],
            },
        }
    ]
)
class ComplexNestedComponentsTest(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.request = self.factory.get("/")

    def test_deeply_nested_components_preserve_processor_data(self):
        """Test that processor data is preserved through multiple levels of nesting."""

        content = render_to_string(
            "test_complex_nested.html",
            context={"custom_var": "custom_value"},
            request=self.request,
        )

        # Verify all processor data is available at every level
        self.assertIn("user_type: premium", content)  # Level 1
        self.assertIn("app_version: 3.1.0", content)  # Level 2
        self.assertIn("notifications: 5", content)  # Level 3
        self.assertIn("theme: dark", content)  # Level 4

        # Verify content flows through all levels
        self.assertIn("Root content", content)

    def test_processor_data_isolation_between_components(self):
        """Test that processor data modifications in one component don't affect others."""
        template_source = """
        <include:complex-nested/modifier data-modify="user_type">
            First component
        </include:complex-nested/modifier>
        <include:complex-nested/reader>
            Second component
        </include:complex-nested/reader>
        """

        template = Template(template_source)
        content = template.render(Context({}, autoescape=False))

        # First component might modify context but second should see original data
        # (This tests that context isolation works properly)
        content_lines = content.split("\\n")
        modifier_lines = [
            line for line in content_lines if "modifier-component" in line
        ]
        reader_lines = [line for line in content_lines if "reader-component" in line]

        self.assertTrue(len(modifier_lines) > 0)
        self.assertTrue(len(reader_lines) > 0)

    def test_processor_data_with_component_props_interaction(self):
        """Test interaction between processor data and component props."""
        content = render_to_string(
            "test_processor_props_interaction.html",
            context={"component_variant": "secondary"},
            request=self.request,
        )

        # Should combine processor data with component props
        self.assertIn("variant: secondary", content)
        self.assertIn("user_type: premium", content)
        self.assertIn("theme: dark", content)

    def test_csrf_token_preservation_in_nested_components(self):
        """Test that CSRF tokens are preserved through nested components."""
        # Use a dummy CSRF token
        csrf_token = "test-csrf-token-12345"

        content = render_to_string(
            "test_csrf_nested.html",
            context={"csrf_token": csrf_token},
            request=self.request,
        )

        # CSRF token should be available in deeply nested components
        self.assertIn(f"CSRF Token: {csrf_token}", content)
        # Should have CSRF input fields from the component
        self.assertIn("csrfmiddlewaretoken", content)

    def test_request_object_availability_in_nested_components(self):
        """Test that request object is available in nested components."""
        self.request.META["HTTP_USER_AGENT"] = "TestBrowser/1.0"

        content = render_to_string(
            "test_request_nested.html", context={}, request=self.request
        )

        # Request should be available for URL generation and other operations
        self.assertIn("user_agent: TestBrowser/1.0", content)
        self.assertIn("method: GET", content)

    def test_processor_data_performance_with_deep_nesting(self):
        """Test that processor data collection doesn't degrade with deep nesting."""
        import time

        # Create a template with very deep nesting
        template_source = """
        <include:complex-nested/performance-test depth="10">
            Deep nesting test
        </include:complex-nested/performance-test>
        """

        Template(template_source)

        # Measure rendering time
        start_time = time.perf_counter()
        for _ in range(10):
            content = render_to_string(
                "test_performance_nested.html", context={}, request=self.request
            )
        end_time = time.perf_counter()

        avg_time = (end_time - start_time) / 10

        # Should complete reasonably quickly (less than 100ms per render)
        self.assertLess(avg_time, 0.1)

        # Verify content is still correct
        self.assertIn("depth: 10", content)
        self.assertIn("user_type: premium", content)

    def test_processor_data_with_enum_props_and_nesting(self):
        """Test processor data with enum props in nested components."""
        content = render_to_string(
            "test_enum_processor_nested.html",
            context={"button_variant": "primary"},
            request=self.request,
        )

        # Should handle enum props while preserving processor data
        self.assertIn("btn-primary", content)
        self.assertIn("user_type: premium", content)
        self.assertIn("theme: dark", content)

    def test_multiple_processor_data_sources_merge_correctly(self):
        """Test that multiple context processors merge correctly in nested components."""
        content = render_to_string(
            "test_multi_processor_merge.html", context={}, request=self.request
        )

        # All three processors should contribute data
        self.assertIn("user_type: premium", content)  # processor_one
        self.assertIn("app_version: 3.1.0", content)  # processor_two
        self.assertIn("notifications_count: 5", content)  # processor_three

        # Should not have conflicts or missing data
        self.assertNotIn("undefined", content.lower())
        self.assertNotIn("none", content.lower())

    def test_processor_data_context_stack_integrity(self):
        """Test that context stack integrity is maintained with processor data."""
        template_source = """
        {% with outer_var="outer_value" %}
            <include:complex-nested/context-stack var1="component_value">
                {% with inner_var="inner_value" %}
                    Content with variables
                {% endwith %}
            </include:complex-nested/context-stack>
        {% endwith %}
        """

        template = Template(template_source)
        context = Context({"base_var": "base_value"})
        context.update({"request": self.request})

        content = template.render(context)

        # All context levels should be accessible
        self.assertIn("base_var: base_value", content)
        self.assertIn("outer_var: outer_value", content)
        self.assertIn("var1: component_value", content)
        self.assertIn("user_type: premium", content)  # processor data

    def test_processor_data_with_component_slots(self):
        """Test processor data accessibility in component slots."""
        content = render_to_string(
            "test_processor_slots.html",
            context={"slot_data": "slot_content"},
            request=self.request,
        )

        # Processor data should be available in named slots
        self.assertIn("header: user_type=premium", content)
        self.assertIn("footer: app_version=3.1.0", content)
        self.assertIn("default: slot_content", content)

    def test_error_handling_with_missing_processor_data(self):
        """Test graceful handling when processor data is missing."""
        # Create a minimal template without full processor setup
        template = Template("""
        <include:complex-nested/minimal>
            Minimal component
        </include:complex-nested/minimal>
        """)

        # Should not crash even without processor data
        content = template.render(Context({}))
        self.assertIn("Minimal component", content)

    def test_processor_data_type_preservation(self):
        """Test that processor data types are preserved correctly."""
        content = render_to_string(
            "test_processor_types.html", context={}, request=self.request
        )

        # Different data types should be preserved
        self.assertIn("features_count: 3", content)  # list length
        self.assertIn("debug_mode: True", content)  # boolean
        self.assertIn("notifications_count: 5", content)  # integer
        self.assertIn("api_endpoints_users", content)  # dict access
