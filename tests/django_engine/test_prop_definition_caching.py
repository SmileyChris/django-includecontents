import time
import pytest
from unittest.mock import patch
from django.template import Context
from includecontents.django.base import Template


def test_prop_definitions_cached_on_template_instance():
    """Test that prop definitions are cached on template instances."""
    # Create a template with a props comment
    template = Template("""{# props variant=primary,secondary size=small,large #}
    <div class="component {{ variant }} {{ size }}">{{ contents }}</div>""")

    # First call should parse and cache the definitions
    props1 = template.get_component_prop_definitions()

    # Second call should return the same cached instance
    props2 = template.get_component_prop_definitions()

    # Should be the exact same object reference (cached)
    assert props1 is props2
    assert props1 is not None
    assert "variant" in props1
    assert "size" in props1


def test_prop_definitions_not_cached_across_template_instances():
    """Test that different template instances have their own prop definition caches."""
    template_source = """{# props variant=primary,secondary size=small,large #}
    <div class="component {{ variant }} {{ size }}">{{ contents }}</div>"""

    template1 = Template(template_source)
    template2 = Template(template_source)

    props1 = template1.get_component_prop_definitions()
    props2 = template2.get_component_prop_definitions()

    # Should be different objects (not shared cache)
    assert props1 is not props2
    # But should have the same content structure
    assert len(props1) == len(props2)
    assert set(props1.keys()) == set(props2.keys())


def test_prop_definitions_parsing_only_happens_once():
    """Test that prop parsing from source only happens once per template."""
    # Test that build_prop_definition is only called once per prop
    template = Template("""{# props variant=primary,secondary size=small,large #}
    <div class="component {{ variant }} {{ size }}">{{ contents }}</div>""")

    with patch(
        "includecontents.django.base.build_prop_definition",
        wraps=lambda spec: type(
            "PropDef",
            (),
            {
                "spec": spec,
                "name": spec.name,
                "required": False,
                "is_enum": lambda: hasattr(spec, "default")
                and "," in str(spec.default),
                "enum_values": str(spec.default).split(",")
                if hasattr(spec, "default") and "," in str(spec.default)
                else None,
                "enum_required": False,
                "clone_default": lambda: spec.default,
            },
        )(),
    ) as mock_build:
        # Multiple calls to get prop definitions
        template.get_component_prop_definitions()
        template.get_component_prop_definitions()
        template.get_component_prop_definitions()

        # build_prop_definition should only be called once per prop (2 props = 2 calls)
        assert mock_build.call_count == 2


def test_component_rendering_uses_cached_prop_definitions():
    """Test that component rendering reuses cached prop definitions efficiently."""
    template = Template("""{# props variant=primary,secondary count= #}
    <div class="component {{ variant }}">Count: {{ count }}</div>""")

    # Render multiple times with different contexts
    contexts = [
        Context({"count": 1}),
        Context({"count": 2}),
        Context({"count": 3}),
    ]

    # First call to get_component_prop_definitions builds the cache
    first_props = template.get_component_prop_definitions()

    # Render multiple times
    for context in contexts:
        template.render(context)
        # Each render should reuse the same cached prop definitions
        current_props = template.get_component_prop_definitions()
        assert current_props is first_props


def test_prop_definition_caching_performance():
    """Test that prop definition caching provides performance benefits."""
    # Create a template with complex prop definitions
    template_source = """{# props variant=primary,secondary,accent size=small,medium,large theme=light,dark alignment=left,center,right display=block,inline,flex #}
    <div class="complex {{ variant }} {{ size }} {{ theme }} {{ alignment }} {{ display }}">
        Complex component content
    </div>"""

    template = Template(template_source)
    Context({})

    # Time getting prop definitions multiple times
    times = []
    for _ in range(100):
        start_time = time.perf_counter()
        template.get_component_prop_definitions()
        times.append(time.perf_counter() - start_time)

    # After the first call, subsequent calls should be much faster (cached)
    first_call_time = times[0]
    avg_cached_time = sum(times[1:]) / len(times[1:]) if len(times) > 1 else 0

    # Cached calls should be significantly faster
    assert avg_cached_time < first_call_time * 0.1  # At least 10x faster


def test_empty_props_comment_returns_none():
    """Test that templates without props comments return None for prop definitions."""
    template = Template("<div>No props here</div>")

    props = template.get_component_prop_definitions()
    assert props is None


def test_props_comment_detection_caching():
    """Test that props comment detection is cached and doesn't reparse."""
    # Template with props comment
    template_with_props = Template("""
    {# props variant=primary,secondary #}
    <div>{{ variant }}</div>
    """)

    # Template without props comment
    template_without_props = Template("<div>No props</div>")

    # Test that props comment detection works
    assert template_with_props.get_component_prop_definitions() is not None
    assert template_without_props.get_component_prop_definitions() is None

    # Multiple calls should return consistent results
    assert template_with_props.get_component_prop_definitions() is not None
    assert template_without_props.get_component_prop_definitions() is None


def test_prop_definition_caching_with_enum_flags():
    """Test that enum flag generation works with cached prop definitions."""
    template = Template("""{# props variant=primary,secondary,accent #}
    <div class="btn {{ variant }}">Multi-value</div>""")

    # Get prop definitions multiple times
    props1 = template.get_component_prop_definitions()
    props2 = template.get_component_prop_definitions()

    # Should be cached
    assert props1 is props2
    assert "variant" in props1

    # Test that enum properties are correctly identified
    variant_prop = props1["variant"]
    assert variant_prop.is_enum()
    assert "primary" in variant_prop.enum_values
    assert "secondary" in variant_prop.enum_values
    assert "accent" in variant_prop.enum_values


@pytest.mark.parametrize(
    "template_source,has_props",
    [
        ("{# props variant=primary,secondary #}\n<div>{{ variant }}</div>", True),
        ("<div>No props comment</div>", False),
        (
            "{# props size=small,large theme=light,dark #}\n<div>Multiple props</div>",
            True,
        ),
    ],
)
def test_caching_behavior_with_different_templates(template_source, has_props):
    """Test caching behavior with various template patterns."""
    template = Template(template_source)

    # Get prop definitions multiple times
    props1 = template.get_component_prop_definitions()
    props2 = template.get_component_prop_definitions()

    if has_props:
        # Should cache and return same reference
        assert props1 is props2
        assert props1 is not None
    else:
        # Should return None consistently
        assert props1 is None
        assert props2 is None


def test_concurrent_access_to_prop_definitions():
    """Test that prop definition caching is thread-safe."""
    import threading
    import queue

    template = Template("""{# props variant=primary,secondary size=small,large #}
    <div class="component {{ variant }} {{ size }}">Content</div>""")
    results = queue.Queue()

    def get_props():
        props = template.get_component_prop_definitions()
        results.put(id(props))  # Store object id to check if same instance

    # Create multiple threads accessing prop definitions
    threads = []
    for _ in range(10):
        thread = threading.Thread(target=get_props)
        threads.append(thread)
        thread.start()

    # Wait for all threads to complete
    for thread in threads:
        thread.join()

    # All threads should get the same cached instance
    prop_ids = []
    while not results.empty():
        prop_ids.append(results.get())

    # All IDs should be the same (same cached object)
    assert len(set(prop_ids)) == 1
    assert len(prop_ids) == 10
