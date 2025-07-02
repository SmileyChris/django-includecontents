# Tailwind CSS Integration

Django IncludeContents works excellently with Tailwind CSS, providing powerful utilities for building styled components. The conditional class system integrates seamlessly with Tailwind's utility-first approach.

## Setup

### Installation

Install Tailwind CSS in your Django project:

```bash
# Install via npm
npm install -D tailwindcss @tailwindcss/forms @tailwindcss/typography
npx tailwindcss init
```

### Configuration

Configure `tailwind.config.js` to work with Django IncludeContents:

```javascript
/** @type {import('tailwindcss').Config} */
module.exports = {
  content: {
    files: [
      './templates/**/*.html',
      './static/js/**/*.js',
      './*/templates/**/*.html',  // App templates
      '!./node_modules',
    ],
    transform: {
      // Handle Django IncludeContents class: syntax
      html: (content) => {
        return content.replace(/class:([\w-]+)/g, '$1');
      },
    },
  },
  theme: {
    extend: {
      // Custom colors for your components
      colors: {
        primary: {
          50: '#eff6ff',
          500: '#3b82f6',
          600: '#2563eb',
          700: '#1d4ed8',
        },
      },
    },
  },
  plugins: [
    require('@tailwindcss/forms'),
    require('@tailwindcss/typography'),
  ],
}
```

### CSS File

Create `static/css/tailwind.css`:

```css
@tailwind base;
@tailwind components;
@tailwind utilities;

/* Custom component styles */
@layer components {
  .btn {
    @apply inline-flex items-center justify-center rounded-md text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring disabled:pointer-events-none disabled:opacity-50;
  }
  
  .btn-primary {
    @apply bg-primary-600 text-white hover:bg-primary-700;
  }
  
  .btn-secondary {
    @apply bg-gray-100 text-gray-900 hover:bg-gray-200;
  }
  
  .btn-sm {
    @apply h-8 px-3 text-xs;
  }
  
  .btn-md {
    @apply h-10 px-4 py-2;
  }
  
  .btn-lg {
    @apply h-12 px-8 text-base;
  }
}
```

### Build Process

Add to `package.json`:

```json
{
  "scripts": {
    "build-css": "tailwindcss -i ./static/css/tailwind.css -o ./static/css/output.css --watch",
    "build-css-prod": "tailwindcss -i ./static/css/tailwind.css -o ./static/css/output.css --minify"
  }
}
```

## Component Examples

### Button Component

**templates/components/button.html**
```html
{# props variant=primary,secondary,danger, size=sm,md,lg, disabled=False #}
<button {% attrs
  class="btn"
  class:btn-primary=variantPrimary
  class:btn-secondary=variantSecondary
  class:btn-danger=variantDanger
  class:btn-sm=sizeSm
  class:btn-md=sizeMd
  class:btn-lg=sizeLg
  class:opacity-50=disabled
  class:cursor-not-allowed=disabled
  disabled=disabled
%}>
  {{ contents }}
</button>
```

**Usage:**
```html
<include:button variant="primary" size="lg">
  Large Primary Button
</include:button>

<include:button variant="danger" disabled="true">
  Disabled Danger Button
</include:button>
```

### Card Component

**templates/components/card.html**
```html
{# props title="", shadow=sm,md,lg,xl, rounded=md,lg,xl #}
<div {% attrs
  class="bg-white border border-gray-200"
  class:shadow-sm=shadowSm
  class:shadow-md=shadowMd
  class:shadow-lg=shadowLg
  class:shadow-xl=shadowXl
  class:rounded-md=roundedMd
  class:rounded-lg=roundedLg
  class:rounded-xl=roundedXl
%}>
  {% if title %}
    <div class="px-6 py-4 border-b border-gray-200">
      <h3 class="text-lg font-medium text-gray-900">{{ title }}</h3>
    </div>
  {% endif %}
  
  <div class="px-6 py-4">
    {{ contents }}
  </div>
  
  {% if contents.footer %}
    <div class="px-6 py-4 bg-gray-50 border-t border-gray-200">
      {{ contents.footer }}
    </div>
  {% endif %}
</div>
```

### Form Field Component

**templates/components/forms/field.html**
```html
{# props 
  name, 
  label="", 
  type=text,email,password,
  required=False,
  error="",
  help_text="",
  size=sm,md,lg
#}
<div class="space-y-1">
  {% if label %}
    <label for="{{ name }}" class="block text-sm font-medium text-gray-700">
      {{ label }}
      {% if required %}
        <span class="text-red-500">*</span>
      {% endif %}
    </label>
  {% endif %}
  
  <input {% attrs.input
    type=type
    name=name
    id=name
    required=required
    class="block w-full border-gray-300 rounded-md shadow-sm focus:ring-primary-500 focus:border-primary-500"
    class:text-sm=sizeSm
    class:text-base=sizeMd
    class:text-lg=sizeLg
    class:border-red-300=error
    class:focus:ring-red-500=error
    class:focus:border-red-500=error
  %}>
  
  {% if help_text %}
    <p class="text-sm text-gray-500">{{ help_text }}</p>
  {% endif %}
  
  {% if error %}
    <p class="text-sm text-red-600">{{ error }}</p>
  {% endif %}
</div>
```

## Advanced Patterns

### Responsive Components

**templates/components/grid.html**
```html
{# props cols_sm=1, cols_md=2, cols_lg=3, cols_xl=4, gap=4 #}
<div {% attrs
  class="grid gap-{{ gap }}"
  class:grid-cols-{{ cols_sm }}=True
  class:md:grid-cols-{{ cols_md }}=True
  class:lg:grid-cols-{{ cols_lg }}=True
  class:xl:grid-cols-{{ cols_xl }}=True
%}>
  {{ contents }}
</div>
```

### Dynamic Color Components

**templates/components/badge.html**
```html
{# props 
  variant=gray,red,yellow,green,blue,indigo,purple,pink,
  size=sm,md,lg
#}
<span {% attrs
  class="inline-flex items-center rounded-full font-medium"
  class:px-2=sizeSm
  class:py-1=sizeSm
  class:text-xs=sizeSm
  class:px-2.5=sizeMd
  class:py-0.5=sizeMd
  class:text-sm=sizeMd
  class:px-3=sizeLg
  class:py-1=sizeLg
  class:text-base=sizeLg
  class:bg-gray-100=variantGray
  class:text-gray-800=variantGray
  class:bg-red-100=variantRed
  class:text-red-800=variantRed
  class:bg-yellow-100=variantYellow
  class:text-yellow-800=variantYellow
  class:bg-green-100=variantGreen
  class:text-green-800=variantGreen
  class:bg-blue-100=variantBlue
  class:text-blue-800=variantBlue
  class:bg-indigo-100=variantIndigo
  class:text-indigo-800=variantIndigo
  class:bg-purple-100=variantPurple
  class:text-purple-800=variantPurple
  class:bg-pink-100=variantPink
  class:text-pink-800=variantPink
%}>
  {{ contents }}
</span>
```

### Interactive Components

**templates/components/dropdown.html**
```html
{# props trigger_text="Options", align=left,right #}
<div class="relative inline-block text-left" x-data="{ open: false }">
  <button
    @click="open = !open"
    class="inline-flex w-full justify-center gap-x-1.5 rounded-md bg-white px-3 py-2 text-sm font-semibold text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 hover:bg-gray-50"
  >
    {{ trigger_text }}
    <svg class="-mr-1 h-5 w-5 text-gray-400" viewBox="0 0 20 20" fill="currentColor">
      <path fill-rule="evenodd" d="M5.23 7.21a.75.75 0 011.06.02L10 11.168l3.71-3.938a.75.75 0 111.08 1.04l-4.25 4.5a.75.75 0 01-1.08 0l-4.25-4.5a.75.75 0 01.02-1.06z" clip-rule="evenodd" />
    </svg>
  </button>

  <div
    x-show="open"
    @click.outside="open = false"
    x-transition
    {% attrs
      class="absolute z-10 mt-2 w-56 origin-top-right divide-y divide-gray-100 rounded-md bg-white shadow-lg ring-1 ring-black ring-opacity-5 focus:outline-none"
      class:right-0=alignRight
      class:left-0=alignLeft
    %}
  >
    <div class="py-1">
      {{ contents }}
    </div>
  </div>
</div>
```

## Dark Mode Support

### Theme-Aware Components

**templates/components/themed-card.html**
```html
{# props #}
<div {% attrs
  class="border rounded-lg p-6 transition-colors"
  class="bg-white dark:bg-gray-800"
  class="border-gray-200 dark:border-gray-700"
  class="text-gray-900 dark:text-gray-100"
%}>
  {{ contents }}
</div>
```

### Theme Toggle Component

**templates/components/theme-toggle.html**
```html
{# props #}
<button
  @click="toggleTheme()"
  class="p-2 rounded-md bg-gray-100 dark:bg-gray-800 text-gray-800 dark:text-gray-200 hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors"
  aria-label="Toggle theme"
>
  <svg x-show="theme === 'light'" class="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
    <path fill-rule="evenodd" d="M10 2a1 1 0 011 1v1a1 1 0 11-2 0V3a1 1 0 011-1zm4 8a4 4 0 11-8 0 4 4 0 018 0zm-.464 4.95l.707.707a1 1 0 001.414-1.414l-.707-.707a1 1 0 00-1.414 1.414zm2.12-10.607a1 1 0 010 1.414l-.706.707a1 1 0 11-1.414-1.414l.707-.707a1 1 0 011.414 0zM17 11a1 1 0 100-2h-1a1 1 0 100 2h1zm-7 4a1 1 0 011 1v1a1 1 0 11-2 0v-1a1 1 0 011-1zM5.05 6.464A1 1 0 106.465 5.05l-.708-.707a1 1 0 00-1.414 1.414l.707.707zm1.414 8.486l-.707.707a1 1 0 01-1.414-1.414l.707-.707a1 1 0 011.414 1.414zM4 11a1 1 0 100-2H3a1 1 0 000 2h1z" clip-rule="evenodd"></path>
  </svg>
  <svg x-show="theme === 'dark'" class="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
    <path d="M17.293 13.293A8 8 0 016.707 2.707a8.001 8.001 0 1010.586 10.586z"></path>
  </svg>
</button>
```

## Build Integration

### Django Integration

**settings.py**
```python
# Static files
STATICFILES_DIRS = [
    BASE_DIR / "static",
]

# For development
if DEBUG:
    STATICFILES_DIRS += [
        BASE_DIR / "node_modules",
    ]
```

**base.html**
```html
{% load static %}
<!DOCTYPE html>
<html lang="en" class="h-full bg-gray-50">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}My Site{% endblock %}</title>
    <link href="{% static 'css/output.css' %}" rel="stylesheet">
    <script defer src="https://unpkg.com/alpinejs@3.x.x/dist/cdn.min.js"></script>
</head>
<body class="h-full" x-data="{ theme: 'light' }">
    <div class="min-h-full">
        {{ contents }}
    </div>
</body>
</html>
```

### Production Build

**Docker configuration:**
```dockerfile
# Install Node.js for Tailwind CSS
FROM node:18-alpine AS css-builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build-css-prod

# Django build
FROM python:3.11-alpine
# ... Django setup
COPY --from=css-builder /app/static/css/output.css /app/static/css/
```

## VS Code Integration

### Tailwind IntelliSense

Add to `.vscode/settings.json`:

```json
{
  "tailwindCSS.includeLanguages": {
    "django-html": "html"
  },
  "tailwindCSS.experimental.classRegex": [
    ["class\\s*[=:]\\s*['\"]([^'\"]*)['\"]", "['\"]([^'\"]*)['\"]"],
    ["class:[\\w-]+\\s*=\\s*['\"]([^'\"]*)['\"]", "['\"]([^'\"]*)['\"]"],
    ["class:[\\w-]+=[\\w-]+", "class:[\\w-]+=([\\w-]+)"]
  ]
}
```

### Custom CSS Classes

**IntelliSense for component classes:**
```json
{
  "tailwindCSS.classAttributes": [
    "class",
    "className",
    "class:.*"
  ]
}
```

## Performance Optimization

### Purge Configuration

Ensure unused classes are removed:

```javascript
module.exports = {
  content: {
    files: [
      './templates/**/*.html',
      './static/js/**/*.js',
    ],
    safelist: [
      // Classes generated dynamically
      {
        pattern: /btn-(primary|secondary|danger)/,
      },
      {
        pattern: /(text|bg)-(red|green|blue)-(100|800)/,
      },
    ],
  },
  // ... rest of config
}
```

### Component Library

Create a comprehensive Tailwind component library:

**templates/components/ui/alert.html**
```html
{# props 
  variant=info,success,warning,error,
  dismissible=False,
  title=""
#}
<div {% attrs
  class="rounded-md p-4"
  class:bg-blue-50=variantInfo
  class:border-blue-200=variantInfo
  class:bg-green-50=variantSuccess
  class:border-green-200=variantSuccess
  class:bg-yellow-50=variantWarning
  class:border-yellow-200=variantWarning
  class:bg-red-50=variantError
  class:border-red-200=variantError
%}>
  <div class="flex">
    <div class="flex-shrink-0">
      {% if variantInfo %}
        <svg class="h-5 w-5 text-blue-400" viewBox="0 0 20 20" fill="currentColor">
          <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clip-rule="evenodd" />
        </svg>
      {% elif variantSuccess %}
        <svg class="h-5 w-5 text-green-400" viewBox="0 0 20 20" fill="currentColor">
          <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd" />
        </svg>
      {% elif variantWarning %}
        <svg class="h-5 w-5 text-yellow-400" viewBox="0 0 20 20" fill="currentColor">
          <path fill-rule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clip-rule="evenodd" />
        </svg>
      {% elif variantError %}
        <svg class="h-5 w-5 text-red-400" viewBox="0 0 20 20" fill="currentColor">
          <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd" />
        </svg>
      {% endif %}
    </div>
    <div class="ml-3">
      {% if title %}
        <h3 {% attrs
          class="text-sm font-medium"
          class:text-blue-800=variantInfo
          class:text-green-800=variantSuccess
          class:text-yellow-800=variantWarning
          class:text-red-800=variantError
        %}>
          {{ title }}
        </h3>
      {% endif %}
      <div {% attrs
        class="text-sm"
        class:text-blue-700=variantInfo
        class:text-green-700=variantSuccess
        class:text-yellow-700=variantWarning
        class:text-red-700=variantError
        class:mt-2=title
      %}>
        {{ contents }}
      </div>
    </div>
    {% if dismissible %}
      <div class="ml-auto pl-3">
        <div class="-mx-1.5 -my-1.5">
          <button class="inline-flex rounded-md p-1.5 focus:outline-none focus:ring-2 focus:ring-offset-2">
            <span class="sr-only">Dismiss</span>
            <svg class="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
              <path fill-rule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clip-rule="evenodd" />
            </svg>
          </button>
        </div>
      </div>
    {% endif %}
  </div>
</div>
```

## Best Practices

### 1. Component-First Design

Design components with Tailwind utilities:

```html
<!-- ✅ Good: Utility-first component -->
<include:card class="max-w-md mx-auto">
  <include:button variant="primary" class="w-full">
    Full Width Button
  </include:button>
</include:card>
```

### 2. Consistent Spacing

Use Tailwind's spacing scale consistently:

```html
{# props #}
<div class="space-y-4">  <!-- Consistent 1rem spacing -->
  <div class="p-4">{{ contents.header }}</div>
  <div class="p-4">{{ contents }}</div>
  <div class="p-4">{{ contents.footer }}</div>
</div>
```

### 3. Responsive Design

Build mobile-first responsive components:

```html
{# props #}
<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
  {{ contents }}
</div>
```

### 4. Accessibility

Include accessibility classes:

```html
{# props label, required=False #}
<label class="block text-sm font-medium text-gray-700">
  {{ label }}
  {% if required %}
    <span class="text-red-500 ml-1" aria-label="required">*</span>
  {% endif %}
</label>
```

## Next Steps

- Explore [Component Patterns](../advanced/component-patterns.md) for advanced Tailwind usage
- Set up [VS Code Integration](vscode.md) for Tailwind IntelliSense
- Check [Prettier Integration](prettier.md) for consistent formatting