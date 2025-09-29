# Django IncludeContents Tests

## Running Tests

### Basic Test Suite
```bash
# Run all tests (excluding integration tests)
pytest

# Run with coverage
pytest --cov=includecontents --cov-report=html

# Run specific test file
pytest tests/django_engine/test_includecontents_tag.py -v

# Run tests for specific engine
pytest tests/django_engine/ -v
pytest tests/jinja_engine/ -v
```

### Integration Tests

The icon system includes integration tests that make real API calls to Iconify. These are disabled by default.

#### Running Integration Tests

```bash
# Enable and run integration tests
TEST_ICONIFY_API=1 pytest tests/shared/icons/test_integration.py -v

# Run ALL tests including integration
TEST_ICONIFY_API=1 pytest -v

# Show skipped tests and reasons
pytest -rs
```

#### Excluding Integration Tests

```bash
# Explicitly exclude integration tests (default behavior)
pytest -m "not integration"
```

## Test Organization

### Core Engine Tests

**Django Engine** (`tests/django_engine/`):
- `test_includecontents_tag.py` - Basic includecontents tag functionality
- `test_component_syntax.py` - HTML component syntax tests
- `test_csrf.py` - CSRF token handling
- `test_props_validation.py` - Component props validation
- `test_django_prop_types.py` - Django-specific prop types
- `test_context_processors.py` - Django context processor integration
- `test_improved_error_messages.py` - Enhanced error reporting

**Jinja2 Engine** (`tests/jinja_engine/`):
- `test_extension.py` - Core Jinja2 extension functionality
- `test_props.py` - Component props handling
- `test_content_blocks.py` - Content block support
- `test_context.py` - Context handling and isolation
- `test_csrf_integration.py` - CSRF token support
- `test_filesystem_components.py` - File-based component loading

**Shared Functionality** (`tests/shared/`):
- `test_prop_types.py` - Cross-engine prop type system
- `test_type_coercion.py` - Type conversion and validation
- `test_dataclass_props.py` - Dataclass-based props
- `test_multichoice.py` - Multi-choice prop validation
- `test_enhanced_errors.py` - Error handling improvements

### Icon System Tests

**Icon Core** (`tests/shared/icons/`):
- `test_builder.py` - Icon sprite building functionality
- `test_integration.py` - Iconify API integration tests
- `test_api_cache.py` - Icon caching system
- `test_validation.py` - Icon name validation

**Django Icon Tests** (`tests/django_engine/icons/`):
- `test_rendering.py` - Icon template tag rendering
- `test_accessibility_attributes.py` - ARIA and accessibility features
- `test_error_handling.py` - Icon error scenarios
- `test_local_svg_integration.py` - Local SVG file support

**Jinja2 Icon Tests** (`tests/jinja_engine/icons/`):
- `test_icon_rendering.py` - Jinja2 icon rendering
- `test_rendering.py` - Template integration
- `test_accessibility_attributes.py` - Accessibility support
- `test_error_handling.py` - Error handling
- `test_local_svg_integration.py` - Local SVG integration

### Template Feature Tests

**Template Features** (`tests/template_features/`):
- `test_multiline_support.py` - Multi-line tag support
- `test_wrapif.py` - Conditional wrapping tests
- `test_attrs_handling.py` - Attribute spreading functionality
- `test_template_tags_in_attrs.py` - Template tags in attributes
- `test_nested_content.py` - Nested component content

### Configuration Tests

**Config** (`tests/config/`):
- `test_finders.py` - Component discovery and loading
- `test_ignore_patterns.py` - File pattern exclusions

## Test Data

- `templates/` - Test template files organized by engine
- `static/icons/` - Test SVG files for local icon tests
- `test_icons_output/` - Generated sprite output (gitignored)
- `shared/` - Shared test utilities and fixtures