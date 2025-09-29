# Test Parity Overview

This document tracks coverage differences between the Django and Jinja test suites.

## Current Test Coverage Status

### Django Engine (154 tests across 14 files)
- Complete feature coverage including advanced attribute handling, content blocks, error reporting
- Framework integration (context processors, CSRF, request propagation)
- Performance and caching optimizations
- Enhanced error messages with suggestions

### Jinja Engine (151 tests across 15 files)
- ✅ **Core rendering** - Basic includes, named contents, nesting, context isolation
- ✅ **Advanced attributes** - Class manipulation, JS framework events, nested attributes
- ✅ **Content blocks** - HTML `<content:name>` syntax and complex nesting
- ✅ **Error handling** - Enhanced error messages and enum validation
- ✅ **Props validation** - Enum validation, complex objects, edge cases
- ✅ **Performance** - Compilation, rendering, memory usage, complex scenarios
- ✅ **Template logic in attributes** - Full support for `{{ variables }}` and `{% if %}` in attribute values
- ✅ **Icon preprocessing** - `<icon:name>` HTML syntax (both engines)
- ✅ **CSRF integration** - Full CSRF token support with context isolation preservation

## Intentionally Engine-Specific Features

### Django-Only Features (Will Not Port to Jinja)
1. **Django Framework Integration**
   - Context processors integration (`test_context_processors.py`)
   - Complex CSRF middleware token propagation (`test_csrf.py`) - Note: Basic CSRF support is available in Jinja
   - Django `{% includecontents %}` template tag class
   - Request object propagation through components
   - **Rationale**: These are Django-specific framework features, but essential CSRF functionality is preserved in Jinja

2. **Django Template Engine Features**
   - Prop definition caching and concurrency (`test_prop_definition_caching.py`)
   - Django-specific template loading and compilation optimizations
   - **Rationale**: Jinja has its own caching and optimization mechanisms

### Icon System Tests Organization ✅
The icon system tests have been reorganized for proper parity testing:
1. **Django-specific tests**: `tests/django_engine/icons/` - Tests using Django templates
2. **Jinja-specific tests**: `tests/jinja_engine/icons/` - Equivalent tests using Jinja2 templates
3. **Engine-agnostic tests**: `tests/shared/icons/` - Core icon functionality tests

## Achieved Parity Areas

### ✅ Advanced Attribute Handling
- **Django**: `tests/django_engine/test_component_syntax.py` (lines 388-564)
- **Jinja**: `tests/jinja_engine/test_attributes.py`
- **Coverage**: Class append/prepend/negation, JS framework attributes, template logic in attributes, nested attributes

### ✅ HTML Content Block Syntax
- **Django**: `tests/django_engine/test_component_syntax.py` (lines 256-385)
- **Jinja**: `tests/jinja_engine/test_content_blocks.py`
- **Coverage**: `<content:name>` syntax, mixing old/new syntax, complex nesting, edge cases

### ✅ Enhanced Error Reporting
- **Django**: `tests/django_engine/test_improved_error_messages.py`, `test_template_error_messages.py`
- **Jinja**: `tests/jinja_engine/test_errors.py`
- **Coverage**: Enum suggestions, missing template guidance, attribute validation errors

### ✅ Complex Props and Validation
- **Django**: `tests/django_engine/test_props_validation.py`
- **Jinja**: `tests/jinja_engine/test_props.py`
- **Coverage**: Enum validation, special characters, complex objects, list handling

### ✅ Performance and Complex Scenarios
- **Django**: `tests/django_engine/test_complex_nested_components.py`
- **Jinja**: `tests/jinja_engine/test_performance.py`
- **Coverage**: Deep nesting, compilation performance, memory usage, real-world scenarios

## Implementation Notes

### Test File Mapping
```
Django Engine (154 tests)          →  Jinja Engine (151 tests)
├── test_component_syntax.py      →  test_attributes.py + test_content_blocks.py
├── test_improved_error_messages.py → test_errors.py
├── test_template_error_messages.py → test_errors.py
├── test_props_validation.py      →  test_props.py
├── test_complex_nested_components.py → test_performance.py
├── test_context.py               →  test_context.py
├── test_extension.py             →  test_extension.py
├── test_parity_gaps.py           →  [Jinja-specific validation]
├── test_csrf.py                  →  test_csrf_integration.py (essential CSRF support)
├── test_prop_definition_caching.py → [Django-specific, not ported]
└── test_context_processors.py    →  [Django-specific, not ported]
```

### Key Differences in Implementation
1. **Error Handling**: Jinja tests focus on compilation-time errors vs Django's render-time validation
2. **Performance Testing**: Jinja tests compilation speed, Django tests framework integration overhead
3. **Context Handling**: Django uses framework context stack, Jinja uses enhanced context flattening with CSRF preservation
4. **CSRF Integration**: Django uses complex middleware integration, Jinja leverages Django's automatic token injection

### Standardized Behaviors ✅
1. **Attribute Handling**: Both engines now use identical camelCase access patterns (`data-role` → `attrs.dataRole`)
2. **Class Manipulation**: Identical `class:not`, append/prepend logic across both engines
3. **JavaScript Framework Attributes**: Same `@click`, `v-on:`, `x-on:` syntax support in both engines
4. **CSRF Token Handling**: Both engines preserve `csrf_token` and `csrf_input` in component contexts
5. **Attrs Implementation**: Shared `BaseAttrs` with unified callable logic, engine-specific syntax:
   - **Django**: `{% attrs class='btn' type='button' %}`
   - **Jinja2**: `{{ attrs(class_='btn', type='button') }}`

## Validation Strategy

### Functional Parity Verification
- ✅ Both engines produce equivalent output for core component features
- ✅ Attribute handling works identically (class manipulation, JS events, template logic, camelCase access)
- ✅ Content block syntax is interchangeable between engines
- ✅ Error messages provide similar guidance and detail level

### Performance Expectations
- Jinja compilation should be comparable to Django template parsing
- Both engines should handle deep nesting and complex scenarios efficiently
- Memory usage should remain stable across multiple compilations/renders

## Future Maintenance

### When Adding New Features
1. **Cross-Engine Features**: Add tests to both `django_engine/` and `jinja_engine/` directories
2. **Engine-Specific Features**: Document the rationale in this file and add engine-specific tests only
3. **Breaking Changes**: Update this parity matrix and verify both test suites pass

### Review Schedule
- Review this matrix whenever new component features are added
- Update test coverage numbers after significant test additions
- Validate parity claims with actual cross-engine testing when possible

## Current Status: ✅ COMPLETE PARITY

Comprehensive test coverage has been added for both engines, and **all implementation gaps** in the Jinja extension have been resolved.

### ✅ Resolved Implementation Gaps in Jinja Extension

1. **JavaScript Framework Attributes** (Django ✅ → Jinja ✅)
   - `@click`, `@keyup.enter`, `@click.stop.prevent` syntax now works in Jinja
   - `v-on:submit`, `v-model`, `v-bind:` syntax now works in Jinja
   - `x-on:click`, `x-data`, `:class` syntax now works in Jinja
   - **Result**: Full support for modern JS frameworks (Vue, Alpine) with Jinja components

2. **Advanced Class Manipulation** (Django ✅ → Jinja ✅)
   - `class:not="condition ? 'class'"` syntax now works in Jinja
   - Class append/prepend with `& ` and ` &` syntax now works in Jinja
   - **Result**: Full conditional class logic support in Jinja components

3. **Nested Attribute Syntax** (Django ✅ → Jinja ✅)
   - `inner.class="value"`, `button.type="submit"` syntax now works in Jinja
   - Attribute grouping and namespacing fully supported
   - **Result**: Can pass attributes to nested elements in Jinja components

4. **HTML Content Block Syntax** (Django ✅ → Jinja ✅)
   - `<content:name>Content</content:name>` syntax now implemented in Jinja
   - Works alongside traditional `{% contents name %}Content{% endcontents %}` syntax
   - **Result**: Intuitive content block syntax available in Jinja

5. **Template Variables in Attributes** (Django ✅ → Jinja ✅)
   - `class="btn {{ size }}"` - Variables are now properly expanded in attribute values
   - **Status**: Fixed with `_process_template_expression()` method
   - **Result**: Full support for dynamic attribute values

6. **Template Logic in Attributes** (Django ✅ → Jinja ✅)
   - `class="btn {% if large %}btn-lg{% endif %}"` - Control structures now fully processed
   - **Status**: Fixed with mini-template rendering for attribute values
   - **Result**: Complete conditional attribute logic support

7. **Enhanced Context Handling** (Django ✅ → Jinja ✅)
   - Improved context flattening that mirrors Django's `context.flatten()` behavior
   - Added `csrf_input` to preserved context keys for complete CSRF token support
   - **Status**: Fixed with `_flatten_jinja_context()` method and expanded `PRESERVED_KEYS`
   - **Result**: Consistent context behavior and full CSRF protection in components

### ✅ Confirmed Working Features (Full Parity Achieved)

- ✅ **Basic component syntax**: `<include:component-name>`
- ✅ **Hyphenated component names**: `<include:card-with-footer>`
- ✅ **Self-closing syntax**: `<include:component />`
- ✅ **Props and enum validation**: Identical validation rules with detailed error messages
- ✅ **JavaScript framework attributes**: `@click`, `v-on:`, `x-on:`, `:bind` all working
- ✅ **Nested attributes**: `inner.class`, `button.type` syntax fully supported
- ✅ **HTML content blocks**: `<content:name>` syntax implemented
- ✅ **Advanced class manipulation**: `class:not`, append/prepend logic
- ✅ **Template logic in attributes**: `{{ variables }}` and `{% if %}` syntax
- ✅ **Named contents**: Traditional `{% contents %}` syntax
- ✅ **Error messages**: Enhanced enum validation with suggestions
- ✅ **Performance**: Comparable compilation and rendering speed

### Implementation Summary

**All Priority Items Completed** ✅:
1. ✅ JavaScript framework attribute parsing (`@click`, `v-on:`, `x-on:`, `:bind`)
2. ✅ Nested attribute syntax (`inner.class`, `button.type`)
3. ✅ HTML content block syntax (`<content:name>`)
4. ✅ Advanced class manipulation (`class:not`, `class="& base"`)
5. ✅ Template variables and logic in attributes (`{{ var }}`, `{% if %}`)
6. ✅ Callable attrs with unified fallback API (engine-specific syntax, shared implementation)

**Technical Implementation**:
- Enhanced preprocessing layer with attribute normalization/denormalization
- Extended Jinja2 parser to handle special characters in attribute names
- Added content block preprocessing (`<content:name>` → `{% contents %}`)
- Implemented `_process_template_expression()` for template logic in attributes
- Leveraged existing shared BaseAttrs class for class manipulation logic
- Unified callable attrs API with shared `BaseAttrs.__call__()` and engine-specific string rendering:
  - Trailing underscore support for reserved keywords (`class_='btn'` → `class='btn'`)
  - Method chaining: `attrs(type='button')(class_='btn')(disabled=True)`
  - Proper merging of extended/prepended/nested attribute dictionaries
  - Engine-specific HTML escaping (Django escapes, Jinja2 delegates to template-level escaping)
