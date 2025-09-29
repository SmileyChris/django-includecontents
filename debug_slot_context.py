#!/usr/bin/env python
import os
import django
from django.conf import settings
from django.template.loader import render_to_string
from django.http import HttpRequest

# Configure Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tests.settings')
django.setup()

# Create a test request
request = HttpRequest()
request.method = 'GET'

# Test simple rendering with context
content = render_to_string(
    'test_processor_slots.html',
    context={'slot_data': 'slot_content'},
    request=request
)

print("Rendered content:")
print(content)
print()

# Test a simpler case to see what's available in the default slot
from django.template import Template, Context
from includecontents.django.base import DjangoTemplates

engine = DjangoTemplates({
    'DIRS': ['tests/templates'],
    'OPTIONS': {}
})

# Test template rendering directly
template_content = '''
<include:slot-tester>
    Available variables: {% for var_name, var_value in contents.default.context.items %}{{ var_name }}={{ var_value }}, {% endfor %}
    slot_data={{ slot_data }}
</include:slot-tester>
'''

template = engine.from_string(template_content)
result = template.render(context={'slot_data': 'test_value'}, request=request)
print("Direct template test:")
print(result)