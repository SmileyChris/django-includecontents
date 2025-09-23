# Test Parity Overview

This document tracks coverage differences between the Django and Jinja test suites.

## Current Test Coverage Status

### Django Engine (99 tests across 8 files)
- Complete feature coverage including advanced attribute handling, content blocks, error reporting
- Framework integration (context processors, CSRF, request propagation)
- Performance and caching optimizations
- Enhanced error messages with suggestions

### Jinja Engine (30 → 80+ tests across 6 files)
- ✅ **Core rendering** - Basic includes, named contents, nesting, context isolation
- ✅ **Advanced attributes** - Class manipulation, JS framework events, template logic
- ✅ **Content blocks** - HTML `<content:name>` syntax and complex nesting
- ✅ **Error handling** - Enhanced error messages and validation
- ✅ **Props validation** - Enum validation, complex objects, edge cases
- ✅ **Performance** - Compilation, rendering, memory usage, complex scenarios
- ⚠️ **Icon preprocessing** - Jinja-specific `<icon:name>` syntax (not in Django)

## Intentionally Engine-Specific Features

### Django-Only Features (Will Not Port to Jinja)
1. **Django Framework Integration**
   - Context processors integration (`test_context_processors.py`)
   - CSRF middleware token propagation (`test_csrf.py`)
   - Django `{% includecontents %}` template tag class
   - Request object propagation through components
   - **Rationale**: These are Django-specific framework features

2. **Django Template Engine Features**
   - Prop definition caching and concurrency (`test_prop_definition_caching.py`)
   - Django-specific template loading and compilation optimizations
   - **Rationale**: Jinja has its own caching and optimization mechanisms

### Jinja-Only Features (Not in Django)
1. **Icon Preprocessing**
   - `<icon:name>` HTML syntax preprocessing
   - Icon system integration tests
   - **Rationale**: Jinja extension has tighter integration with icon preprocessing

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
Django Engine (99 tests)          →  Jinja Engine (80+ tests)
├── test_component_syntax.py      →  test_attributes.py + test_content_blocks.py
├── test_improved_error_messages.py → test_errors.py
├── test_template_error_messages.py → test_errors.py
├── test_props_validation.py      →  test_props.py
├── test_complex_nested_components.py → test_performance.py
├── test_prop_definition_caching.py → [Django-specific, not ported]
├── test_context_processors.py    →  [Django-specific, not ported]
└── test_csrf.py                  →  [Django-specific, not ported]
```

### Key Differences in Implementation
1. **Error Handling**: Jinja tests focus on compilation-time errors vs Django's render-time validation
2. **Performance Testing**: Jinja tests compilation speed, Django tests framework integration overhead
3. **Attribute Parsing**: Different syntax validation approaches between template engines
4. **Context Handling**: Django uses framework context stack, Jinja uses native Jinja context

## Validation Strategy

### Functional Parity Verification
- Both engines should produce equivalent output for core component features
- Attribute handling should work identically (class manipulation, JS events, template logic)
- Content block syntax should be interchangeable between engines
- Error messages should provide similar guidance and detail level

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

## Current Status: ⚠️ PARTIAL PARITY - GAPS IDENTIFIED

Comprehensive test coverage has been added for both engines, revealing **4 major implementation gaps** in the Jinja extension that prevent full parity:

### 🔴 Real Implementation Gaps in Jinja Extension

1. **JavaScript Framework Attributes** (Django ✅ → Jinja ❌)
   - `@click`, `@keyup.enter`, `@click.stop.prevent` syntax fails in Jinja
   - `v-on:submit`, `v-model`, `v-bind:` syntax fails in Jinja
   - `x-on:click`, `x-data`, `:class` syntax fails in Jinja
   - **Impact**: Cannot use modern JS frameworks (Vue, Alpine) with Jinja components

2. **Advanced Class Manipulation** (Django ✅ → Jinja ❌)
   - `class:not="condition ? 'class'"` syntax fails in Jinja
   - Class append/prepend with `& ` and ` &` syntax fails in Jinja
   - **Impact**: Cannot use conditional class logic in Jinja components

3. **Nested Attribute Syntax** (Django ✅ → Jinja ❌)
   - `inner.class="value"`, `button.type="submit"` syntax fails in Jinja
   - Attribute grouping and namespacing not supported
   - **Impact**: Cannot pass attributes to nested elements in Jinja components

4. **HTML Content Block Syntax** (Django ✅ → Jinja ❌)
   - `<content:name>Content</content:name>` syntax not implemented in Jinja
   - Must use traditional `{% contents name %}Content{% endcontents %}` syntax
   - **Impact**: Less intuitive content block syntax in Jinja

### ✅ Confirmed Working Features (Parity Achieved)

- ✅ **Basic component syntax**: `<include:component-name>`
- ✅ **Hyphenated component names**: `<include:card-with-footer>`
- ✅ **Self-closing syntax**: `<include:component />`
- ✅ **Props and enum validation**: Identical validation rules
- ✅ **Template variables in attributes**: `title="{{ variable }}"`
- ✅ **Named contents**: Traditional `{% contents %}` syntax
- ✅ **Error messages**: Both provide helpful validation errors
- ✅ **Performance**: Comparable compilation and rendering speed

### Implementation Priority for Jinja Extension

**High Priority** (Breaks modern web development patterns):
1. JavaScript framework attribute parsing (`@click`, `v-on:`, `x-on:`, `:bind`)
2. Nested attribute syntax (`inner.class`, `button.type`)

**Medium Priority** (Quality of life improvements):
3. HTML content block syntax (`<content:name>`)
4. Advanced class manipulation (`class:not`, `class="& base"`)

**Notes**: The gaps are in the Jinja extension's preprocessing layer, not the core component logic. The Django implementation provides the reference for desired syntax support.
