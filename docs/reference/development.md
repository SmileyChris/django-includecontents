# Development Guide

This guide is for developers who want to contribute to Django IncludeContents or understand its internals.

If you have not installed the project locally yet, follow the [Development Installation steps](../getting-started/installation.md#development-installation). For runtime issues while developing, keep the [Troubleshooting Guide](../reference/troubleshooting.md) close at hand.

## Quick Start for Contributors

### Setting Up Development Environment

1. **Clone the repository:**
   ```bash
   git clone https://github.com/SmileyChris/django-includecontents.git
   cd django-includecontents
   ```

2. **Install development dependencies:**
   ```bash
   # Install package with test dependencies
   pip install -e ".[test]"
   
   # Or install all dependencies (including deployment tools)
   pip install -e ".[test,deploy]"
   ```

3. **Run tests to verify setup:**
   ```bash
   # Run all tests
   pytest
   
   # Run with coverage
   pytest --cov=includecontents
   ```

### Development Workflow

#### Making Changes

1. **Create a feature branch:**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes** following the project's coding standards

3. **Write tests** for new functionality

4. **Run the test suite:**
   ```bash
   # Run all tests
   pytest
   
   # Run a specific test file
   pytest tests/test_tag.py
   
   # Run a specific test
   pytest tests/test_tag.py::test_basic -v
   ```

5. **Check code formatting** (if applicable):
   ```bash
   # Format Django/Jinja templates (requires npm)
   npm install
   npx prettier --write "**/{templates,jinja2}/**/*.html"
   ```

#### Testing Guidelines

- **Write tests for all new features**
- **Ensure existing tests pass**
- **Test both template tag and HTML component syntaxes**
- **Include edge cases and error conditions**

**Test Structure:**
```
tests/
├── settings.py          # Test Django settings
├── templates/           # Test templates
│   └── components/      # Test component templates
├── test_tag.py          # Template tag functionality
├── test_component.py    # HTML component syntax
├── test_csrf.py         # CSRF token propagation
└── test_multiline.py    # Multi-line tag support
```

### Creating Documentation

#### Running Documentation Locally

1. **Install documentation dependencies:**
   ```bash
   pip install -e ".[docs]"
   ```

2. **Serve documentation locally:**
   ```bash
   mkdocs serve
   ```

3. **Build documentation:**
   ```bash
   mkdocs build
   ```

#### Documentation Guidelines

- **Update relevant documentation** for any user-facing changes
- **Include code examples** in documentation
- **Test documentation examples** to ensure they work
- **Follow the existing documentation structure**

## Changelog Management

This project uses [towncrier](https://towncrier.readthedocs.io/) for changelog management.

### Adding Changelog Entries

**Create news fragments** for your changes in the `changes/` directory:

```bash
# Create a news fragment for a new feature
# Format: changes/+description.feature.md
echo "Description of the feature" > changes/+my-feature.feature.md

# Other fragment types:
# changes/+fix-name.bugfix.md     # Bug fixes
# changes/+docs.doc.md            # Documentation improvements
# changes/+remove-name.removal.md # Removals
# changes/+misc-name.misc.md      # Miscellaneous
```

### Fragment Naming Conventions

- **For new features**: `+descriptive-name.feature.md` 
- **For GitHub issue fixes**: `123.bugfix.md` (where 123 is the issue number)
- **For other bug fixes**: `+fix-description.bugfix.md`
- **For documentation**: `+docs-description.doc.md`
- **For removals**: `+remove-description.removal.md`
- **For miscellaneous**: `+misc-description.misc.md`

### Examples

```bash
# New feature (use + prefix with description):
echo "Add support for Django template tags in component attributes" > changes/+template-tags-in-attributes.feature.md

# GitHub issue fix (use issue number):
echo "Fix component rendering with special characters" > changes/42.bugfix.md

# Other bug fix (use + prefix):
echo "Fix memory leak in template caching" > changes/+fix-memory-leak.bugfix.md
```

**Important:** Never edit `CHANGES.md` directly - it's generated automatically by towncrier during releases.

## Architecture Overview

### Package Structure

```
includecontents/
├── __init__.py                     # Package initialization
├── templatetags/
│   └── includecontents.py         # Core template tag implementation
├── django/
│   ├── __init__.py
│   ├── base.py                     # Custom template engine base
│   ├── engine.py                   # Custom Django template engine
│   └── loaders.py                  # Template loaders
└── next_version.py                 # Version management
```

### Key Components

#### 1. Template Tag (`templatetags/includecontents.py`)

- **Core `{% includecontents %}` tag implementation**
- **Context isolation logic**
- **Content block processing**
- **Props validation**

#### 2. Custom Template Engine (`django/`)

- **HTML component syntax parsing** (`base.py`)
- **Template engine integration** (`engine.py`)
- **Custom template loaders** (`loaders.py`)

#### 3. Testing Framework (`tests/`)

- **Comprehensive test suite**
- **Test templates and components**
- **Integration and unit tests**

### Design Principles

1. **Context Isolation**: Components run in isolated contexts for predictability
2. **Backward Compatibility**: Template tag syntax always supported
3. **HTML-like Syntax**: Modern component syntax feels familiar
4. **Django Integration**: Works seamlessly with Django's template system

## Contributing Guidelines

### Code Standards

- **Follow Django coding conventions**
- **Write comprehensive tests**
- **Document new features**
- **Maintain backward compatibility**

### Pull Request Process

1. **Fork the repository**
2. **Create a feature branch**
3. **Make your changes with tests**
4. **Create changelog fragment**
5. **Submit pull request**

### Getting Help

- **GitHub Issues**: Bug reports and feature requests
- **Discussions**: Questions and community help
- **Documentation**: Complete feature documentation

## Troubleshooting Development Issues

### Common Setup Issues

**Tests not running:**
```bash
# Ensure you're in the project directory
cd django-includecontents

# Install in development mode
pip install -e ".[test]"

# Run tests with verbose output
pytest -v
```

**Documentation not building:**
```bash
# Install docs dependencies
pip install -e ".[docs]"

# Check for missing dependencies
mkdocs build --verbose
```

### Debugging Tips

1. **Use `uv run` for consistent environments**
2. **Enable Django template debugging**
3. **Run specific test files for faster feedback**
4. **Use print statements in template tags for debugging**

### Enhanced Error Messages and Debugging

Django IncludeContents provides enhanced error messages and debugging features to improve the development experience:

#### Registry Introspection

Use these helpers to debug component registration issues:

```python
from includecontents.props import list_registered_components, resolve_props_class_for

# List all registered components
components = list_registered_components()
print("Registered components:", components)

# Debug path resolution
props_class = resolve_props_class_for('/app/templates/components/card.html')
print("Resolved props class:", props_class)
```

#### Enhanced Error Context

Validation errors now include comprehensive context (Python 3.11+ uses `Exception.add_note()`):

```python
# Example enhanced error output:
# TemplateSyntaxError: Props validation failed: email: Enter a valid email address
# Component: components/user-card.html
# Props class: UserCardProps
#   • email: Enter a valid email address
#   • age: Cannot convert 'abc' to integer
```

#### Debug Logging

Enable debug logging to see registry lookup attempts:

```python
# settings.py
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'includecontents.props': {
            'handlers': ['console'],
            'level': 'DEBUG',
        },
        'includecontents.templatetags.includecontents': {
            'handlers': ['console'],
            'level': 'DEBUG',
        },
    },
}
```

Debug output includes:
- Registry collision warnings
- Props cache hit/miss information
- Component lookup candidates when resolution fails
- Sample of registered components for comparison

#### Registry Collision Detection

The system automatically detects and warns about duplicate component registrations:

```python
@component('components/button.html')
class ButtonProps:
    text: str

@component('components/button.html')  # Duplicate!
class DuplicateButtonProps:
    label: str

# Logs: WARNING: Component already registered for 'components/button.html'.
# Previous: ButtonProps, New: DuplicateButtonProps (keeping first)
```

#### Thread Safety Considerations

The component registry is designed for production use:

- **Startup Registration**: Components should be registered during Django startup (typically in `apps.py` or module imports)
- **Runtime Read-Only**: Once Django has started, the registry is effectively read-only
- **Thread Safe**: Multiple threads can safely read from the registry simultaneously
- **Testing**: Use `clear_registry()` to reset state between tests

## Release Process

The release process for Django IncludeContents uses manual GitHub Actions workflows for complete control over releases.

### Creating a Release

**1. Ensure there are changelog fragments** for changes (see Changelog Management above)

**2. Run the Release workflow:**

   - Go to the [GitHub repository Actions tab](https://github.com/SmileyChris/django-includecontents/actions)
   - Select **"Release new version"** workflow
   - Click **"Run workflow"**
   - Choose the version bump type: `patch`, `minor`, or `major`

!!! note "The release workflow will automatically:"
    1. Calculate the next version number
    1. Generate changelog from fragments using towncrier
    1. Commit the updated CHANGES.md
    1. Create and push a git tag
    1. Create a GitHub release with release notes

**3. Deploy to PyPI:**

   - Go to the [GitHub repository Actions tab](https://github.com/SmileyChris/django-includecontents/actions)
   - Select **"Publish to PyPI"** workflow
   - Click **"Run workflow"**
   - Confirm the deployment

### Deploy Manually (Alternative)

If you need to deploy without using the GitHub Actions workflow:

**1. Install dependencies:**
   ```bash
   python -m pip install -e .[deploy]
   python -m pip install towncrier
   ```

**2. Get next version number:**
   ```bash
   # Replace 'patch' with 'minor' or 'major' as needed
   export VERSION=$(python -m includecontents.next_version patch)
   echo "Next version: $VERSION"
   ```

**3. Generate release notes:**
   ```bash
   towncrier build --draft --version $VERSION
   ```

**4. Build full changelog:**
   ```bash
   towncrier build --yes --name "Version" --version $VERSION
   ```

**5. Commit changelog and create tag:**
   ```bash
   git config user.name "Your Name"
   git config user.email "your.email@example.com"
   git commit -am "Update CHANGES for $VERSION"
   git tag "v$VERSION" --file=/tmp/changes.txt --cleanup=whitespace
   git push --follow-tags
   ```

**6. Create GitHub release:**
   ```bash
   gh release create "v$VERSION" --title "$VERSION" --notes-from-tag --verify-tag
   ```

**7. Deploy to PyPI:**
   ```bash
   # Ensure you're on the release version
   python -m includecontents.next_version
   # Publish to PyPI
   pdm publish
   ```

!!! warning "Manual Deployment"
    Manual deployment bypasses the automated checks and should only be used in exceptional circumstances. The GitHub Actions workflow is the preferred method.

### Release Checklist

- [ ] All tests pass
- [ ] Documentation is updated
- [ ] Changelog fragment created in `changes/` directory
- [ ] "Release new version" workflow completed successfully
- [ ] GitHub release created with correct version and notes
- [ ] "Publish to PyPI" workflow completed successfully
- [ ] Package available on PyPI
- [ ] Release announcement (if applicable)

## Next Steps

- Verify runtime behaviour with the [Troubleshooting Guide](../reference/troubleshooting.md)
- Ensure feature docs stay aligned by updating the [API Reference](../reference/api-reference.md) and topic guides such as [Component Props Validation](../prop-validation.md)
- Configure your local tooling using [Custom Template Engine](../tooling-integration/custom-engine.md) and related setup guides in `tooling-integration/`

---

## Changelog

This page shows the complete changelog for Django IncludeContents.

The full changelog is maintained in [CHANGES.md](https://github.com/SmileyChris/django-includecontents/blob/main/CHANGES.md) and is automatically generated using [towncrier](https://towncrier.readthedocs.io/).

### Latest Changes

--8<-- "CHANGES.md"
