# Django IncludeContents Component Showcase

A comprehensive component library and documentation system for django-includecontents components.

## Features

### 🎨 Component Library Browser
- Automatic discovery of all components in your project
- Organized by categories (Forms, Layout, Navigation, etc.)
- Live component previews with real data
- Search and filter capabilities

### 🎛️ Interactive Prop Editor
- Real-time prop adjustment with instant preview updates
- Support for all prop types:
  - Text inputs for string props
  - Dropdowns for enum props
  - Checkboxes for boolean props
  - Number inputs for numeric props
- Content and content block editors

### 📋 Code Generation
- Automatic generation of Django template syntax
- HTML component syntax (`<include:component>`)
- Copy-to-clipboard functionality
- Live code updates as props change

### 📚 Rich Documentation
- Props reference with types and defaults
- Usage examples with loadable configurations
- Best practices guidelines
- Accessibility notes
- Related components

### 🎨 Design Tokens
- Visual design token library with live previews
- Color swatches, typography samples, spacing examples
- Copy-to-clipboard for CSS variables and values
- Organized by categories (Colors, Typography, Spacing, etc.)
- Style Dictionary compatible JSON format

## Installation

1. Add `showcase` to your `INSTALLED_APPS`:

```python
INSTALLED_APPS = [
    # ...
    'includecontents',
    'showcase',
]
```

2. Include the showcase URLs:

```python
from django.urls import include, path

urlpatterns = [
    # ...
    path('showcase/', include('showcase.urls')),
]
```

3. Run the development server:

```bash
python manage.py runserver
```

4. Visit `http://localhost:8000/showcase/` to browse components

## Adding Components to the Showcase

### Basic Components

Create component templates in `templates/components/`:

```html
{# templates/components/button.html #}
{# props text, variant=primary,secondary,danger #}
<button class="btn btn-{{ variant }}">
    {{ text }}
</button>
```

Components are automatically discovered and added to the showcase.

### Component Organization

Organize components using subdirectories:

```
templates/components/
├── forms/
│   ├── button.html
│   ├── input.html
│   └── select.html
├── layout/
│   ├── card.html
│   └── grid.html
└── feedback/
    ├── alert.html
    └── modal.html
```

### Adding Metadata

Create a YAML or TOML file alongside the component template for enhanced documentation:

```yaml
# templates/components/forms/button.yaml
name: Button
category: Forms
description: Interactive button component
props:
  variant:
    description: Visual style of the button
    type: enum
    values: [primary, secondary, danger]
  size:
    description: Button size
    type: enum
    values: [small, medium, large]
    default: medium
examples:
  - name: Primary Button
    code: |
      <include:button variant="primary">
        Click me
      </include:button>
    props:
      variant: primary
best_practices: |
  - Use primary for main actions
  - Limit to one primary button per form
accessibility: |
  - Ensure sufficient color contrast
  - Include descriptive labels
related: [forms:input, forms:select]
```

The metadata file must share the same filename (minus the `.html` extension) and live in the same directory. TOML is supported as `button.toml` if you prefer that format.

## Props System

### Prop Types

The showcase supports various prop types:

```html
{# String props #}
{# props title, subtitle="" #}

{# Boolean props #}
{# props visible=True, disabled=False #}

{# Number props #}
{# props count=0, max_items=10 #}

{# Enum props (comma-separated values) #}
{# props variant=primary,secondary,danger #}

{# Optional enum (empty first value) #}
{# props size=,small,medium,large #}
```

### Required vs Optional Props

```html
{# Required prop (no default value) #}
{# props title #}

{# Optional prop (with default) #}
{# props subtitle="" #}
```

## Component Categories

Components are automatically categorized based on:

1. **Directory structure**: Components in `forms/` → Forms category
2. **Component name**: Names containing "button", "input" → Forms
3. **Metadata file**: Explicitly set category in YAML

Default categories:
- **Forms**: Input fields, buttons, checkboxes
- **Layout**: Cards, grids, containers
- **Navigation**: Menus, breadcrumbs, tabs
- **Feedback**: Alerts, modals, toasts
- **Display**: Tables, lists, badges
- **Typography**: Headings, text blocks
- **Media**: Images, videos, galleries
- **Icons**: Icon components

## Design Tokens

Design tokens are design decisions represented as data. The showcase automatically discovers and displays design tokens from JSON files, providing a visual token library alongside your components.

### Adding Design Tokens

1. **Create Token Files**: Add JSON files to `showcase/`:

```json
{
  "color": {
    "primary": {
      "500": {
        "value": "#3b82f6",
        "type": "color",
        "description": "Primary brand color"
      }
    }
  }
}
```

2. **Token Structure**: Use the Style Dictionary format with:
   - `value`: The actual token value
   - `type`: Token type (`color`, `dimension`, `fontFamily`, etc.)
   - `description`: Human-readable description

3. **Access Tokens**: Visit `/showcase/tokens/` to browse the design token library

### Token Categories

Tokens are automatically categorized by path and type:
- **Colors**: Color palette and semantic colors
- **Typography**: Font families, sizes, weights, line heights
- **Spacing**: Spacing scale, margins, padding, border radius
- **Shadows**: Box shadows and elevation levels
- **Effects**: Transitions, animations, blur effects

### Using Tokens in Components

Reference tokens using CSS custom properties:

```html
{# Component using design tokens #}
<button style="
  background-color: var(--color-primary-500);
  padding: var(--spacing-md) var(--spacing-lg);
  border-radius: var(--border-radius-md);
  font-family: var(--font-family-primary);
">
  {{ label }}
</button>
```

### Token Features

- **Visual Previews**: Color swatches, typography samples, spacing examples
- **Copy-to-Clipboard**: Easy copying of CSS variables and raw values
- **Search Integration**: Find tokens alongside components
- **Live Examples**: See tokens in context with usage examples

## Advanced Features

### Content Blocks

Components can define named content areas:

```html
{# props title #}
<div class="card">
    <div class="card-header">{{ title }}</div>
    <div class="card-body">{{ contents }}</div>
    {% contents footer %}
    <div class="card-footer">{{ contents.footer }}</div>
    {% endcontents %}
</div>
```

The showcase automatically detects and provides editors for content blocks.

### Live Preview

The preview updates automatically as you:
- Change prop values
- Edit content
- Modify content blocks
- Switch between device sizes (mobile, desktop, wide)

### Search Functionality

Search components by:
- Component name
- Description
- Prop names
- Category

## Running the Example Project

An example project is included to demonstrate the showcase:

```bash
cd example_project
python manage.py migrate
python manage.py runserver
```

Visit `http://localhost:8000/` for the homepage and `/showcase/` for the component library.

## Customization

### Styling

Override the default styles by creating your own CSS:

```css
/* static/css/showcase-custom.css */
.showcase-sidebar {
    background: #f0f0f0;
}

.component-card {
    border-color: #e0e0e0;
}
```

### Adding Custom Categories

Extend the registry to add custom categories:

```python
# myapp/apps.py
from django.apps import AppConfig
from showcase.registry import registry

class MyAppConfig(AppConfig):
    name = 'myapp'

    def ready(self):
        # Add custom category detection
        registry._categories['Custom'] = []
```

## Best Practices

1. **Consistent Naming**: Use clear, descriptive component names
2. **Documentation**: Add metadata for all production components
3. **Examples**: Provide realistic usage examples
4. **Props Validation**: Use enum props for limited options
5. **Accessibility**: Include accessibility notes in metadata
6. **Organization**: Group related components in subdirectories

## Troubleshooting

### Components Not Appearing

- Ensure templates are in `templates/components/`
- Check that the template has a `.html` extension
- Verify the props comment syntax is correct
- Components starting with `_` are ignored

### Preview Not Updating

- Check browser console for JavaScript errors
- Ensure CSRF token is included in forms
- Verify the preview URL is accessible

### Metadata Not Loading

- Ensure a `.yaml`, `.yml`, or `.toml` file exists alongside the component template
- File name must match the template name (for example `button.html` → `button.yaml`)
- Verify the metadata syntax is valid

## Contributing

To contribute components to the showcase:

1. Create a component template with a `{# props ... #}` definition
2. Add a matching YAML/TOML sidecar with documentation and examples
3. Include usage examples
4. Test in different screen sizes
5. Ensure accessibility compliance

## License

Part of the django-includecontents project. See main LICENSE file.
