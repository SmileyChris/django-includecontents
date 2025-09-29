#!/usr/bin/env python
"""Debug script for class negation issue."""

import os
import sys
import django
from django.conf import settings

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tests.settings')
sys.path.insert(0, os.path.dirname(__file__))
django.setup()

from django.template import Context
from django.template.loader import render_to_string
from includecontents.templatetags.includecontents import TemplateAttributeExpression

print("=== Testing class negation ===")

# Test 1: Basic filter evaluation
print("\n1. Testing basic filter evaluation:")
from django.template import Template

template_str = "{{ disabled|not }}"
template = Template(template_str)
context = Context({'disabled': False})
result = template.render(context)
print(f"disabled=False, disabled|not = {result!r}")

context = Context({'disabled': True})
result = template.render(context)
print(f"disabled=True, disabled|not = {result!r}")

# Test 2: TemplateAttributeExpression
print("\n2. Testing TemplateAttributeExpression:")
expr = TemplateAttributeExpression("{{ disabled|not }}")
context = Context({'disabled': False})
result = expr.resolve(context)
print(f"disabled=False, TemplateAttributeExpression result = {result!r}")

context = Context({'disabled': True})
result = expr.resolve(context)
print(f"disabled=True, TemplateAttributeExpression result = {result!r}")

# Test 3: Test coercion function
print("\n3. Testing coercion function:")
from includecontents.templatetags.includecontents import _coerce_attr_value
print(f"_coerce_attr_value('True') = {_coerce_attr_value('True')!r}")
print(f"_coerce_attr_value('False') = {_coerce_attr_value('False')!r}")
print(f"_coerce_attr_value('true') = {_coerce_attr_value('true')!r}")
print(f"_coerce_attr_value('false') = {_coerce_attr_value('false')!r}")

# Test 4: Manual attrs testing
print("\n4. Testing attrs merging manually:")
from includecontents.django.attrs import Attrs as DjangoAttrs

# Simulate what happens in the attrs tag
context_attrs = DjangoAttrs()
context_attrs['class'] = 'mycard'
context_attrs['class:active'] = True

print(f"Parent attrs: {dict(context_attrs.all_attrs())}")

# Create child attrs with fallbacks
child_attrs = DjangoAttrs()
child_attrs['class'] = '& card'  # This should append to existing class
child_attrs['class:lg'] = False

print(f"Child attrs before merge: {dict(child_attrs.all_attrs())}")

# Debug the update process
print(f"Context attrs to be updated: {dict(context_attrs.all_attrs())}")
print("Before update:")
print(f"  child_attrs._attrs = {child_attrs._attrs}")
print(f"  child_attrs._conditional_modifiers = {child_attrs._conditional_modifiers}")

# Now simulate the attrs tag logic
child_attrs.update(context_attrs)

print("After update:")
print(f"  child_attrs._attrs = {child_attrs._attrs}")
print(f"  child_attrs._conditional_modifiers = {child_attrs._conditional_modifiers}")
print(f"Child attrs after merge: {dict(child_attrs.all_attrs())}")

# Test 5: Full component rendering
print("\n5. Testing full component rendering:")
context = {'disabled': False}
try:
    result = render_to_string("test_component/class_negation.html", context)
    print(f"disabled=False, rendered result:")
    print(repr(result))
    print("Actual output:")
    print(result)
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()

print("\n=== Done ===")
