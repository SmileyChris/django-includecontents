# Django IncludeContents Tests

## Running Tests

### Basic Test Suite
```bash
# Run all tests (excluding integration tests)
pytest

# Run with coverage
pytest --cov=includecontents --cov-report=html

# Run specific test file
pytest tests/test_icons.py -v
```

### Integration Tests

The icon system includes integration tests that make real API calls to Iconify. These are disabled by default.

#### Running Integration Tests

```bash
# Enable and run integration tests
TEST_ICONIFY_API=1 pytest tests/test_icons_integration.py -v

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

- `test_tag.py` - Basic includecontents tag functionality
- `test_component.py` - HTML component syntax tests
- `test_icons.py` - Icon system unit tests (no external calls)
- `test_icons_integration.py` - Icon system integration tests (Iconify API)
- `test_csrf.py` - CSRF token handling
- `test_multiline.py` - Multi-line tag support
- `test_wrapif.py` - Conditional wrapping tests
- `test_attrs_spread.py` - Attribute spreading functionality

## Test Data

- `templates/` - Test template files
- `static/icons/` - Test SVG files for local icon tests
- `test_icons_output/` - Generated sprite output (gitignored)