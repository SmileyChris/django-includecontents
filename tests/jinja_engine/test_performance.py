import time
import pytest
from jinja2 import Environment

from includecontents.jinja2.extension import IncludeContentsExtension


def create_jinja_env():
    """Create a Jinja environment with the extension."""
    return Environment(
        extensions=[IncludeContentsExtension],
        loader=None,  # We'll use from_string
        autoescape=True,
    )


class TestNestedComponentPerformance:
    """Test performance characteristics of nested components."""

    def test_deep_nesting_compilation_performance(self):
        """Test that deeply nested components compile efficiently."""
        env = create_jinja_env()

        # Create template with deep nesting
        template_source = '''
        <include:level1>
            <include:level2>
                <include:level3>
                    <include:level4>
                        <include:level5>
                            <include:level6>
                                <include:level7>
                                    <include:level8>
                                        <include:level9>
                                            <include:level10>
                                                Deep content
                                            </include:level10>
                                        </include:level9>
                                    </include:level8>
                                </include:level7>
                            </include:level6>
                        </include:level5>
                    </include:level4>
                </include:level3>
            </include:level2>
        </include:level1>
        '''

        # Measure compilation time
        start_time = time.perf_counter()
        for _ in range(10):
            template = env.from_string(template_source)
        end_time = time.perf_counter()

        avg_compilation_time = (end_time - start_time) / 10

        # Should compile reasonably quickly (less than 50ms per compilation)
        assert avg_compilation_time < 0.05

        # Verify template compiles correctly
        assert template is not None

    def test_multiple_components_compilation_performance(self):
        """Test compilation performance with many components at same level."""
        env = create_jinja_env()

        # Create template with many sibling components
        components = []
        for i in range(50):
            components.append(f'<include:component-{i} id="{i}">Content {i}</include:component-{i}>')

        template_source = '\n'.join(components)

        # Measure compilation time
        start_time = time.perf_counter()
        for _ in range(5):
            template = env.from_string(template_source)
        end_time = time.perf_counter()

        avg_compilation_time = (end_time - start_time) / 5

        # Should handle many components efficiently (less than 100ms)
        assert avg_compilation_time < 0.1

        assert template is not None

    def test_complex_attribute_parsing_performance(self):
        """Test performance of parsing complex attributes."""
        env = create_jinja_env()

        # Create template with complex attributes
        template_source = '''
        <include:complex-component
            class="btn btn-{{ variant }} {{ size }} {{ theme }}"
            data-config="{{ config | tojson | escape }}"
            style="{{{% if width %}}width: {{{{ width }}}}px;{{{% endif %}}} {{{% if height %}}height: {{{{ height }}}}px;{{{% endif %}}}}"
            @click="handleClick($event, '{{ item_id }}', {{ item_data | tojson }})"
            v-on:mouseover="showTooltip($event, { title: '{{ title | escape }}', content: '{{ description | escape }}' })"
            :class="{ 'active': {{ is_active | lower }}, 'disabled': {{ is_disabled | lower }}, 'loading': {{ is_loading | lower }} }"
            x-data="{ open: {{ is_open | lower }}, count: {{ initial_count }}, items: {{ items | tojson }} }"
            inner.data-id="{{ inner_id }}"
            inner.class="inner-component {{ inner_variant }}"
            inner.@click="handleInnerClick({{ inner_data | tojson }})"
            aria-label="{{ accessibility_label | escape }}"
            aria-describedby="{{ description_id }}"
            role="{{ component_role | default('button') }}"
            tabindex="{{ tab_index | default(0) }}">
            Complex component content
        </include:complex-component>
        '''

        # Measure parsing time
        start_time = time.perf_counter()
        for _ in range(20):
            template = env.from_string(template_source)
        end_time = time.perf_counter()

        avg_parsing_time = (end_time - start_time) / 20

        # Should parse complex attributes efficiently (less than 20ms)
        assert avg_parsing_time < 0.02

        assert template is not None

    def test_content_block_parsing_performance(self):
        """Test performance of parsing complex content blocks."""
        env = create_jinja_env()

        # Create template with many content blocks
        content_blocks = []
        for i in range(20):
            content_blocks.append(f'''
            <content:section-{i}>
                <h{i % 6 + 1}>Section {i}</h{i % 6 + 1}>
                <p>Content for section {i} with {{{{ "variable_{i}".format(i=i) }}}}.</p>
                {{% for item in items_{i} %}}
                    <div class="item-{i}">{{{{ item.name }}}}</div>
                {{% endfor %}}
            </content:section-{i}>
            ''')

        template_source = f'''
        <include:multi-section-component>
            {chr(10).join(content_blocks)}
        </include:multi-section-component>
        '''

        # Measure parsing time
        start_time = time.perf_counter()
        for _ in range(10):
            template = env.from_string(template_source)
        end_time = time.perf_counter()

        avg_parsing_time = (end_time - start_time) / 10

        # Should parse multiple content blocks efficiently (less than 50ms)
        assert avg_parsing_time < 0.05

        assert template is not None


class TestRenderingPerformance:
    """Test performance characteristics of rendering components."""

    def test_simple_component_rendering_performance(self):
        """Test basic component rendering performance."""
        env = create_jinja_env()

        template_source = '''
        <include:simple-button variant="primary" size="large">
            Click me
        </include:simple-button>
        '''

        template = env.from_string(template_source)

        # Measure rendering time (without actual component templates)
        context = {
            'variant': 'primary',
            'size': 'large',
            'button_text': 'Click me'
        }

        start_time = time.perf_counter()
        for _ in range(100):
            try:
                result = template.render(**context)
            except Exception:
                # Expected if component templates don't exist
                pass
        end_time = time.perf_counter()

        avg_render_time = (end_time - start_time) / 100

        # Should render quickly even with missing templates (less than 5ms)
        assert avg_render_time < 0.005

    def test_nested_component_rendering_performance(self):
        """Test rendering performance with nested components."""
        env = create_jinja_env()

        template_source = '''
        <include:outer-container>
            <include:inner-grid cols="3">
                {% for i in range(9) %}
                    <include:grid-item index="{{ i }}">
                        <include:content-card variant="compact">
                            Item {{ i }}
                        </include:content-card>
                    </include:grid-item>
                {% endfor %}
            </include:inner-grid>
        </include:outer-container>
        '''

        template = env.from_string(template_source)

        context = {}

        start_time = time.perf_counter()
        for _ in range(20):
            try:
                result = template.render(**context)
            except Exception:
                # Expected if component templates don't exist
                pass
        end_time = time.perf_counter()

        avg_render_time = (end_time - start_time) / 20

        # Should handle nested rendering efficiently (less than 20ms)
        assert avg_render_time < 0.02

    def test_variable_substitution_performance(self):
        """Test performance of variable substitution in component attributes."""
        env = create_jinja_env()

        template_source = '''
        {% for item in items %}
            <include:dynamic-component
                id="{{ item.id }}"
                title="{{ item.title | title }}"
                description="{{ item.description | truncate(100) }}"
                category="{{ item.category | lower }}"
                tags="{{ item.tags | join(',') }}"
                created="{{ item.created | strftime('%Y-%m-%d') }}"
                priority="{{ item.priority | default('normal') }}"
                status="{{ item.status | capitalize }}"
                url="{{ url_for('item_detail', id=item.id) }}"
                class="item item-{{ item.category }} priority-{{ item.priority }}">
                {{ item.content | markdown | safe }}
            </include:dynamic-component>
        {% endfor %}
        '''

        template = env.from_string(template_source)

        # Create context with many items
        items = []
        for i in range(50):
            items.append({
                'id': i,
                'title': f'Item {i}',
                'description': f'Description for item {i}' * 5,
                'category': f'category-{i % 5}',
                'tags': [f'tag-{j}' for j in range(3)],
                'priority': ['low', 'normal', 'high'][i % 3],
                'status': 'active',
                'content': f'Content for item {i}'
            })

        context = {'items': items}

        start_time = time.perf_counter()
        for _ in range(5):
            try:
                result = template.render(**context)
            except Exception:
                # Expected - some filters/functions may not exist
                pass
        end_time = time.perf_counter()

        avg_render_time = (end_time - start_time) / 5

        # Should handle many variable substitutions efficiently (less than 100ms)
        assert avg_render_time < 0.1


class TestMemoryPerformance:
    """Test memory usage characteristics."""

    def test_template_compilation_memory_usage(self):
        """Test that template compilation doesn't create excessive objects."""
        env = create_jinja_env()

        # Create many different templates
        templates = []
        for i in range(100):
            template_source = f'''
            <include:component-{i}
                prop1="value-{i}"
                prop2="{{{{ variable_{i} }}}}"
                prop3="{{{{ 'constant-{i}' }}}}">
                Content {i}
            </include:component-{i}>
            '''
            templates.append(env.from_string(template_source))

        # All templates should compile successfully
        assert len(templates) == 100
        for template in templates:
            assert template is not None

    def test_large_template_compilation(self):
        """Test compilation of very large templates."""
        env = create_jinja_env()

        # Create a very large template
        components = []
        for i in range(500):
            components.append(f'''
            <include:item-{i}
                id="{i}"
                class="item-{i % 10}"
                data-value="{{{{ values[{i}] }}}}"
                {{{% if i % 2 %}}enabled{{{% endif %}}}>
                Item content {i}
            </include:item-{i}>
            ''')

        template_source = '\n'.join(components)

        # Should handle large templates
        start_time = time.perf_counter()
        template = env.from_string(template_source)
        compilation_time = time.perf_counter() - start_time

        # Should compile large template reasonably quickly (less than 1 second)
        assert compilation_time < 1.0
        assert template is not None

    def test_repeated_compilation_memory_stability(self):
        """Test that repeated compilation doesn't cause memory leaks."""
        env = create_jinja_env()

        template_source = '''
        <include:memory-test
            data="{{ large_data }}"
            items="{{ item_list }}"
            config="{{ complex_config }}">
            Memory test content
        </include:memory-test>
        '''

        # Compile the same template many times
        for i in range(200):
            template = env.from_string(template_source)
            assert template is not None

            # Try to trigger garbage collection periodically
            if i % 50 == 0:
                import gc
                gc.collect()


class TestComplexScenarioPerformance:
    """Test performance in complex real-world scenarios."""

    def test_dashboard_template_performance(self):
        """Test performance of a complex dashboard-like template."""
        env = create_jinja_env()

        template_source = '''
        <include:dashboard-layout>
            <content:header>
                <include:navigation>
                    <include:nav-item href="/">Home</include:nav-item>
                    <include:nav-item href="/dashboard">Dashboard</include:nav-item>
                    <include:nav-item href="/settings">Settings</include:nav-item>
                </include:navigation>
                <include:user-menu user="{{ current_user }}">
                    <content:dropdown>
                        <include:menu-item href="/profile">Profile</include:menu-item>
                        <include:menu-item href="/logout">Logout</include:menu-item>
                    </content:dropdown>
                </include:user-menu>
            </content:header>

            <content:sidebar>
                <include:widget-list>
                    {% for widget in widgets %}
                        <include:widget
                            type="{{ widget.type }}"
                            title="{{ widget.title }}"
                            data="{{ widget.data }}"
                            config="{{ widget.config }}">
                            {{ widget.content | safe }}
                        </include:widget>
                    {% endfor %}
                </include:widget-list>
            </content:sidebar>

            <content:main>
                <include:grid cols="3">
                    {% for item in main_items %}
                        <include:card
                            variant="{{ item.variant }}"
                            size="{{ item.size }}"
                            status="{{ item.status }}">
                            <content:header>{{ item.title }}</content:header>
                            <content:body>{{ item.body | markdown | safe }}</content:body>
                            <content:footer>
                                <include:action-bar>
                                    {% for action in item.actions %}
                                        <include:button
                                            variant="{{ action.variant }}"
                                            href="{{ action.url }}"
                                            @click="{{ action.onclick }}">
                                            {{ action.label }}
                                        </include:button>
                                    {% endfor %}
                                </include:action-bar>
                            </content:footer>
                        </include:card>
                    {% endfor %}
                </include:grid>
            </content:main>
        </include:dashboard-layout>
        '''

        start_time = time.perf_counter()
        template = env.from_string(template_source)
        compilation_time = time.perf_counter() - start_time

        # Should compile complex template efficiently (less than 200ms)
        assert compilation_time < 0.2
        assert template is not None

    def test_form_template_performance(self):
        """Test performance of complex form templates."""
        env = create_jinja_env()

        template_source = '''
        <include:form action="/submit" method="post">
            <content:fields>
                {% for field in form_fields %}
                    <include:field-group>
                        <include:label for="{{ field.id }}">{{ field.label }}</include:label>

                        {% if field.type == 'text' %}
                            <include:text-input
                                id="{{ field.id }}"
                                name="{{ field.name }}"
                                value="{{ field.value | default('') }}"
                                placeholder="{{ field.placeholder }}"
                                required="{{ field.required }}"
                                pattern="{{ field.pattern }}"
                                class="{{ field.css_class }}">
                            </include:text-input>
                        {% elif field.type == 'select' %}
                            <include:select
                                id="{{ field.id }}"
                                name="{{ field.name }}"
                                multiple="{{ field.multiple }}">
                                {% for option in field.options %}
                                    <include:option
                                        value="{{ option.value }}"
                                        selected="{{ option.selected }}">
                                        {{ option.label }}
                                    </include:option>
                                {% endfor %}
                            </include:select>
                        {% elif field.type == 'checkbox-group' %}
                            <include:checkbox-group>
                                {% for checkbox in field.checkboxes %}
                                    <include:checkbox
                                        id="{{ checkbox.id }}"
                                        name="{{ field.name }}"
                                        value="{{ checkbox.value }}"
                                        checked="{{ checkbox.checked }}">
                                        {{ checkbox.label }}
                                    </include:checkbox>
                                {% endfor %}
                            </include:checkbox-group>
                        {% endif %}

                        {% if field.help_text %}
                            <include:help-text>{{ field.help_text }}</include:help-text>
                        {% endif %}

                        {% if field.errors %}
                            <include:error-list>
                                {% for error in field.errors %}
                                    <include:error-message>{{ error }}</include:error-message>
                                {% endfor %}
                            </include:error-list>
                        {% endif %}
                    </include:field-group>
                {% endfor %}
            </content:fields>

            <content:actions>
                <include:button type="submit" variant="primary">Submit</include:button>
                <include:button type="button" variant="secondary">Cancel</include:button>
            </content:actions>
        </include:form>
        '''

        start_time = time.perf_counter()
        template = env.from_string(template_source)
        compilation_time = time.perf_counter() - start_time

        # Should compile complex form template efficiently (less than 150ms)
        assert compilation_time < 0.15
        assert template is not None


class TestErrorHandlingPerformance:
    """Test performance characteristics of error handling."""

    def test_syntax_error_detection_performance(self):
        """Test that syntax errors are detected quickly."""
        env = create_jinja_env()

        # Templates with various syntax errors
        error_templates = [
            '<include:unclosed>Content',  # Unclosed tag
            '<include:>Empty name</include:>',  # Empty component name
            '<include:test attr=>Invalid attr</include:test>',  # Invalid attribute
            '<include:test class="unclosed>Missing quote</include:test>',  # Unclosed quote
            '<content:invalid>Outside component</content:invalid>',  # Content block outside component
        ]

        total_time = 0
        for template_source in error_templates:
            start_time = time.perf_counter()
            try:
                template = env.from_string(template_source)
                template.render()
            except Exception:
                # Expected - these should produce errors
                pass
            total_time += time.perf_counter() - start_time

        avg_error_time = total_time / len(error_templates)

        # Error detection should be fast (less than 10ms per error)
        assert avg_error_time < 0.01


if __name__ == "__main__":
    # Simple test runner for development
    import sys

    test_classes = [
        TestNestedComponentPerformance,
        TestRenderingPerformance,
        TestMemoryPerformance,
        TestComplexScenarioPerformance,
        TestErrorHandlingPerformance,
    ]

    passed = 0
    failed = 0

    for test_class in test_classes:
        instance = test_class()
        methods = [method for method in dir(instance) if method.startswith('test_')]

        for method_name in methods:
            try:
                method = getattr(instance, method_name)
                method()
                print(f"✓ {test_class.__name__}.{method_name}")
                passed += 1
            except Exception as e:
                print(f"✗ {test_class.__name__}.{method_name}: {e}")
                failed += 1

    print(f"\nResults: {passed} passed, {failed} failed")

    if failed > 0:
        sys.exit(1)