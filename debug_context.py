#!/usr/bin/env python
import os
os.environ['DJANGO_SETTINGS_MODULE'] = 'tests.settings'
import django
django.setup()

from django.test import RequestFactory
from django.template import Context, RequestContext
from django.template.loader import render_to_string

# Set up the same test configuration
from tests.django_engine.test_complex_nested_components import (
    complex_processor_one, complex_processor_two, complex_processor_three
)

# Create a request
factory = RequestFactory()
request = factory.get('/')

# Create a RequestContext with processors (like the test)
context = RequestContext(request, {'base_var': 'base_value'})

print("Context dicts:")
for i, d in enumerate(context.dicts):
    print(f"  Dict {i}: {d}")

print(f"\nContext._processors_index: {getattr(context, '_processors_index', 'NOT SET')}")
print(f"Context type: {type(context)}")

# Test what the processors return
print(f"\nProcessor outputs:")
print(f"  complex_processor_one: {complex_processor_one(request)}")
print(f"  complex_processor_two: {complex_processor_two(request)}")
print(f"  complex_processor_three: {complex_processor_three(request)}")

# Check if the context has the processor data
print(f"\nContext values:")
print(f"  base_var: {context.get('base_var')}")
print(f"  user_type: {context.get('user_type')}")
print(f"  app_version: {context.get('app_version')}")
print(f"  request: {context.get('request')}")