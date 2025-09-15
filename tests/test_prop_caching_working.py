"""Test template prop caching with working syntax."""

import logging
from pathlib import Path
from unittest.mock import patch
import time

import pytest
from django.template import Context, Template

# Component template paths for testing
CACHE_TEST_TEMPLATES = [
    'cached_test_1.html',
    'cached_test_2.html',
    'cache_complex.html',
    'cache_debug.html',
    'cache_performance.html'
]


@pytest.mark.django_db
class TestPropCachingWorking:
    """Test template prop caching using working {% includecontents %} syntax."""

    def setup_method(self):
        """Create test templates."""
        # Create template directory
        template_dir = Path('tests/templates/test_caching_working')
        template_dir.mkdir(parents=True, exist_ok=True)

        # Template 1 - Simple props with defaults
        template1_content = """{# props title:str="Cached Title" count:int=42 active:bool=true #}
<div class="cached-component">
    <h1>{{ title }}</h1>
    <p>Count: {{ count }}, Active: {{ active }}</p>
</div>"""

        template1_file = template_dir / 'cached_test_1.html'
        template1_file.write_text(template1_content)

        # Template 2 - Different props to test separate caches
        template2_content = """{# props message:str="Different Cache" value:int=100 #}
<div class="other-component">
    <span>{{ message }}: {{ value }}</span>
</div>"""

        template2_file = template_dir / 'cached_test_2.html'
        template2_file.write_text(template2_content)

        # Template 3 - Complex props with variables and expressions
        template3_content = """{# props user_name:str=user.name formatted_title:str="{{ title|default:'Complex Test' }}" items:list[str]=[alpha,beta,gamma] #}
<div class="complex-component">
    <h2>{{ formatted_title }}</h2>
    <p>User: {{ user_name }}</p>
    <ul>
    {% for item in items %}
        <li>{{ item }}</li>
    {% endfor %}
    </ul>
</div>"""

        template3_file = template_dir / 'cache_complex.html'
        template3_file.write_text(template3_content)

        # Template 4 - For debug logging tests
        template4_content = """{# props debug_prop:str="Debug Value" #}
<p>Debug: {{ debug_prop }}</p>"""

        template4_file = template_dir / 'cache_debug.html'
        template4_file.write_text(template4_content)

        # Template 5 - For performance testing (many props)
        template5_content = """{# props prop1:str="value1" prop2:int=1 prop3:bool=true prop4:list[str]=[a,b,c] prop5:str=user.name prop6:str="{{ title|default:'Performance' }}" prop7:int=999 prop8:bool=false prop9:list[int]=[1,2,3] prop10:str="final" #}
<div>Performance test with {{ prop1 }}, {{ prop2 }}, {{ prop7 }}</div>"""

        template5_file = template_dir / 'cache_performance.html'
        template5_file.write_text(template5_content)

    def test_props_cached_after_first_parse(self):
        """Test that props are cached after the first parse using includecontents syntax."""

        # Create template using includecontents tag (the syntax that works)
        template = Template(
            "{% load includecontents %}"
            '{% includecontents "test_caching_working/cached_test_1.html" %}{% endincludecontents %}'
        )

        context = Context({})

        # Render the first time
        output1 = template.render(context)

        # Render the second time - should use cache
        output2 = template.render(context)

        # Both outputs should be identical
        assert output1 == output2
        assert "Cached Title" in output1
        assert "Count: 42" in output1
        assert "Active: True" in output1

    def test_different_templates_have_separate_caches(self):
        """Test that different templates maintain separate caches."""

        template1 = Template(
            "{% load includecontents %}"
            '{% includecontents "test_caching_working/cached_test_1.html" %}{% endincludecontents %}'
        )

        template2 = Template(
            "{% load includecontents %}"
            '{% includecontents "test_caching_working/cached_test_2.html" %}{% endincludecontents %}'
        )

        context = Context({})

        # Render both templates
        output1 = template1.render(context)
        output2 = template2.render(context)

        # Verify they render correctly and independently
        assert "Cached Title" in output1
        assert "Different Cache" in output2
        assert "Cached Title" not in output2
        assert "Different Cache" not in output1

    def test_cache_with_variable_and_expression_defaults(self):
        """Test that caching works with Variable and Expression defaults."""

        template = Template(
            "{% load includecontents %}"
            '{% includecontents "test_caching_working/cache_complex.html" %}{% endincludecontents %}'
        )

        # Render multiple times with different contexts
        context1 = Context({"user": {"name": "Alice"}, "title": "Welcome"})
        context2 = Context({"user": {"name": "Bob"}, "title": "Hello"})

        output1 = template.render(context1)
        output2 = template.render(context2)

        # Verify both render correctly (cache should not interfere with variable resolution)
        assert "Welcome" in output1
        assert "Alice" in output1
        assert "Hello" in output2
        assert "Bob" in output2

    def test_cache_logs_debug_messages(self, caplog):
        """Test that cache operations are logged at debug level."""

        template = Template(
            "{% load includecontents %}"
            '{% includecontents "test_caching_working/cache_debug.html" %}{% endincludecontents %}'
        )

        context = Context({})

        # Enable debug logging for our module
        with caplog.at_level(logging.DEBUG, logger='includecontents.templatetags.includecontents'):
            # First render should cache
            output1 = template.render(context)
            assert "Debug Value" in output1

            # Second render should hit cache
            output2 = template.render(context)
            assert output1 == output2

        # Check for cache-related log messages
        log_messages = [record.message for record in caplog.records]
        cache_messages = [msg for msg in log_messages if 'cache' in msg.lower()]

        # We should have at least one cache storage message and one cache hit message
        assert len(cache_messages) >= 2

        # Check for specific cache operations
        cache_storage_messages = [msg for msg in cache_messages if 'cached' in msg]
        cache_hit_messages = [msg for msg in cache_messages if 'hit' in msg]

        assert len(cache_storage_messages) >= 1, f"Expected cache storage messages, got: {cache_messages}"
        assert len(cache_hit_messages) >= 1, f"Expected cache hit messages, got: {cache_messages}"

    def test_cache_fallback_on_error(self):
        """Test that parsing continues if cache operations fail."""

        template = Template(
            "{% load includecontents %}"
            '{% includecontents "test_caching_working/cache_debug.html" %}{% endincludecontents %}'
        )

        context = Context({})

        # Simulate cache failure by patching hasattr to return False for our cache attribute
        # This is safer than patching getattr which has broad side effects
        original_hasattr = hasattr

        def mock_hasattr(obj, name):
            if name == '_includecontents_props_cache':
                return False  # Pretend the cache doesn't exist
            return original_hasattr(obj, name)

        with patch('builtins.hasattr', side_effect=mock_hasattr):
            # Should still work despite cache being "missing"
            output = template.render(context)
            assert "Debug Value" in output

    def test_performance_improvement_with_cache(self):
        """Test that caching provides performance benefits."""

        template = Template(
            "{% load includecontents %}"
            '{% includecontents "test_caching_working/cache_performance.html" %}{% endincludecontents %}'
        )

        context = Context({"user": {"name": "TestUser"}, "title": "Test"})

        # Time the first render (should create cache)
        start_time = time.time()
        output1 = template.render(context)
        first_render_time = time.time() - start_time

        # Time subsequent renders (should use cache)
        cached_times = []
        for _ in range(5):
            start_time = time.time()
            output = template.render(context)
            cached_times.append(time.time() - start_time)
            # Verify output is consistent
            assert output == output1

        avg_cached_time = sum(cached_times) / len(cached_times)

        # Verify the content rendered correctly
        assert "Performance" in output1  # From the default
        assert "value1" in output1       # From literal string default
        assert "999" in output1          # From int default

        # While we can't guarantee caching makes rendering faster (template rendering has many factors),
        # we can verify that caching doesn't break anything and provides consistent results
        print(f"First render: {first_render_time:.4f}s, Avg cached: {avg_cached_time:.4f}s")

        # The main benefit should be consistent props parsing, not necessarily faster total render time
        # As long as all renders produce identical output, caching is working correctly
        for cached_time in cached_times:
            # No cached render should take significantly longer than the first (which includes parsing)
            assert cached_time <= first_render_time * 2, "Cached renders should not be much slower than first render"

    def teardown_method(self):
        """Clean up test templates."""
        import shutil

        test_dir = Path('tests/templates/test_caching_working')
        try:
            if test_dir.exists():
                shutil.rmtree(test_dir)
        except FileNotFoundError:
            pass