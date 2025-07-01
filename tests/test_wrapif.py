import pytest
from django.template import Context, Template, TemplateSyntaxError
from django.test import SimpleTestCase


class TestWrapIfTag(SimpleTestCase):
    """Test cases for the {% wrapif %} template tag."""
    
    def render_template(self, template_string, context=None):
        """Helper to render a template string with context."""
        template = Template(template_string)
        return template.render(Context(context or {}))
    
    def test_basic_wrapif_true(self):
        """Test basic wrapif with true condition."""
        template = """
        {% load includecontents %}
        {% wrapif show %}
        <div>{% contents %}Hello{% endcontents %}</div>
        {% endwrapif %}
        """
        result = self.render_template(template, {"show": True})
        self.assertEqual(result.strip(), "<div>Hello</div>")
    
    def test_basic_wrapif_false(self):
        """Test basic wrapif with false condition."""
        template = """
        {% load includecontents %}
        {% wrapif show %}
        <div>{% contents %}Hello{% endcontents %}</div>
        {% endwrapif %}
        """
        result = self.render_template(template, {"show": False})
        self.assertEqual(result.strip(), "Hello")
    
    def test_shorthand_then_syntax(self):
        """Test shorthand syntax with then."""
        template = """
        {% load includecontents %}
        {% wrapif show then "div" class="wrapper" %}
          Hello World
        {% endwrapif %}
        """
        result = self.render_template(template, {"show": True})
        self.assertIn('<div class="wrapper">', result)
        self.assertIn('Hello World', result)
        self.assertIn('</div>', result)
        
        result = self.render_template(template, {"show": False})
        self.assertIn("Hello World", result)
        self.assertNotIn('<div', result)
    
    def test_shorthand_with_variable_attrs(self):
        """Test shorthand syntax with variable attributes."""
        template = """
        {% load includecontents %}
        {% wrapif has_link then "a" href=url class="link" %}
          Click me
        {% endwrapif %}
        """
        result = self.render_template(template, {"has_link": True, "url": "/path/to/page"})
        self.assertIn('<a href="/path/to/page" class="link">', result)
        self.assertIn('Click me', result)
        self.assertIn('</a>', result)
        
        result = self.render_template(template, {"has_link": False})
        self.assertIn("Click me", result)
        self.assertNotIn('<a', result)
    
    def test_wrapelse_shorthand(self):
        """Test wrapelse with shorthand syntax."""
        template = """
        {% load includecontents %}
        {% wrapif is_link then "a" href="/path" %}
        {% wrapelse "span" class="text" %}
          Click me
        {% endwrapif %}
        """
        result = self.render_template(template, {"is_link": True})
        self.assertIn('<a href="/path">', result)
        self.assertIn('Click me', result)
        self.assertIn('</a>', result)
        
        result = self.render_template(template, {"is_link": False})
        self.assertIn('<span class="text">', result)
        self.assertIn('Click me', result)
        self.assertIn('</span>', result)
    
    def test_wrapelse_full_syntax(self):
        """Test wrapelse with full template syntax."""
        template = """
        {% load includecontents %}
        {% wrapif premium %}
        <div class="premium-content">
          <span class="badge">PRO</span>
          {% contents %}{{ content }}{% endcontents %}
        </div>
        {% wrapelse %}
        <div class="regular-content">
          {{ contents }}
          <a href="/upgrade">Upgrade to see more</a>
        </div>
        {% endwrapif %}
        """
        result = self.render_template(template, {"premium": True, "content": "Secret"})
        self.assertIn('<div class="premium-content">', result)
        self.assertIn('<span class="badge">PRO</span>', result)
        self.assertIn('Secret', result)
        
        result = self.render_template(template, {"premium": False, "content": "Secret"})
        self.assertIn('<div class="regular-content">', result)
        self.assertIn('Secret', result)
        self.assertIn('<a href="/upgrade">Upgrade to see more</a>', result)
    
    def test_wrapelif_shorthand(self):
        """Test wrapelif with shorthand syntax."""
        template = """
        {% load includecontents %}
        {% wrapif level == 1 then "h1" %}
        {% wrapelif level == 2 then "h2" %}
        {% wrapelif level == 3 then "h3" %}
        {% wrapelse "p" %}
          {{ text }}
        {% endwrapif %}
        """
        result = self.render_template(template, {"level": 1, "text": "Title"})
        self.assertIn('<h1>', result)
        self.assertIn('Title', result)
        self.assertIn('</h1>', result)
        
        result = self.render_template(template, {"level": 2, "text": "Title"})
        self.assertIn('<h2>', result)
        self.assertIn('Title', result)
        self.assertIn('</h2>', result)
        
        result = self.render_template(template, {"level": 3, "text": "Title"})
        self.assertIn('<h3>', result)
        self.assertIn('Title', result)
        self.assertIn('</h3>', result)
        
        result = self.render_template(template, {"level": 4, "text": "Title"})
        self.assertIn('<p>', result)
        self.assertIn('Title', result)
        self.assertIn('</p>', result)
    
    def test_complex_conditions(self):
        """Test complex conditions with and/or/not."""
        template = """
        {% load includecontents %}
        {% wrapif user.is_authenticated and user.is_staff then "div" class="admin" %}
        {% wrapelse "div" class="guest" %}
          Admin panel
        {% endwrapif %}
        """
        # Create mock user object
        class MockUser:
            def __init__(self, is_authenticated, is_staff):
                self.is_authenticated = is_authenticated
                self.is_staff = is_staff
        
        user = MockUser(True, True)
        result = self.render_template(template, {"user": user})
        self.assertIn('<div class="admin">', result)
        self.assertIn('Admin panel', result)
        self.assertIn('</div>', result)
        
        user = MockUser(True, False)
        result = self.render_template(template, {"user": user})
        self.assertIn('<div class="guest">', result)
        self.assertIn('Admin panel', result)
        
        user = MockUser(False, False)
        result = self.render_template(template, {"user": user})
        self.assertIn('<div class="guest">', result)
        self.assertIn('Admin panel', result)
    
    def test_boolean_attributes(self):
        """Test boolean attributes in shorthand syntax."""
        template = """
        {% load includecontents %}
        {% wrapif show then "button" disabled %}
          Click me
        {% endwrapif %}
        """
        result = self.render_template(template, {"show": True})
        self.assertIn('<button disabled>', result)
        self.assertIn('Click me', result)
        self.assertIn('</button>', result)
    
    def test_empty_condition_error(self):
        """Test that empty condition raises error."""
        template = """
        {% load includecontents %}
        {% wrapif %}
          content
        {% endwrapif %}
        """
        with self.assertRaises(TemplateSyntaxError):
            self.render_template(template)
    
    def test_missing_then_tag_error(self):
        """Test that missing tag after 'then' raises error."""
        template = """
        {% load includecontents %}
        {% wrapif condition then %}
          content
        {% endwrapif %}
        """
        with self.assertRaises(TemplateSyntaxError):
            self.render_template(template, {"condition": True})
    
    def test_multiple_contents_blocks(self):
        """Test multiple named contents blocks."""
        template = """
        {% load includecontents %}
        {% wrapif show_card %}
        <div class="card">
          <div class="card-header">
            {% contents header %}{{ title }}{% endcontents %}
          </div>
          <div class="card-body">
            {% contents %}{{ body }}{% endcontents %}
          </div>
        </div>
        {% endwrapif %}
        """
        result = self.render_template(template, {
            "show_card": True,
            "title": "Card Title",
            "body": "Card Body"
        })
        self.assertIn('<div class="card">', result)
        self.assertIn('<div class="card-header">', result)
        self.assertIn('Card Title', result)
        self.assertIn('<div class="card-body">', result)
        self.assertIn('Card Body', result)
        
        # When condition is false, only contents are shown
        result = self.render_template(template, {
            "show_card": False,
            "title": "Card Title",
            "body": "Card Body"
        })
        self.assertNotIn('<div class="card">', result)
        # Multiple contents blocks are returned when no wrapper is applied
        self.assertIn('Card Title', result)
        self.assertIn('Card Body', result)
    
    def test_nested_wrapif(self):
        """Test nested wrapif tags."""
        template = """
        {% load includecontents %}
        {% wrapif outer then "div" class="outer" %}
          {% wrapif inner then "span" class="inner" %}
            Content
          {% endwrapif %}
        {% endwrapif %}
        """
        result = self.render_template(template, {"outer": True, "inner": True})
        self.assertIn('<div class="outer">', result)
        self.assertIn('<span class="inner">', result)
        self.assertIn('Content', result)
        
        result = self.render_template(template, {"outer": True, "inner": False})
        self.assertIn('<div class="outer">', result)
        self.assertIn('Content', result)
        self.assertNotIn('<span', result)
        
        result = self.render_template(template, {"outer": False, "inner": True})
        self.assertIn('<span class="inner">', result)
        self.assertIn('Content', result)
        self.assertNotIn('<div', result)
        
        result = self.render_template(template, {"outer": False, "inner": False})
        self.assertIn('Content', result)
        self.assertNotIn('<div', result)
        self.assertNotIn('<span', result)
    
    def test_escaping_attributes(self):
        """Test that attribute values are properly escaped."""
        template = """
        {% load includecontents %}
        {% wrapif show then "div" title=user_input %}
          Content
        {% endwrapif %}
        """
        result = self.render_template(template, {
            "show": True,
            "user_input": 'Hello "World" & <Friends>'
        })
        self.assertIn('title="Hello &quot;World&quot; &amp; &lt;Friends&gt;"', result)
    
    def test_comparison_operators(self):
        """Test various comparison operators in conditions."""
        template = """
        {% load includecontents %}
        {% wrapif value > 10 then "strong" %}
          Big number
        {% endwrapif %}
        """
        result = self.render_template(template, {"value": 15})
        self.assertIn('<strong>', result)
        self.assertIn('Big number', result)
        self.assertIn('</strong>', result)
        
        result = self.render_template(template, {"value": 5})
        self.assertIn('Big number', result)
        self.assertNotIn('<strong>', result)
    
    def test_in_operator(self):
        """Test 'in' operator in conditions."""
        template = """
        {% load includecontents %}
        {% wrapif item in allowed_items then "span" class="allowed" %}
          {{ item }}
        {% endwrapif %}
        """
        result = self.render_template(template, {
            "item": "apple",
            "allowed_items": ["apple", "banana", "orange"]
        })
        self.assertIn('<span class="allowed">', result)
        self.assertIn('apple', result)
        self.assertIn('</span>', result)
        
        result = self.render_template(template, {
            "item": "grape",
            "allowed_items": ["apple", "banana", "orange"]
        })
        self.assertIn('grape', result)
        self.assertNotIn('<span', result)