"""
Tests for registry introspection helpers and debugging features.

This module tests the registry helper functions that provide introspection
and debugging capabilities for the component props system.
"""

from dataclasses import dataclass
from unittest.mock import patch


from includecontents.shared.typed_props import (
    component,
    list_registered_components,
    resolve_props_class_for,
    clear_registry,
    get_props_class,
)


class TestRegistryIntrospection:
    """Test registry introspection and helper functions."""

    def setup_method(self):
        """Clear registry before each test."""
        clear_registry()

    def test_clear_registry(self):
        """Test that clear_registry removes all registered components."""

        @component("components/test1.html")
        @dataclass
        class Test1Props:
            title: str

        @component("components/test2.html")
        @dataclass
        class Test2Props:
            name: str

        # Verify components are registered
        assert len(list_registered_components()) == 2

        # Clear and verify empty
        clear_registry()
        assert list_registered_components() == []

    def test_list_registered_components_empty(self):
        """Test list_registered_components with empty registry."""
        result = list_registered_components()
        assert result == []
        assert isinstance(result, list)

    def test_list_registered_components_with_data(self):
        """Test list_registered_components returns all registered paths."""

        @component("components/card.html")
        @dataclass
        class CardProps:
            title: str

        @component("components/forms/input.html")
        @dataclass
        class InputProps:
            name: str
            type: str = "text"

        @component("shared/header.html")
        @dataclass
        class HeaderProps:
            brand: str

        components = list_registered_components()
        assert len(components) == 3
        assert "components/card.html" in components
        assert "components/forms/input.html" in components
        assert "shared/header.html" in components

    def test_resolve_props_class_for_exact_match(self):
        """Test resolve_props_class_for with exact path match."""

        @component("components/exact.html")
        @dataclass
        class ExactProps:
            value: str

        result = resolve_props_class_for("components/exact.html")
        assert result is ExactProps

    def test_resolve_props_class_for_absolute_to_relative(self):
        """Test resolve_props_class_for converts absolute paths to relative."""

        @component("components/button.html")
        @dataclass
        class ButtonProps:
            text: str

        # Should find the component by stripping leading slash
        result = resolve_props_class_for("/components/button.html")
        assert result is ButtonProps

    def test_resolve_props_class_for_templates_prefix(self):
        """Test resolve_props_class_for handles templates/ prefix."""

        @component("components/nav.html")
        @dataclass
        class NavProps:
            items: list

        # Should find the component by removing templates/ prefix
        result = resolve_props_class_for("/path/to/templates/components/nav.html")
        assert result is NavProps

        result = resolve_props_class_for("templates/components/nav.html")
        assert result is NavProps

    def test_resolve_props_class_for_complex_absolute_path(self):
        """Test resolve_props_class_for with complex absolute paths."""

        @component("components/widget.html")
        @dataclass
        class WidgetProps:
            id: str

        # Should handle various absolute path formats
        test_paths = [
            "/home/project/templates/components/widget.html",
            "/usr/src/app/myapp/templates/components/widget.html",
            "C:\\project\\templates\\components\\widget.html",  # Windows path
        ]

        for path in test_paths:
            result = resolve_props_class_for(path)
            assert result is WidgetProps, f"Failed to resolve: {path}"

    def test_resolve_props_class_for_not_found(self):
        """Test resolve_props_class_for returns None for unregistered paths."""

        @component("components/existing.html")
        @dataclass
        class ExistingProps:
            data: str

        # Should return None for non-existent components
        assert resolve_props_class_for("components/missing.html") is None
        assert (
            resolve_props_class_for("/path/to/templates/components/missing.html")
            is None
        )
        assert resolve_props_class_for("totally/different/path.html") is None

    def test_resolve_props_class_for_edge_cases(self):
        """Test resolve_props_class_for with edge cases."""

        @component("simple.html")
        @dataclass
        class SimpleProps:
            text: str

        # Should handle simple template names
        assert resolve_props_class_for("simple.html") is SimpleProps
        assert resolve_props_class_for("/simple.html") is SimpleProps
        assert resolve_props_class_for("templates/simple.html") is SimpleProps

        # Should handle empty/None paths gracefully
        assert resolve_props_class_for("") is None
        assert resolve_props_class_for("/") is None


class TestRegistryCollisionWarnings:
    """Test registry collision detection and warnings."""

    def setup_method(self):
        """Clear registry before each test."""
        clear_registry()

    def test_registry_collision_warning(self):
        """Test that registry collisions generate warnings."""
        with patch("includecontents.shared.typed_props.logger") as mock_logger:

            @component("components/collision.html")
            @dataclass
            class FirstProps:
                first: str

            # No warning on first registration
            mock_logger.warning.assert_not_called()

            @component("components/collision.html")
            @dataclass
            class SecondProps:
                second: str

            # Should warn on collision
            mock_logger.warning.assert_called_once()
            call_args = mock_logger.warning.call_args[0]
            assert "already registered" in call_args[0]
            assert "components/collision.html" in call_args[1]
            assert "FirstProps" in call_args[2]
            assert "SecondProps" in call_args[3]

    def test_registry_collision_keeps_first(self):
        """Test that registry collisions keep the first registration."""

        @component("components/keeper.html")
        @dataclass
        class KeepProps:
            keep: str

        @component("components/keeper.html")
        @dataclass
        class DiscardProps:
            discard: str

        # Should keep the first registration
        result = get_props_class("components/keeper.html")
        assert result is KeepProps
        assert result is not DiscardProps

    def test_multiple_collisions(self):
        """Test multiple collisions on the same path."""
        with patch("includecontents.shared.typed_props.logger") as mock_logger:

            @component("components/multi.html")
            @dataclass
            class First:
                first: str

            @component("components/multi.html")
            @dataclass
            class Second:
                second: str

            @component("components/multi.html")
            @dataclass
            class Third:
                third: str

            # Should warn twice (for second and third registrations)
            assert mock_logger.warning.call_count == 2

            # Should still keep the first
            result = get_props_class("components/multi.html")
            assert result is First


class TestRegistryThreadSafety:
    """Test registry thread safety considerations."""

    def setup_method(self):
        """Clear registry before each test."""
        clear_registry()

    def test_registry_read_operations_safe(self):
        """Test that read operations are safe and don't modify state."""

        @component("components/readonly.html")
        @dataclass
        class ReadOnlyProps:
            data: str

        initial_components = list_registered_components()
        initial_count = len(initial_components)

        # Multiple read operations shouldn't change registry
        for _ in range(10):
            list_registered_components()
            get_props_class("components/readonly.html")
            resolve_props_class_for("components/readonly.html")

        final_components = list_registered_components()
        assert len(final_components) == initial_count
        assert set(final_components) == set(initial_components)

    def test_registry_immutability_from_list(self):
        """Test that modifying the returned list doesn't affect registry."""

        @component("components/immutable.html")
        @dataclass
        class ImmutableProps:
            value: str

        components = list_registered_components()
        original_length = len(components)

        # Modifying returned list shouldn't affect registry
        components.append("fake/component.html")
        components.clear()

        # Registry should be unchanged
        new_components = list_registered_components()
        assert len(new_components) == original_length
        assert "components/immutable.html" in new_components
        assert "fake/component.html" not in new_components


class TestRegistryDebugging:
    """Test registry debugging and logging features."""

    def setup_method(self):
        """Clear registry before each test."""
        clear_registry()

    def test_debug_logging_captures_registry_state(self):
        """Test that debug logging provides useful registry information."""

        @component("components/debug1.html")
        @dataclass
        class Debug1Props:
            value1: str

        @component("components/debug2.html")
        @dataclass
        class Debug2Props:
            value2: str

        components = list_registered_components()

        # Should have useful debugging information
        assert len(components) == 2
        assert all("components/" in comp for comp in components)
        assert all(".html" in comp for comp in components)

    def test_empty_registry_debugging(self):
        """Test debugging with empty registry."""
        components = list_registered_components()
        assert components == []

        # Should handle empty registry gracefully
        result = resolve_props_class_for("any/path.html")
        assert result is None
