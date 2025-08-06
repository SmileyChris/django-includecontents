# Advanced Icon Styling

This guide covers advanced techniques for styling icons, particularly using CSS variables to create dynamic, themeable icons that work across the shadow DOM boundary.

## CSS Variables in Icon Sprites

When SVG icons are combined into sprites and used via `<use>` elements, normal CSS styling faces limitations due to the shadow DOM boundary. However, CSS variables can cross this boundary, enabling powerful styling capabilities.

The icon system preserves `style` attributes that contain CSS variables (e.g., `var(--name)`), while removing regular inline styles to prevent conflicts.

## Basic Theme Switching

Create icons that automatically adapt to light/dark modes:

```html
<!-- Original icon SVG with CSS variables -->
<svg>
  <path style="fill: var(--icon-primary)" d="..." />
  <circle style="stroke: var(--icon-accent)" cx="..." />
</svg>
```

```css
/* Define theme colors */
:root {
  --icon-primary: #1f2937;
  --icon-accent: #3b82f6;
}

.dark {
  --icon-primary: #f3f4f6;
  --icon-accent: #60a5fa;
}
```

```html
<!-- Icon automatically uses current theme -->
<icon:myicon />
```

## Interactive Hover Effects

Transform specific parts of icons on hover by combining CSS variables with transforms:

```html
<!-- Icon SVG with transform and transition -->
<svg>
  <g style="transform: var(--icon-transform, none); 
            transform-origin: center;
            transition: var(--icon-transition, none);">
    <path style="fill: var(--icon-color, currentColor)" d="..." />
  </g>
</svg>
```

```css
/* Hover animation */
.interactive-icon {
  --icon-color: #6b7280;
  --icon-transform: scale(1);
  --icon-transition: all 0.2s ease;
}

.interactive-icon:hover {
  --icon-color: #3b82f6;
  --icon-transform: scale(1.1) rotate(5deg);
}
```

## Multi-Part Icon Animation

Animate different parts of an icon independently:

```html
<!-- Icon with multiple animated parts -->
<svg>
  <circle style="fill: var(--icon-bg, #fff);
                 transform: var(--icon-bg-scale, scale(1));
                 transform-origin: center;
                 transition: var(--icon-bg-transition, none);" r="20" />
  <path style="fill: var(--icon-fg, #000);
               transform: var(--icon-fg-rotate, rotate(0));
               transform-origin: center;
               transition: var(--icon-fg-transition, none);" d="..." />
</svg>
```

```css
.animated-icon {
  --icon-bg: #f3f4f6;
  --icon-fg: #6b7280;
  --icon-bg-scale: scale(1);
  --icon-fg-rotate: rotate(0);
  --icon-bg-transition: transform 0.3s ease;
  --icon-fg-transition: transform 0.3s ease, fill 0.2s ease;
}

.animated-icon:hover {
  --icon-bg: #dbeafe;
  --icon-fg: #2563eb;
  --icon-bg-scale: scale(1.2);
  --icon-fg-rotate: rotate(180deg);
}
```

## State-Based Styling

Change icon appearance based on application state:

```html
<!-- Icon with state-based colors -->
<svg>
  <path style="fill: var(--status-color)" d="..." />
</svg>
```

```css
.status-icon {
  --status-color: #6b7280; /* default/idle */
}

.status-icon.success {
  --status-color: #10b981;
}

.status-icon.warning {
  --status-color: #f59e0b;
}

.status-icon.error {
  --status-color: #ef4444;
}
```

```html
<!-- Usage in templates -->
<icon:status class="status-icon {{ status_class }}" />
```

## Brand Customization

Define brand colors once and apply across all icons:

```css
:root {
  /* Brand palette */
  --brand-primary: #7c3aed;
  --brand-secondary: #06b6d4;
  --brand-accent: #f59e0b;
  
  /* Map to icon variables */
  --icon-primary: var(--brand-primary);
  --icon-secondary: var(--brand-secondary);
}

/* Client-specific overrides */
.client-acme {
  --brand-primary: #dc2626;
  --brand-secondary: #0891b2;
}
```

## Best Practices

### 1. Namespace Your Variables

Use consistent prefixes to avoid conflicts:

```css
/* Good */
--icon-primary-color: #3b82f6;
--icon-hover-transform: scale(1.1);

/* Avoid */
--color: #3b82f6;
--transform: scale(1.1);
```

### 2. Provide Fallback Values

Always include fallbacks in your SVG styles:

```html
<!-- Good -->
<path style="fill: var(--icon-color, currentColor)" />

<!-- Avoid -->
<path style="fill: var(--icon-color)" />
```

### 3. Keep Transitions in SVG

For best compatibility, define transitions within the SVG itself:

```html
<!-- Transitions in the SVG -->
<g style="transition: var(--icon-transition, transform 0.2s ease);">
```

### 4. Document Your Variables

Create a reference for your icon variables:

```css
/* Icon System Variables
 * --icon-primary: Main icon color
 * --icon-accent: Accent/highlight color
 * --icon-muted: Disabled state color
 * --icon-transform: Transform for hover/active states
 * --icon-transition: Animation timing
 */
```

## Limitations

- Only `style` attributes with CSS variables are preserved
- Regular inline styles are removed during sprite generation
- Not all SVG attributes can be controlled via CSS variables
- Browser support varies for complex SVG/CSS interactions

## Examples

### Loading Spinner with Variable Speed

```html
<svg>
  <circle style="animation: spin var(--spinner-speed, 1s) linear infinite;
                 stroke: var(--spinner-color, currentColor);" 
          r="10" fill="none" stroke-width="2" />
</svg>

<style>
  @keyframes spin {
    to { transform: rotate(360deg); }
  }
  
  .spinner-fast { --spinner-speed: 0.5s; }
  .spinner-slow { --spinner-speed: 2s; }
</style>
```

### Progress Indicator

```html
<svg>
  <rect style="width: var(--progress, 0%); 
               fill: var(--progress-color, #3b82f6);
               transition: width 0.3s ease;" 
        height="4" />
</svg>

<style>
  .progress-25 { --progress: 25%; }
  .progress-50 { --progress: 50%; }
  .progress-75 { --progress: 75%; }
  .progress-complete { 
    --progress: 100%; 
    --progress-color: #10b981;
  }
</style>
```