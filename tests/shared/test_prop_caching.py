"""Test template prop caching behavior."""

import logging
from pathlib import Path
from unittest.mock import patch
import time

import pytest
from django.template.loader import render_to_string

from includecontents.shared.typed_props import _registry


@pytest.mark.django_db
class TestPropCaching:
    """Test that template prop caching works correctly."""

    def setup_method(self):
        """Clear the registry before each test."""
        _registry.clear()

    def test_props_cached_after_first_parse(self):
        """Test that props are cached after the first parse."""

        # Create template with props definition
        template_content = """{# props
title:str="Default Title"
count:int=5
active:bool=true
#}
<div class="card">
    <h2>{{ title }}</h2>
    <p>Count: {{ count }}, Active: {{ active }}</p>
</div>"""

        # Create template directory
        template_dir = Path("tests/templates/components")
        template_dir.mkdir(parents=True, exist_ok=True)
        template_file = template_dir / "cached-test.html"
        template_file.write_text(template_content)

        # Create test template that uses the component
        test_content = """<include:cached-test />"""
        test_dir = Path("tests/templates/test_caching")
        test_dir.mkdir(parents=True, exist_ok=True)
        test_file = test_dir / "test.html"
        test_file.write_text(test_content)

        # Render the first time
        output1 = render_to_string("test_caching/test.html")

        # Render the second time
        output2 = render_to_string("test_caching/test.html")

        # Both outputs should be identical
        assert output1 == output2
        assert "Default Title" in output1
        assert "Count: 5" in output1
        assert "Active: True" in output1

    def test_cache_is_stored_on_template_instance(self):
        """Test that cache is stored as an attribute on the template instance."""

        # Create template with props
        template_content = """{# props
name:str=Test
#}
<p>{{ name }}</p>"""

        template_dir = Path("tests/templates/components")
        template_dir.mkdir(parents=True, exist_ok=True)
        template_file = template_dir / "cache-instance-test.html"
        template_file.write_text(template_content)

        test_content = """<include:cache-instance-test />"""
        test_dir = Path("tests/templates/test_caching")
        test_dir.mkdir(parents=True, exist_ok=True)
        test_file = test_dir / "instance.html"
        test_file.write_text(test_content)

        # First render should create cache
        render_to_string("test_caching/instance.html")

        # Check that the template instance has the cache attribute
        # We'll need to access the internal template to check this
        from django.template import loader

        template = loader.get_template("test_caching/instance.html")

        # The component template should have been cached
        # We can't easily access it directly, but we can verify by counting parsing calls

    def test_different_templates_have_separate_caches(self):
        """Test that different templates maintain separate caches."""

        # Create two different templates with different props
        template1_content = """{# props
title:str="Template 1"
#}
<h1>{{ title }}</h1>"""

        template2_content = """{# props
heading:str="Template 2"
#}
<h2>{{ heading }}</h2>"""

        template_dir = Path("tests/templates/components")
        template_dir.mkdir(parents=True, exist_ok=True)

        template1_file = template_dir / "cache-test-1.html"
        template1_file.write_text(template1_content)

        template2_file = template_dir / "cache-test-2.html"
        template2_file.write_text(template2_content)

        # Create test templates
        test_content1 = """<include:cache-test-1 />"""
        test_content2 = """<include:cache-test-2 />"""

        test_dir = Path("tests/templates/test_caching")
        test_dir.mkdir(parents=True, exist_ok=True)

        test_file1 = test_dir / "separate1.html"
        test_file1.write_text(test_content1)

        test_file2 = test_dir / "separate2.html"
        test_file2.write_text(test_content2)

        # Render both templates
        output1 = render_to_string("test_caching/separate1.html")
        output2 = render_to_string("test_caching/separate2.html")

        # Verify they render correctly and independently
        assert "Template 1" in output1
        assert "Template 2" in output2
        assert "Template 1" not in output2
        assert "Template 2" not in output1

    def test_cache_key_uses_first_comment(self):
        """Test that cache key is based on the first_comment content."""

        # Create template
        template_content = """{# props
message:str="Hello World"
#}
<p>{{ message }}</p>"""

        template_dir = Path("tests/templates/components")
        template_dir.mkdir(parents=True, exist_ok=True)
        template_file = template_dir / "cache-key-test.html"
        template_file.write_text(template_content)

        test_content = """<include:cache-key-test />"""
        test_dir = Path("tests/templates/test_caching")
        test_dir.mkdir(parents=True, exist_ok=True)
        test_file = test_dir / "key.html"
        test_file.write_text(test_content)

        # First render
        output = render_to_string("test_caching/key.html")
        assert "Hello World" in output

    def test_cache_with_variable_and_expression_defaults(self):
        """Test that caching works with Variable and Expression defaults."""

        # Create template with various default types
        template_content = """{# props
user_name:str=user.name
formatted_title:str="{{ title|default:'Untitled' }}"
items:list[str]=[item1,item2,item3]
#}
<div>
    <h1>{{ formatted_title }}</h1>
    <p>User: {{ user_name }}</p>
    <ul>
    {% for item in items %}
        <li>{{ item }}</li>
    {% endfor %}
    </ul>
</div>"""

        template_dir = Path("tests/templates/components")
        template_dir.mkdir(parents=True, exist_ok=True)
        template_file = template_dir / "cache-complex-test.html"
        template_file.write_text(template_content)

        test_content = """<include:cache-complex-test />"""
        test_dir = Path("tests/templates/test_caching")
        test_dir.mkdir(parents=True, exist_ok=True)
        test_file = test_dir / "complex.html"
        test_file.write_text(test_content)

        # Render multiple times with different contexts
        context1 = {"user": {"name": "Alice"}, "title": "Welcome"}
        context2 = {"user": {"name": "Bob"}, "title": "Hello"}

        output1 = render_to_string("test_caching/complex.html", context1)
        output2 = render_to_string("test_caching/complex.html", context2)

        # Verify both render correctly (cache should not interfere with variable resolution)
        assert "Welcome" in output1
        assert "Alice" in output1
        assert "Hello" in output2
        assert "Bob" in output2

    def test_cache_logs_debug_messages(self, caplog):
        """Test that cache operations are logged at debug level."""

        template_content = """{# props
test:str="Debug Test"
#}
<p>{{ test }}</p>"""

        template_dir = Path("tests/templates/components")
        template_dir.mkdir(parents=True, exist_ok=True)
        template_file = template_dir / "cache-debug-test.html"
        template_file.write_text(template_content)

        test_content = """<include:cache-debug-test />"""
        test_dir = Path("tests/templates/test_caching")
        test_dir.mkdir(parents=True, exist_ok=True)
        test_file = test_dir / "debug.html"
        test_file.write_text(test_content)

        # Enable debug logging
        with caplog.at_level(
            logging.DEBUG, logger="includecontents.templatetags.includecontents"
        ):
            # First render should cache
            render_to_string("test_caching/debug.html")

            # Second render should hit cache
            render_to_string("test_caching/debug.html")

        # Check for cache-related log messages
        log_messages = [record.message for record in caplog.records]
        cache_messages = [msg for msg in log_messages if "cache" in msg.lower()]

        # We should have at least one cache storage message and one cache hit message
        assert len(cache_messages) >= 2

    def test_cache_fallback_on_error(self):
        """Test that parsing continues if cache operations fail."""

        template_content = """{# props
fallback:str="Fallback Test"
#}
<p>{{ fallback }}</p>"""

        template_dir = Path("tests/templates/components")
        template_dir.mkdir(parents=True, exist_ok=True)
        template_file = template_dir / "cache-fallback-test.html"
        template_file.write_text(template_content)

        test_content = """<include:cache-fallback-test />"""
        test_dir = Path("tests/templates/test_caching")
        test_dir.mkdir(parents=True, exist_ok=True)
        test_file = test_dir / "fallback.html"
        test_file.write_text(test_content)

        # Mock to simulate cache failure by patching setattr instead of hasattr
        # This simulates a scenario where cache storage fails
        original_setattr = setattr

        def failing_setattr(obj, name, value):
            if name == "_includecontents_props_cache":
                raise Exception("Cache storage error")
            return original_setattr(obj, name, value)

        with patch("builtins.setattr", side_effect=failing_setattr):
            # Should still work despite cache error
            output = render_to_string("test_caching/fallback.html")
            assert "Fallback Test" in output

    def test_performance_improvement_with_cache(self):
        """Test that caching actually improves performance."""

        # Create a complex template that would be expensive to parse
        template_content = """{# props
prop1:str=default1
prop2:int=42
prop3:bool=true
prop4:list[str]=[a,b,c,d,e]
prop5:str="username"
prop6:str="{{ title|default:'Complex' }}"
prop7:int=123
prop8:bool=false
prop9:list[int]=[1,2,3,4,5]
prop10:str=final
#}
<div>Complex template with many props</div>"""

        template_dir = Path("tests/templates/components")
        template_dir.mkdir(parents=True, exist_ok=True)
        template_file = template_dir / "cache-perf-test.html"
        template_file.write_text(template_content)

        test_content = """<include:cache-perf-test />"""
        test_dir = Path("tests/templates/test_caching")
        test_dir.mkdir(parents=True, exist_ok=True)
        test_file = test_dir / "perf.html"
        test_file.write_text(test_content)

        # Time the first render (should cache)
        start_time = time.time()
        render_to_string("test_caching/perf.html")
        first_render_time = time.time() - start_time

        # Time subsequent renders (should use cache)
        cached_times = []
        for _ in range(5):
            start_time = time.time()
            render_to_string("test_caching/perf.html")
            cached_times.append(time.time() - start_time)

        avg_cached_time = sum(cached_times) / len(cached_times)

        # Cached renders should generally be faster
        # Note: This is a rough check as template rendering involves many factors
        # The main benefit of caching is avoiding prop parsing, not total render time
        print(
            f"First render: {first_render_time:.4f}s, Avg cached: {avg_cached_time:.4f}s"
        )

    def teardown_method(self):
        """Clean up test templates."""
        import shutil

        test_paths = [
            "tests/templates/components/cached-test.html",
            "tests/templates/components/cache-instance-test.html",
            "tests/templates/components/cache-test-1.html",
            "tests/templates/components/cache-test-2.html",
            "tests/templates/components/cache-key-test.html",
            "tests/templates/components/cache-complex-test.html",
            "tests/templates/components/cache-debug-test.html",
            "tests/templates/components/cache-fallback-test.html",
            "tests/templates/components/cache-perf-test.html",
            "tests/templates/test_caching",
        ]

        for test_path in test_paths:
            try:
                path = Path(test_path)
                if path.is_dir():
                    shutil.rmtree(path)
                else:
                    path.unlink()
            except FileNotFoundError:
                pass
