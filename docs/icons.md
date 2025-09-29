# Icons

The django-includecontents icons system generates SVG sprite sheets from both Iconify icons and your local SVG files.

!!! info "Template Engine Support"
    The icon system supports both template engines:

    - **Django Templates**: Both `{% icon "home" %}` tags and `<icon:home />` HTML syntax
    - **Jinja2**: HTML syntax `<icon:home />` via preprocessing (icon template tags coming soon)

    Icon sprite generation works identically for both engines.

## How Component Names Work

When you configure icons, they're automatically given component names based on simple rules:

- **Iconify icons**: `'mdi:home'` → `<icon:home>` (uses part after colon)
- **Local SVG files**: `'icons/logo.svg'` → `<icon:logo>` (uses filename without extension)  
- **Custom names**: `('brand', 'icons/company.svg')` → `<icon:brand>` (uses your custom name)

## Quick Start

### 1. Configuration

First, add the icon finder to your static files settings:

```python
# settings.py
STATICFILES_FINDERS = [
    'includecontents.icons.finders.IconSpriteFinder',  # Must be first for icons
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
]
```

!!! important "Finder Order"
    The `IconSpriteFinder` must be listed **first** in `STATICFILES_FINDERS`. This ensures that source SVG files are automatically excluded from other finders, preventing them from being served both individually and as part of the sprite.

Then configure your icons:

```python
# settings.py
INCLUDECONTENTS_ICONS = {
    'icons': [
        # Iconify icons - 'mdi:home' becomes <icon:home>
        'mdi:home',
        'tabler:user',
        
        # Local SVG files - 'icons/logo.svg' becomes <icon:logo>
        'icons/logo.svg',
        
        # Custom names - override the automatic naming
        ('nav', 'tabler:navigation'),        # Use <icon:nav> instead of <icon:navigation>
        ('brand', 'assets/company-logo.svg'),  # Use <icon:brand> instead of <icon:company-logo>
    ]
}
```

### 2. Usage

```html
<!-- Iconify icons -->
<icon:home class="w-6 h-6" />      <!-- Uses 'mdi:home' -->
<icon:user class="avatar" />       <!-- Uses 'tabler:user' -->

<!-- Local SVG files -->
<icon:logo class="header-logo" />  <!-- Uses 'icons/logo.svg' -->

<!-- Custom names -->
<icon:nav class="navigation" />    <!-- Uses 'tabler:navigation' with shorter name -->
<icon:brand class="footer" />      <!-- Uses 'assets/company-logo.svg' with shorter name -->

<!-- Advanced attributes -->
<icon:user role="img" aria-label="User profile" />
```

!!! important "Custom Template Engine Required"
    The `<icon:.../>` HTML syntax requires the [custom template engine](tooling-integration/custom-engine.md). If you're using Django's standard template engine, use the template tag syntax instead:
    
    ```html
    {% load icons %}
    {% icon "home" class="w-6 h-6" %}
    {% icon "user" class="avatar" %}
    ```

## Icon Sources

### Iconify Icons
Choose from thousands of icons: `mdi:home`, `tabler:calendar`, `lucide:star`, etc.
See [iconify.design](https://iconify.design/) for available icons.

**Component Naming:**
- `'mdi:home'` → use as `<icon:home>`
- `'tabler:calendar'` → use as `<icon:calendar>`
- `'lucide:star'` → use as `<icon:star>`

The component name is the part after the colon (`:`).

### Local SVG Files
Place SVG files in your static directories:
- `myapp/static/icons/logo.svg` → `'icons/logo.svg'` → use as `<icon:logo>`
- `static/logos/brand.svg` → `'logos/brand.svg'` → use as `<icon:brand>`

Files are found using Django's static file system (`staticfiles`).

**Automatic SVG Cleaning**: Local SVG files are automatically cleaned when added to sprites. The cleaning process:
- Removes metadata, comments, and non-essential elements (like Inkscape-specific data)
- Strips problematic attributes: `width`, `height`, `x`, `y`, `class`, `id`
- Removes namespaced attributes (e.g., `inkscape:*`, `sodipodi:*`)
- **Preserves** `style` attributes that contain CSS variables (e.g., `style="fill: var(--icon-color)"`)
- Removes regular inline styles without CSS variables to prevent conflicts
- Keeps all drawing elements (`path`, `circle`, `rect`, `g`, `defs`, gradients, filters, etc.)

This ensures your icons work correctly in sprite sheets, reduces file size, and enables advanced styling with CSS variables (see [Styling with CSS Variables](icons/styling-with-css-variables.md)).

**Component Naming:**
The component name is the filename without extension:
- `'icons/logo.svg'` → use as `<icon:logo>`
- `'assets/nav-home.svg'` → use as `<icon:nav-home>`

## Custom Names

Use tuples to create custom component names when you want something different from the automatic naming:

```python
INCLUDECONTENTS_ICONS = {
    'icons': [
        ('home', 'mdi:house'),                    # <icon:home> uses mdi:house (instead of <icon:house>)
        ('logo', 'assets/very-long-company-name.svg'),  # <icon:logo> instead of <icon:very-long-company-name>
        ('nav', 'tabler:navigation'),             # <icon:nav> uses tabler:navigation (instead of <icon:navigation>)
    ]
}
```

**When to use custom names:**
- **Shorter names**: `('nav', 'tabler:navigation')` → `<icon:nav>` instead of `<icon:navigation>`
- **Consistent naming**: `('user', 'mdi:account')` → `<icon:user>` instead of `<icon:account>`
- **Avoid conflicts**: When two icons would have the same auto-generated name

## Iconify API Caching (Optional)

To reduce API calls and enable offline development, you can cache Iconify icons locally:

```python
# settings.py
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

INCLUDECONTENTS_ICONS = {
    'icons': [...],
    
    # Cache configuration
    'api_cache_root': BASE_DIR / 'static' / '.icon_cache',  # Where to write cached icons
    'api_cache_static_path': '.icon_cache',                 # Where to read cached icons from static files
}
```

This creates a cache structure like:
```
static/.icon_cache/
├── mdi/
│   ├── home.json
│   └── account.json
├── tabler/
│   └── user.json
```

**Benefits:**
- Icons are fetched from Iconify API only once
- Subsequent builds use local cached copies
- Works offline after initial fetch
- Can be committed to version control for reproducible builds

**Notes:**
- Cache is optional - leave settings undefined to disable
- Only caches Iconify icons, not local SVG files
- Each icon cached individually for incremental updates

## Configuration Options

All available configuration options for `INCLUDECONTENTS_ICONS`:

```python
# settings.py
INCLUDECONTENTS_ICONS = {
    # Required: List of icons
    'icons': [
        'mdi:home',
        'icons/logo.svg',
        ('custom', 'tabler:star'),
    ],
    
    # Optional settings
    'dev_mode': True,                    # Development features
    'cache_timeout': 3600,               # Cache timeout (seconds)
    'api_base': 'https://api.iconify.design',  # Iconify API URL
    
    # Optional cache settings (see Iconify API Caching section above)
    'api_cache_root': Path('static/.icon_cache'),      # Filesystem path for writing cached icons
    'api_cache_static_path': '.icon_cache',            # Static files path for reading cached icons
}
```

## Template Usage

### HTML Component Syntax (Requires Custom Engine)

The `<icon:.../>` syntax requires the [custom template engine](tooling-integration/custom-engine.md):

```html
<icon:home class="nav-icon" />
<icon:user class="avatar" use.fill="currentColor" />
```

### Template Tags (Works with Any Engine)

The template tag syntax works with both standard Django and custom engines:

```html
{% load icons %}
{% icon "home" class="nav-icon" %}
{% icon "user" as user_icon %}  <!-- Store in variable instead of rendering -->
{% icons_inline %}  <!-- Development mode -->
```

## Advanced Features

### Conditional Icon Rendering

Use the `as variable_name` syntax to store icon HTML in a template variable instead of rendering immediately. This allows you to conditionally render icons or test if they exist:

```html
{% load icons %}

<!-- Store icon in variable -->
{% icon "home" class="nav-icon" as home_icon %}

<!-- Use conditionally -->
{% if home_icon %}
    <button>{{ home_icon }} Go Home</button>
{% endif %}

<!-- Or render directly when needed -->
<div class="sidebar">{{ home_icon }}</div>
```

**Invalid icons behavior**: If you request an icon that doesn't exist in your configuration, it will render as an empty string rather than broken HTML.

```html
{% icon "non-existent-icon" as missing_icon %}
{% if missing_icon %}
    This won't show since the icon doesn't exist
{% else %}
    <span>Icon not available</span>
{% endif %}
```

### Attribute Separation
Use `use.*` to control SVG vs USE element attributes:

```html
<icon:star 
    class="icon-wrapper" 
    role="img"
    aria-label="Favorite item"
    use.fill="gold" 
    use.stroke="orange" />
```

Generates:
```html
<svg class="icon-wrapper" role="img" aria-label="Favorite item">
  <use fill="gold" stroke="orange" href="/static/icons/sprite-abc123.svg#star"></use>
</svg>
```

### Static File Integration

Icons are automatically integrated with Django's static file system:

- **Automatic generation**: Sprites created on-demand when requested
- **Seamless integration**: Works with `collectstatic`, `findstatic`, and development server
- **Cache-friendly**: Uses Django's static file versioning and CDN support
- **No build step**: No separate management commands needed
- **Strict validation**: Build fails fast on any missing icons

## How It Works

Icons work automatically with Django's static file system:
- `python manage.py collectstatic` (production)
- `python manage.py findstatic icons/sprite-*.svg` (debugging)  
- Django development server (development)

The `IconSpriteFinder` generates sprites on-demand when requested, integrating seamlessly with Django's static file handling.

### Generated Output

When you use `<icon:home>`, it generates:

```html
<svg class="your-classes">
  <use href="/static/icons/sprite-abc123def.svg#home"></use>
</svg>
```

**Key parts:**
- `/static/icons/sprite-abc123def.svg` - Django static file URL to the generated sprite
- `#home` - Fragment identifier pointing to the specific icon symbol in the sprite (uses component name)
- The hash (`abc123def`) changes when your icon configuration changes, enabling cache busting

## Best Practices

### File Organization
```
static/
├── icons/
│   ├── nav/
│   │   ├── home.svg
│   │   └── profile.svg
│   └── ui/
│       ├── star.svg
│       └── heart.svg
└── logos/
    ├── brand.svg
    └── partner.svg
```

### Configuration
```python
INCLUDECONTENTS_ICONS = {
    'icons': [
        # Navigation icons
        ('nav-home', 'icons/nav/home.svg'),
        ('nav-profile', 'icons/nav/profile.svg'),
        
        # UI icons from Iconify
        ('ui-star', 'mdi:star'),
        ('ui-heart', 'mdi:heart'),
        
        # Brand assets
        ('logo', 'logos/brand.svg'),
        ('partner-logo', 'logos/partner.svg'),
    ]
}
```

### Accessibility
```html
<!-- Decorative icon -->
<icon:star aria-hidden="true" />

<!-- Meaningful icon -->
<icon:home role="img" aria-label="Go to homepage" />

<!-- Button with icon -->
<button>
  <icon:save aria-hidden="true" />
  Save Document
</button>
```

## Troubleshooting

**Icons not rendering:**
- Check `INCLUDECONTENTS_ICONS` configuration
- Verify static files are properly configured
- Ensure `includecontents` is in `INSTALLED_APPS`

**Local SVG files not found:**
- Check file exists: `python manage.py findstatic icons/logo.svg`
- Verify `STATICFILES_DIRS` or app static directories
- Ensure file path matches configuration

**Template syntax errors:**
- Use quotes around icon names in template tags
- Check for typos in icon names
- Verify custom template engine is configured

## Next Steps

- Style sprites with CSS variables using [Advanced Icon Styling](icons/styling-with-css-variables.md)
- Configure formatter and tooling support in [Prettier Formatting](tooling-integration/prettier-formatting.md) and [VS Code Setup](tooling-integration/vscode-setup.md)
- Review icon template helpers in the [API Reference](reference/api-reference.md#icon)
