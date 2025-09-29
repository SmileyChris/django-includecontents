"""Test that TemplateAttributeExpression works correctly with reuse."""

from django.template import Template, Context

from includecontents.templatetags.includecontents import TemplateAttributeExpression


def test_template_attribute_expression_reuse():
    """Test that TemplateAttributeExpression handles multiple renders correctly."""
    expr = TemplateAttributeExpression("btn {{ variant }}")

    # First render
    result1 = expr.resolve(Context({"variant": "primary"}))
    assert result1 == "btn primary"

    # Second render with different context
    result2 = expr.resolve(Context({"variant": "secondary"}))
    assert result2 == "btn secondary"

    # Third render with yet another context
    result3 = expr.resolve(Context({"variant": "danger"}))
    assert result3 == "btn danger"


def test_multiple_instances_same_pattern():
    """Test that multiple instances with same pattern work independently."""
    expr1 = TemplateAttributeExpression("user-{{ id }}")
    expr2 = TemplateAttributeExpression("user-{{ id }}")

    result1 = expr1.resolve(Context({"id": "123"}))
    result2 = expr2.resolve(Context({"id": "456"}))

    assert result1 == "user-123"
    assert result2 == "user-456"

    # Ensure they don't share compiled templates
    assert expr1._template is not expr2._template


def test_template_reuse_in_loops():
    """Test that attributes work correctly in loops."""
    template = Template("""
        {% for item in items %}
            <include:empty-props data-id="{{ prefix }}-{{ item }}" />
        {% endfor %}
    """)

    output = template.render(Context({"items": ["a", "b", "c"], "prefix": "item"}))

    assert 'data-id="item-a"' in output
    assert 'data-id="item-b"' in output
    assert 'data-id="item-c"' in output


def test_nested_context_inheritance():
    """Test that context inheritance works correctly."""
    template = Template("""
        {% with outer="A" %}
            <include:empty-props data-test="{{ outer }}-{{ inner }}" />
            {% with inner="B" %}
                <include:empty-props data-test="{{ outer }}-{{ inner }}" />
            {% endwith %}
        {% endwith %}
    """)

    output = template.render(Context({"inner": "X"}))

    # First component should see outer=A, inner=X (from parent context)
    assert 'data-test="A-X"' in output
    # Second component should see outer=A, inner=B (from with block)
    assert 'data-test="A-B"' in output


def test_escaping_consistency():
    """Test that escaping is consistent across renders."""
    expr = TemplateAttributeExpression('title="{{ text }}"')

    # Test with dangerous content
    result1 = expr.resolve(Context({"text": '<script>alert("xss")</script>'}))
    assert "&lt;script&gt;" in result1
    assert "<script>" not in result1

    # Test with safe content
    result2 = expr.resolve(Context({"text": "Hello World"}))
    assert result2 == 'title="Hello World"'


def test_complex_mixed_content_reuse():
    """Test complex mixed content with multiple renders."""
    template = Template("""
        <include:empty-props 
            data-info="{% if show_id %}[{{ id }}] {% endif %}{{ name }}{% if show_status %} - {{ status }}{% endif %}"
        />
    """)

    # First render
    output1 = template.render(
        Context(
            {
                "show_id": True,
                "id": "123",
                "name": "Alice",
                "show_status": True,
                "status": "Active",
            }
        )
    )
    assert 'data-info="[123] Alice - Active"' in output1

    # Second render with different values
    output2 = template.render(
        Context(
            {
                "show_id": False,
                "id": "456",
                "name": "Bob",
                "show_status": True,
                "status": "Inactive",
            }
        )
    )
    assert 'data-info="Bob - Inactive"' in output2

    # Third render with minimal values
    output3 = template.render(
        Context({"show_id": False, "name": "Charlie", "show_status": False})
    )
    assert 'data-info="Charlie"' in output3
