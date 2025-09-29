#!/usr/bin/env python
import os
import django
from django.conf import settings
from django.template.loader import render_to_string

# Configure Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tests.settings')
django.setup()

# Test simple class attribute
debug_template = '''<include:debug-card title="test" class:active="{{ disabled|not }}" />'''

from django.template import Template, Context

template = Template(debug_template)
result = template.render(Context({'disabled': False}))
print("With disabled=False:")
print(result)
print()

result = template.render(Context({'disabled': True}))
print("With disabled=True:")
print(result)