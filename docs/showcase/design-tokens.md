# Design Tokens

Design tokens are design decisions represented as data — ensuring consistency across your design system. The showcase includes built-in support for displaying, documenting, and copying design tokens alongside your components.

## Overview

Design tokens capture design decisions like colors, typography, spacing, and shadows in a format that can be shared across design and development tools. The showcase automatically discovers and displays tokens from multiple sources, providing:

- **Visual Previews**: Color swatches, spacing examples, typography samples
- **Interactive Documentation**: Detailed token information with usage examples
- **Copy-to-Clipboard**: Easy copying of CSS variables and raw values
- **Search Integration**: Find tokens alongside components
- **Category Organization**: Automatic grouping by token type

## Token Sources

The showcase supports three types of design tokens, automatically discovered and displayed separately:

### 1. Style Dictionary Tokens
JSON-based tokens following the [Style Dictionary](https://amzn.github.io/style-dictionary/) format.
**Access**: `/showcase/tokens/`

### 2. Tailwind CSS 4.0 @theme Tokens
CSS custom properties defined using Tailwind's new `@theme` directive.
**Access**: `/showcase/tailwind/`

### 3. Tailwind Config Tokens
Design tokens from `tailwind.config.js` theme configuration.
**Access**: `/showcase/tailwind/`

## Quick Start

### Style Dictionary Tokens

1. **Create Token Files**: Use the Style Dictionary format in `showcase/`:

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

### Tailwind 4.0 @theme Tokens

1. **Create CSS Theme Files**: Use Tailwind's `@theme` directive:

```css
/* static/css/theme.css */
@theme {
  --color-primary: #3b82f6;
  --color-secondary: #64748b;
  --spacing-lg: 2rem;
  --font-family-heading: 'Inter', sans-serif;
}
```

### Tailwind Config Tokens

1. **Configure tailwind.config.js**: Define theme extensions:

```javascript
// tailwind.config.js
module.exports = {
  theme: {
    extend: {
      colors: {
        primary: '#3b82f6',
        secondary: '#64748b'
      },
      spacing: {
        'lg': '2rem'
      }
    }
  }
}
```

## Automatic Discovery

The showcase automatically discovers tokens from:
- JSON files in `showcase/` directory (Style Dictionary)
- CSS files with `@theme` directives (Tailwind 4.0)
- `tailwind.config.js` theme configuration (Tailwind legacy)

Run the discovery command to refresh tokens:
```bash
python manage.py import_tailwind_tokens
```

## Token File Format

Design tokens use a hierarchical JSON structure compatible with [Style Dictionary](https://amzn.github.io/style-dictionary/):

### Basic Structure

```json
{
  "category": {
    "subcategory": {
      "token-name": {
        "value": "actual-value",
        "type": "token-type",
        "description": "Human-readable description"
      }
    }
  }
}
```

### Required Properties

- **`value`**: The actual token value (color hex, dimension, font family, etc.)
- **`type`**: Token type for proper rendering (`color`, `dimension`, `fontFamily`, etc.)

### Optional Properties

- **`description`**: Human-readable description of the token's purpose
- **`css_variable`**: Custom CSS variable name (auto-generated if not provided)

## Token Types

The showcase supports various token types with specialized previews:

### Colors

```json
{
  "color": {
    "primary": {
      "blue": {
        "value": "#3b82f6",
        "type": "color",
        "description": "Primary brand blue"
      }
    },
    "semantic": {
      "success": {
        "value": "#10b981",
        "type": "color",
        "description": "Success state color"
      }
    }
  }
}
```

**Preview**: Color swatches with hex values and contrast indicators

### Typography

```json
{
  "font": {
    "family": {
      "sans": {
        "value": "Inter, system-ui, sans-serif",
        "type": "fontFamily",
        "description": "Primary sans-serif font stack"
      }
    },
    "size": {
      "base": {
        "value": "1rem",
        "type": "fontSize",
        "description": "Base font size (16px)"
      }
    },
    "weight": {
      "medium": {
        "value": 500,
        "type": "fontWeight",
        "description": "Medium font weight"
      }
    }
  }
}
```

**Preview**: Live font samples showing typeface, size, and weight

### Spacing & Dimensions

```json
{
  "spacing": {
    "base": {
      "value": "1rem",
      "type": "dimension",
      "description": "Base spacing unit (16px)"
    }
  },
  "borderRadius": {
    "medium": {
      "value": "0.5rem",
      "type": "dimension",
      "description": "Medium border radius (8px)"
    }
  }
}
```

**Preview**: Visual bars showing relative sizes with pixel equivalents

### Shadows

```json
{
  "shadow": {
    "card": {
      "value": "0 4px 6px -1px rgba(0, 0, 0, 0.1)",
      "type": "boxShadow",
      "description": "Subtle shadow for cards"
    }
  }
}
```

**Preview**: Shadow examples applied to preview elements

## Tailwind Token Features

Tailwind tokens come with additional features specific to Tailwind CSS workflows:

### Visual Previews

All Tailwind token types get enhanced visual previews:

- **Colors**: Color swatches with hex/rgb values
- **Spacing**: Visual bars showing relative sizes
- **Typography**: Live font samples and size demonstrations
- **Shadows**: Actual shadow effects applied to demo elements
- **Border Radius**: Rounded corner demonstrations
- **Opacity**: Transparency effects with checkered backgrounds

### Utility Class Generation

Tailwind tokens automatically generate corresponding utility classes:

```css
/* From @theme token: --color-primary: #3b82f6 */
.text-primary { color: #3b82f6; }
.bg-primary { background-color: #3b82f6; }
.border-primary { border-color: #3b82f6; }

/* From config token: spacing.lg: '2rem' */
.p-lg { padding: 2rem; }
.m-lg { margin: 2rem; }
.gap-lg { gap: 2rem; }
```

### Framework Examples

Each token shows usage examples for multiple frameworks:

**React Example:**
```jsx
const styles = {
  backgroundColor: '#3b82f6'  // token value
};
```

**Vue Template:**
```vue
<div :style="{ backgroundColor: '#3b82f6' }">
  Content
</div>
```

**CSS Usage:**
```css
.element {
  background-color: #3b82f6;
}
```

### Source Attribution

Tokens are labeled by their source:
- **Tailwind @theme**: CSS custom properties from `@theme` blocks
- **tailwind.config.js**: JavaScript configuration objects

### Smart Categorization

Tailwind tokens are automatically categorized for better organization:
- **brand-colors**: Primary, secondary, accent colors
- **semantic-colors**: Success, error, warning colors
- **typography**: Font families, sizes, weights
- **spacing**: Padding, margin, gap values
- **shadows**: Box shadow definitions
- **miscellaneous**: Border radius, opacity, other values

## File Organization

Organize tokens across multiple files for better maintainability:

```
showcase/
├── colors.json          # Color palette
├── typography.json      # Font families, sizes, weights
├── spacing.json         # Spacing scale, border radius
├── shadows.json         # Box shadows, elevations
└── animations.json      # Transitions, durations
```

Each file is processed independently, allowing you to organize tokens by system area.

## Automatic Features

### Type Detection

If you omit the `type` property, the showcase attempts to detect the token type:

```json
{
  "color": {
    "primary": {
      "value": "#3b82f6"
      // Type automatically detected as "color"
    }
  },
  "spacing": {
    "large": {
      "value": "2rem"
      // Type automatically detected as "dimension"
    }
  }
}
```

### Category Organization

Tokens are automatically categorized based on their path and type:

- `color.*` → Colors category
- `font.*`, `text.*`, `typography.*` → Typography category
- `spacing.*`, `space.*`, `gap.*` → Spacing category
- `shadow.*`, `elevation.*` → Shadows category
- Everything else → Miscellaneous category

### CSS Variable Generation

CSS custom property names are automatically generated from token paths:

```json
{
  "color": {
    "primary": {
      "500": {
        "value": "#3b82f6"
        // Generates: --color-primary-500
      }
    }
  }
}
```

Override with custom names:

```json
{
  "color": {
    "primary": {
      "500": {
        "value": "#3b82f6",
        "css_variable": "--brand-primary"
      }
    }
  }
}
```

## Usage Examples

### In Components

Reference tokens in your component templates:

```html
{# templates/components/button.html #}
{# props variant=primary,secondary #}
<button {% attrs
  class="btn"
  style="
    background-color: var(--color-primary-500);
    padding: var(--spacing-3) var(--spacing-6);
    border-radius: var(--border-radius-md);
    font-family: var(--font-family-sans);
  "
%}>
  {{ contents }}
</button>
```

### In CSS

Use generated CSS variables:

```css
.card {
  background: white;
  padding: var(--spacing-6);
  border-radius: var(--border-radius-lg);
  box-shadow: var(--shadow-card);
  font-family: var(--font-family-sans);
}

.button-primary {
  background: var(--color-primary-500);
  color: var(--color-primary-50);
}
```

### In JavaScript/CSS-in-JS

Copy token values for use in JavaScript:

```javascript
const theme = {
  colors: {
    primary: '#3b82f6',      // Copied from token detail
    secondary: '#64748b',
  },
  spacing: {
    base: '1rem',           // Copied from token detail
    large: '2rem',
  }
};
```

## Advanced Features

### Token Aliases

Reference other tokens within your token definitions:

```json
{
  "color": {
    "blue": {
      "500": {
        "value": "#3b82f6"
      }
    },
    "primary": {
      "value": "{color.blue.500}",
      "type": "color",
      "description": "Primary color aliases blue-500"
    }
  }
}
```

### Contextual Tokens

Create context-specific token variants:

```json
{
  "color": {
    "text": {
      "primary": {
        "light": {
          "value": "#111827",
          "type": "color",
          "description": "Primary text on light backgrounds"
        },
        "dark": {
          "value": "#f9fafb",
          "type": "color",
          "description": "Primary text on dark backgrounds"
        }
      }
    }
  }
}
```

### Semantic Tokens

Define purpose-driven tokens:

```json
{
  "color": {
    "semantic": {
      "success": {
        "value": "#10b981",
        "type": "color",
        "description": "Success state - forms, notifications"
      },
      "warning": {
        "value": "#f59e0b",
        "type": "color",
        "description": "Warning state - alerts, validation"
      },
      "error": {
        "value": "#ef4444",
        "type": "color",
        "description": "Error state - form errors, critical alerts"
      }
    }
  }
}
```

## Integration with Build Tools

### CSS Generation

Generate CSS custom properties for your build process:

```javascript
// build-tokens.js
const tokens = require('./showcase/colors.json');

function generateCSS(tokens, prefix = '') {
  let css = ':root {\n';

  function traverse(obj, path = '') {
    for (const [key, value] of Object.entries(obj)) {
      const currentPath = path ? `${path}-${key}` : key;

      if (value.value !== undefined) {
        css += `  --${prefix}${currentPath}: ${value.value};\n`;
      } else if (typeof value === 'object') {
        traverse(value, currentPath);
      }
    }
  }

  traverse(tokens);
  css += '}\n';
  return css;
}

console.log(generateCSS(tokens.color, 'color-'));
```

### Sass/SCSS Variables

Convert tokens to Sass variables:

```scss
// Generated from tokens
$color-primary-500: #3b82f6;
$color-secondary-500: #64748b;
$spacing-base: 1rem;
$font-family-sans: Inter, system-ui, sans-serif;
```

### Tailwind CSS Integration

Tailwind tokens are automatically available in your Tailwind build when you import them:

**Using @theme tokens:**
```css
/* Define tokens */
@theme {
  --color-brand: #3b82f6;
  --spacing-section: 4rem;
}

/* Use generated utilities */
.hero {
  @apply bg-brand p-section;
}
```

**Using config tokens:**
```javascript
// tailwind.config.js - tokens are auto-discovered
module.exports = {
  theme: {
    extend: {
      colors: {
        brand: '#3b82f6',        // Available as bg-brand, text-brand
        accent: '#8b5cf6'        // Available as bg-accent, text-accent
      },
      spacing: {
        'section': '4rem'        // Available as p-section, m-section
      }
    }
  }
}
```

**Style Dictionary to Tailwind:**
```javascript
// Convert Style Dictionary tokens to Tailwind format
const tokens = require('./showcase/colors.json');

function extractColors(tokens) {
  const colors = {};
  // Transform token structure to Tailwind format
  return colors;
}

module.exports = {
  theme: {
    extend: {
      colors: extractColors(tokens),
    }
  }
}
```

## Choosing Token Types

### When to Use Style Dictionary Tokens

**Best for:**
- Multi-platform design systems (web, mobile, desktop)
- Complex token relationships and aliases
- Integration with design tools (Figma, Sketch)
- Teams that need platform-specific outputs (iOS, Android, CSS)

**Benefits:**
- Industry standard format
- Extensive tooling ecosystem
- Platform-agnostic token definitions
- Advanced features like token references and transforms

### When to Use Tailwind @theme Tokens

**Best for:**
- Tailwind CSS 4.0+ projects
- CSS-first development workflows
- Simple, direct token definitions
- Teams primarily using CSS custom properties

**Benefits:**
- Native Tailwind CSS integration
- Direct CSS custom property output
- Simple syntax and mental model
- Automatic utility class generation

### When to Use Tailwind Config Tokens

**Best for:**
- Existing Tailwind CSS projects (pre-4.0)
- JavaScript-first development workflows
- Teams comfortable with JavaScript configuration
- Projects needing programmatic token generation

**Benefits:**
- Familiar Tailwind configuration format
- JavaScript programmability (functions, calculations)
- Backward compatibility with existing projects
- Direct integration with build tools

## Best Practices

### 1. **Naming Conventions**

Use consistent, semantic naming:

```json
{
  "color": {
    "brand": {
      "primary": { "value": "#3b82f6" },
      "secondary": { "value": "#64748b" }
    },
    "semantic": {
      "success": { "value": "#10b981" },
      "warning": { "value": "#f59e0b" },
      "error": { "value": "#ef4444" }
    }
  }
}
```

### 2. **Scale Consistency**

Use mathematical scales for spacing and typography:

```json
{
  "spacing": {
    "1": { "value": "0.25rem" },    // 4px
    "2": { "value": "0.5rem" },     // 8px
    "3": { "value": "0.75rem" },    // 12px
    "4": { "value": "1rem" },       // 16px
    "5": { "value": "1.25rem" },    // 20px
    "6": { "value": "1.5rem" }      // 24px
  }
}
```

### 3. **Documentation**

Always include descriptions for context:

```json
{
  "color": {
    "primary": {
      "500": {
        "value": "#3b82f6",
        "type": "color",
        "description": "Primary brand color - use for CTAs, links, and brand elements"
      }
    }
  }
}
```

### 4. **Token Hierarchy**

Organize from generic to specific:

```json
{
  "color": {
    "blue": {
      "500": { "value": "#3b82f6" }        // Generic
    },
    "primary": {
      "value": "{color.blue.500}"          // Semantic alias
    },
    "button": {
      "primary": {
        "background": {
          "value": "{color.primary}"       // Component-specific
        }
      }
    }
  }
}
```

## Troubleshooting

### Tokens Not Appearing

1. **Check file location**: Ensure JSON files are in `showcase/` directory
2. **Validate JSON**: Use a JSON validator to check file syntax
3. **Check token structure**: Ensure tokens have required `value` property
4. **Restart server**: Django may need restart to discover new files

### Invalid Token Values

1. **Color formats**: Use hex (`#3b82f6`), rgb (`rgb(59, 130, 246)`), or hsl (`hsl(217, 91%, 60%)`)
2. **Dimension units**: Include units like `px`, `rem`, `em`, `%`
3. **Font families**: Use quoted strings for multi-word font names

### CSS Variable Generation

1. **Path characters**: Special characters in paths are converted to hyphens
2. **Reserved names**: Avoid CSS reserved keywords in token names
3. **Custom variables**: Use `css_variable` property for specific naming

## Next Steps

- Learn about [Component Patterns](../building-components/component-patterns.md) that use design tokens
- Explore [CSS and Styling](../building-components/css-and-styling.md) integration
- Check out [Showcase Customization](customisation.md) for advanced configuration