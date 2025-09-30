"""Test undefined variable handling in Jinja components."""

from __future__ import annotations

from jinja2 import DebugUndefined, DictLoader, Environment, StrictUndefined

from includecontents.jinja2.extension import IncludeContentsExtension

from ._helpers import render_component


class TestUndefinedVariables:
    """Test how undefined variables are handled in component templates."""

    def test_undefined_variables_render_as_empty_strings(self) -> None:
        """Test that undefined variables in components render as empty strings."""
        # With the fix, undefined variables should render as empty strings
        # regardless of the main environment's undefined behavior
        output, _ = render_component(
            '<include:test_undefined defined_var="hello" />',
            use=["test_undefined"],
        )

        print(f"DEBUG: Output is: {repr(output)}")

        # After the fix: undefined variables render as empty strings
        assert "{{ undefined_var }}" not in output  # No literal rendering
        assert "{{ another_undefined }}" not in output  # No literal rendering
        assert "hello" in output  # defined_var should work fine
        assert "Component with undefined variables:" in output

    def test_undefined_variables_with_debug_undefined(self) -> None:
        """Test that components use standard Undefined even when main env uses DebugUndefined."""
        # This tests that the fix prevents literal rendering in components
        templates = {
            "page.html": '<include:test_undefined defined_var="hello" />',
            "components/test_undefined.html": """
{# props defined_var #}
Component with undefined variables:
{{ defined_var }}
{{ undefined_var }}
{{ another_undefined }}
""".strip(),
        }

        env = Environment(
            loader=DictLoader(templates),
            extensions=[IncludeContentsExtension],
            undefined=DebugUndefined,  # Main environment uses DebugUndefined
        )

        output = env.get_template("page.html").render(defined_var="hello")
        print(f"DEBUG: Component output with DebugUndefined env: {repr(output)}")

        # Components should use standard Undefined, not DebugUndefined
        # So undefined variables render as empty strings, not literal {{ var }}
        assert "{{ undefined_var }}" not in output  # No literal rendering
        assert "{{ another_undefined }}" not in output  # No literal rendering
        assert "hello" in output  # Defined variables still work
        assert "Component with undefined variables:" in output

    def test_undefined_variables_with_strict_undefined(self) -> None:
        """Test that components use standard Undefined even when main env uses StrictUndefined."""
        templates = {
            "page.html": '<include:test_undefined defined_var="hello" />',
            "components/test_undefined.html": """
{# props defined_var #}
Component with undefined variables:
{{ defined_var }}
{{ undefined_var }}
{{ another_undefined }}
""".strip(),
        }

        env = Environment(
            loader=DictLoader(templates),
            extensions=[IncludeContentsExtension],
            undefined=StrictUndefined,  # Main environment uses StrictUndefined
        )

        # Components should NOT raise errors, they use standard Undefined
        output = env.get_template("page.html").render(defined_var="hello")
        print(f"DEBUG: StrictUndefined env output: {repr(output)}")

        # Components should render undefined variables as empty strings
        assert "hello" in output  # Defined variables work
        assert "Component with undefined variables:" in output
        # Undefined variables render as empty strings, not errors

    def test_main_templates_still_use_debug_undefined(self) -> None:
        """Test that non-component templates still use the main environment's undefined behavior."""
        templates = {
            "page.html": """
Main template with undefined variable:
{{ undefined_main_var }}
<include:test_undefined defined_var="hello" />
""".strip(),
            "components/test_undefined.html": """
{# props defined_var #}
Component: {{ defined_var }} {{ undefined_component_var }}
""".strip(),
        }

        env = Environment(
            loader=DictLoader(templates),
            extensions=[IncludeContentsExtension],
            undefined=DebugUndefined,
        )

        output = env.get_template("page.html").render(defined_var="hello")
        print(f"DEBUG: Mixed template output: {repr(output)}")

        # Main template should still show DebugUndefined behavior
        assert "{{ undefined_main_var }}" in output  # Main template uses DebugUndefined

        # But component should use standard Undefined
        assert (
            "{{ undefined_component_var }}" not in output
        )  # Component uses standard Undefined
        assert "Component: hello" in output  # Component works correctly

    def test_undefined_variables_with_context_isolation_disabled(self) -> None:
        """Test what happens when context isolation is disabled."""
        templates = {
            "page.html": '<include:test_undefined defined_var="hello" />',
            "components/test_undefined.html": """
{# props defined_var #}
Component with undefined variables:
{{ defined_var }}
{{ undefined_var }}
{{ another_undefined }}
{{ parent_var }}
""".strip(),
        }

        env = Environment(
            loader=DictLoader(templates),
            extensions=[IncludeContentsExtension],
            undefined=DebugUndefined,
        )

        # Disable context isolation on the extension
        extension = next(
            ext
            for ext in env.extensions.values()
            if isinstance(ext, IncludeContentsExtension)
        )
        extension.use_context_isolation = False

        # Render with parent variables that should NOT be accessible to components
        output = env.get_template("page.html").render(
            defined_var="hello",
            undefined_var="parent_undefined",
            another_undefined="parent_another",
            parent_var="parent_value",
        )
        print(f"DEBUG: No isolation output: {repr(output)}")

        # With context isolation disabled, parent variables leak through
        assert "hello" in output
        assert "parent_undefined" in output  # This shouldn't happen with isolation
        assert "parent_another" in output  # This shouldn't happen with isolation
        assert "parent_value" in output  # This shouldn't happen with isolation

    def test_undefined_variables_with_context_isolation_enabled(self) -> None:
        """Test that context isolation prevents parent variables from leaking."""
        templates = {
            "page.html": '<include:test_undefined defined_var="hello" />',
            "components/test_undefined.html": """
{# props defined_var #}
Component with undefined variables:
{{ defined_var }}
{{ undefined_var }}
{{ another_undefined }}
{{ parent_var }}
""".strip(),
        }

        env = Environment(
            loader=DictLoader(templates),
            extensions=[IncludeContentsExtension],
            undefined=DebugUndefined,
        )

        # Context isolation is enabled by default
        # Render with parent variables that should NOT be accessible to components
        output = env.get_template("page.html").render(
            defined_var="hello",
            undefined_var="parent_undefined",
            another_undefined="parent_another",
            parent_var="parent_value",
        )
        print(f"DEBUG: With isolation output: {repr(output)}")

        # With context isolation enabled, only defined component props work
        assert "hello" in output  # This was passed as defined_var prop
        # After the fix: undefined variables render as empty strings, not literals
        assert "{{ undefined_var }}" not in output  # No literal rendering
        assert "{{ another_undefined }}" not in output  # No literal rendering
        assert "{{ parent_var }}" not in output  # No literal rendering
        # Variables are still isolated (parent values don't leak through)
        assert "parent_undefined" not in output
        assert "parent_another" not in output
        assert "parent_value" not in output

    def test_undefined_variables_in_props(self) -> None:
        """Test that undefined variables in prop values render as empty strings."""
        templates = {
            "page.html": '<include:test_props title="{{ undefined_var }}" />',
            "components/test_props.html": """
{# props title #}
Title: {{ title }}
""".strip(),
        }

        env = Environment(
            loader=DictLoader(templates),
            extensions=[IncludeContentsExtension],
            undefined=DebugUndefined,  # Main environment uses DebugUndefined
        )

        output = env.get_template("page.html").render()
        print(f"DEBUG: Props with undefined output: {repr(output)}")

        # Props should use standard Undefined, not DebugUndefined
        # So undefined variables in props render as empty strings
        assert "{{ undefined_var }}" not in output  # No literal rendering
        assert "Title:" in output  # Component renders
        # The prop value should be empty string
        assert output.strip() == "Title:"
