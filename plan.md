# Django-includecontents Template Loader Enhancement Plan

This plan addresses two related GitHub issues (#2 and #3) that improve how django-includecontents handles template loaders, making the package more user-friendly and reducing configuration complexity.

## Phase 1: Automatic Loader Replacement (Issue #2)

**Goal:** Automatically replace standard Django loaders with includecontents equivalents when manually specified

### Tasks:

1. **Update the engine to detect and replace loaders**
   - Modify `DjangoTemplates.__init__()` in `includecontents/django/engine.py`
   - Create a mapping of Django loaders to includecontents loaders
   - Implement `_replace_loaders()` method to handle:
     - Simple loader strings
     - Nested loaders (e.g., cached loader with child loaders)
     - Preservation of unknown custom loaders

2. **Add comprehensive tests**
   - Create `tests/test_loader_replacement.py`
   - Test simple loader replacement
   - Test cached loader with child loaders
   - Test unknown loader preservation
   - Test engine without manual loaders

### Expected Outcome:

Users can keep their existing Django settings with manually specified loaders, and includecontents will automatically enhance them with component resolution support.

## Phase 2: Debug-aware Cached Loader (Issue #3)

**Goal:** Add `cached_loader_unless_debug` option to automatically disable caching in development

### Tasks:

1. **Implement the new option**
   - Add `cached_loader_unless_debug` handling in engine initialization
   - Configure loaders based on Django's DEBUG setting:
     - `DEBUG=True`: Use non-cached loaders
     - `DEBUG=False`: Use cached loader for performance
   - Remove the option from OPTIONS dict (non-standard Django option)

2. **Add validation**
   - Detect conflicts when both `cached_loader_unless_debug` and `loaders` are specified
   - Raise `ImproperlyConfigured` with clear error message

3. **Add tests**
   - Create `tests/test_cached_loader_unless_debug.py`
   - Test `DEBUG=True` uses non-cached loaders
   - Test `DEBUG=False` uses cached loader
   - Test conflict detection
   - Test option set to False (should use defaults)

### Expected Outcome:

Developers can use a single boolean option instead of complex conditional loader configuration, improving the development experience.

## Phase 3: Documentation and Examples

**Goal:** Update documentation to showcase the new features

### Tasks:

1. **Update README/docs**
   - Document the automatic loader replacement behavior
   - Add `cached_loader_unless_debug` option documentation
   - Show example configurations

2. **Add migration guide**
   - Show how to simplify existing configurations
   - Explain the benefits of each feature

3. **Create changelog entry**
   - Add entries in `changes/` directory using towncrier format
   - Document both new features

## Phase 4: Integration Testing

**Goal:** Ensure the features work well together and with existing functionality

### Tasks:

1. **Test with real Django projects**
   - Test with various Django versions (4.1+)
   - Test with different template configurations
   - Ensure backward compatibility

2. **Performance testing**
   - Verify cached loader performance in production
   - Confirm no performance impact from loader replacement

3. **Edge case testing**
   - Complex loader configurations
   - Custom loader implementations
   - Multiple template engines

## Implementation Order:

1. **Phase 1 first** - Provides foundation for automatic loader handling
2. **Phase 2 next** - Builds on Phase 1's loader replacement logic
3. **Phase 3** - Document both features together
4. **Phase 4** - Final validation before release

## Benefits:

- **Simplified configuration:** No more manual loader specification in most cases
- **Better developer experience:** Templates auto-reload in development
- **Seamless upgrade path:** Existing configurations continue to work
- **Reduced boilerplate:** Eliminates the DEBUG-based loader dance

## Example Configuration (After Implementation)

### Before (Issue #2 example):

```python
_DEFAULT_LOADERS = [
    "django.template.loaders.filesystem.Loader",
    "django.template.loaders.app_directories.Loader",
]

_CACHED_LOADERS = [("django.template.loaders.cached.Loader", _DEFAULT_LOADERS)]

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "OPTIONS": {
            "loaders": _DEFAULT_LOADERS if DEBUG else _CACHED_LOADERS,
        },
    },
]
```

### After (with both features):

```python
TEMPLATES = [
    {
        "BACKEND": "includecontents.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "OPTIONS": {
            "cached_loader_unless_debug": True,
            # Loaders are automatically configured and replaced!
        },
    },
]
```

## Reference Implementation

### Phase 1: Automatic Loader Replacement

**File: `includecontents/django/engine.py`**

```python
from typing import Dict, Any, List, Union, Tuple
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.template.backends.django import DjangoTemplates
from django.template import EngineHandler

from .base import IncludeContentsTemplate


engines = EngineHandler()

# Mapping of standard Django loaders to their includecontents equivalents
LOADER_MAPPING = {
    "django.template.loaders.filesystem.Loader": "includecontents.django.loaders.filesystem.Loader",
    "django.template.loaders.app_directories.Loader": "includecontents.django.loaders.app_directories.Loader",
    "django.template.loaders.cached.Loader": "includecontents.django.loaders.cached.Loader",
}


class DjangoTemplates(DjangoTemplates):
    def __init__(self, params: Dict[str, Any]) -> None:
        params = params.copy()
        options = params.pop("OPTIONS").copy()

        # Check for conflicting options
        if "cached_loader_unless_debug" in options and "loaders" in options:
            raise ImproperlyConfigured(
                "Cannot specify both 'cached_loader_unless_debug' and 'loaders' options. "
                "Use 'loaders' for manual configuration or 'cached_loader_unless_debug' for automatic configuration."
            )

        # Handle cached_loader_unless_debug option
        if options.get("cached_loader_unless_debug", False):
            # Remove the option from OPTIONS as it's not a standard Django option
            options.pop("cached_loader_unless_debug")

            # Configure loaders based on DEBUG setting
            if getattr(settings, "DEBUG", False):
                # Use non-cached loaders in debug mode
                options["loaders"] = [
                    "includecontents.django.loaders.filesystem.Loader",
                    "includecontents.django.loaders.app_directories.Loader",
                ]
            else:
                # Use cached loader in production
                options["loaders"] = [(
                    "includecontents.django.loaders.cached.Loader",
                    [
                        "includecontents.django.loaders.filesystem.Loader",
                        "includecontents.django.loaders.app_directories.Loader",
                    ]
                )]
        elif "loaders" in options:
            # Replace standard loaders with includecontents loaders if manually specified
            options["loaders"] = self._replace_loaders(options["loaders"])

        params["OPTIONS"] = options
        super().__init__(params)

        # We need to reinitialize the engine with our custom template class
        self.engine = self.engine.engine
        self.engine.template_class = IncludeContentsTemplate

        # Override the engine handler to return our custom engine
        engines._engines[params["NAME"]] = self

    def _replace_loaders(self, loaders: List[Union[str, Tuple[str, List]]]) -> List[Union[str, Tuple[str, List]]]:
        """Replace standard Django loaders with their includecontents equivalents."""
        replaced_loaders = []

        for loader in loaders:
            if isinstance(loader, str):
                # Simple loader string
                replaced_loaders.append(LOADER_MAPPING.get(loader, loader))
            elif isinstance(loader, (list, tuple)) and len(loader) == 2:
                # Cached loader or similar: (loader_class, child_loaders)
                loader_class, child_loaders = loader
                replaced_loader_class = LOADER_MAPPING.get(loader_class, loader_class)
                replaced_child_loaders = self._replace_loaders(child_loaders)
                replaced_loaders.append((replaced_loader_class, replaced_child_loaders))
            else:
                # Unknown format, keep as is
                replaced_loaders.append(loader)

        return replaced_loaders
```

### Phase 1 Tests

**File: `tests/test_loader_replacement.py`**

```python
import pytest
from django.template import engines
from django.test import override_settings

from includecontents.django.engine import DjangoTemplates


class TestLoaderReplacement:
    def test_simple_loader_replacement(self):
        """Test that simple loader strings are replaced correctly."""
        engine = DjangoTemplates({
            "NAME": "test",
            "DIRS": [],
            "APP_DIRS": False,
            "OPTIONS": {
                "loaders": [
                    "django.template.loaders.filesystem.Loader",
                    "django.template.loaders.app_directories.Loader",
                ]
            }
        })

        # Check that loaders were replaced
        loaders = engine.engine.loaders
        assert len(loaders) == 2
        assert loaders[0].__class__.__module__ == "includecontents.django.loaders.filesystem"
        assert loaders[0].__class__.__name__ == "Loader"
        assert loaders[1].__class__.__module__ == "includecontents.django.loaders.app_directories"
        assert loaders[1].__class__.__name__ == "Loader"

    def test_cached_loader_replacement(self):
        """Test that cached loader with child loaders is replaced correctly."""
        engine = DjangoTemplates({
            "NAME": "test",
            "DIRS": [],
            "APP_DIRS": False,
            "OPTIONS": {
                "loaders": [(
                    "django.template.loaders.cached.Loader", [
                        "django.template.loaders.filesystem.Loader",
                        "django.template.loaders.app_directories.Loader",
                    ]
                )]
            }
        })

        # Check that cached loader was replaced
        loaders = engine.engine.loaders
        assert len(loaders) == 1
        cached_loader = loaders[0]
        assert cached_loader.__class__.__module__ == "includecontents.django.loaders.cached"
        assert cached_loader.__class__.__name__ == "Loader"

        # Check that child loaders were also replaced
        child_loaders = cached_loader.loaders
        assert len(child_loaders) == 2
        assert child_loaders[0].__class__.__module__ == "includecontents.django.loaders.filesystem"
        assert child_loaders[0].__class__.__name__ == "Loader"
        assert child_loaders[1].__class__.__module__ == "includecontents.django.loaders.app_directories"
        assert child_loaders[1].__class__.__name__ == "Loader"

    def test_unknown_loader_preserved(self):
        """Test that unknown loaders are preserved as-is."""
        engine = DjangoTemplates({
            "NAME": "test",
            "DIRS": [],
            "APP_DIRS": False,
            "OPTIONS": {
                "loaders": [
                    "some.custom.Loader",
                    "django.template.loaders.filesystem.Loader",
                ]
            }
        })

        # Check that unknown loader is preserved but known one is replaced
        loaders = engine.engine.loaders
        assert len(loaders) == 2
        assert loaders[0].__class__.__module__ == "some.custom"
        assert loaders[0].__class__.__name__ == "Loader"
        assert loaders[1].__class__.__module__ == "includecontents.django.loaders.filesystem"
        assert loaders[1].__class__.__name__ == "Loader"

    def test_no_loaders_specified(self):
        """Test that engine works correctly when no loaders are manually specified."""
        engine = DjangoTemplates({
            "NAME": "test",
            "DIRS": [],
            "APP_DIRS": True,
            "OPTIONS": {}
        })

        # Should work without errors and use default includecontents loaders
        assert engine.engine is not None
```

### Phase 2 Tests

**File: `tests/test_cached_loader_unless_debug.py`**

```python
import pytest
from django.core.exceptions import ImproperlyConfigured
from django.test import override_settings

from includecontents.django.engine import DjangoTemplates


class TestCachedLoaderUnlessDebug:
    @override_settings(DEBUG=True)
    def test_debug_mode_uses_non_cached_loaders(self):
        """Test that non-cached loaders are used when DEBUG=True."""
        engine = DjangoTemplates({
            "NAME": "test",
            "DIRS": [],
            "APP_DIRS": False,
            "OPTIONS": {
                "cached_loader_unless_debug": True
            }
        })

        # Check that non-cached loaders are used
        loaders = engine.engine.loaders
        assert len(loaders) == 2

        # Should have filesystem and app_directories loaders directly
        assert loaders[0].__class__.__module__ == "includecontents.django.loaders.filesystem"
        assert loaders[0].__class__.__name__ == "Loader"
        assert loaders[1].__class__.__module__ == "includecontents.django.loaders.app_directories"
        assert loaders[1].__class__.__name__ == "Loader"

    @override_settings(DEBUG=False)
    def test_production_mode_uses_cached_loader(self):
        """Test that cached loader is used when DEBUG=False."""
        engine = DjangoTemplates({
            "NAME": "test",
            "DIRS": [],
            "APP_DIRS": False,
            "OPTIONS": {
                "cached_loader_unless_debug": True
            }
        })

        # Check that cached loader is used
        loaders = engine.engine.loaders
        assert len(loaders) == 1

        # Should have cached loader wrapping the other loaders
        cached_loader = loaders[0]
        assert cached_loader.__class__.__module__ == "includecontents.django.loaders.cached"
        assert cached_loader.__class__.__name__ == "Loader"

        # Check child loaders
        child_loaders = cached_loader.loaders
        assert len(child_loaders) == 2
        assert child_loaders[0].__class__.__module__ == "includecontents.django.loaders.filesystem"
        assert child_loaders[0].__class__.__name__ == "Loader"
        assert child_loaders[1].__class__.__module__ == "includecontents.django.loaders.app_directories"
        assert child_loaders[1].__class__.__name__ == "Loader"

    def test_conflict_with_manual_loaders_raises_error(self):
        """Test that specifying both cached_loader_unless_debug and loaders raises an error."""
        with pytest.raises(ImproperlyConfigured) as exc_info:
            DjangoTemplates({
                "NAME": "test",
                "DIRS": [],
                "APP_DIRS": False,
                "OPTIONS": {
                    "cached_loader_unless_debug": True,
                    "loaders": ["django.template.loaders.filesystem.Loader"]
                }
            })

        assert "Cannot specify both 'cached_loader_unless_debug' and 'loaders'" in str(exc_info.value)

    def test_cached_loader_unless_debug_false_uses_default(self):
        """Test that cached_loader_unless_debug=False doesn't configure loaders."""
        engine = DjangoTemplates({
            "NAME": "test",
            "DIRS": [],
            "APP_DIRS": True,
            "OPTIONS": {
                "cached_loader_unless_debug": False
            }
        })

        # Should use default Django behavior (which includes our custom loaders via APP_DIRS)
        assert engine.engine is not None

    def test_no_cached_loader_option_with_manual_loaders(self):
        """Test that manual loaders work without cached_loader_unless_debug."""
        engine = DjangoTemplates({
            "NAME": "test",
            "DIRS": [],
            "APP_DIRS": False,
            "OPTIONS": {
                "loaders": ["django.template.loaders.filesystem.Loader"]
            }
        })

        # Should have the manually specified loader (replaced with includecontents version)
        loaders = engine.engine.loaders
        assert len(loaders) == 1
        assert loaders[0].__class__.__module__ == "includecontents.django.loaders.filesystem"
```