# Prettier Integration

Django IncludeContents works excellently with Prettier for consistent template formatting. The HTML component syntax integrates seamlessly with Prettier's formatting capabilities.

## Installation

Install the Prettier plugin for Django/Jinja templates:

```bash
npm install --save-dev prettier prettier-plugin-jinja-template
```

## Configuration

### Basic Configuration

Create a `.prettierrc` file in your project root:

```json
{
  "plugins": ["prettier-plugin-jinja-template"],
  "overrides": [
    {
      "files": ["**/{templates,jinja2}/**/*.html"],
      "options": {
        "parser": "jinja-template",
        "printWidth": 100,
        "tabWidth": 2,
        "useTabs": false
      }
    }
  ]
}
```

### Advanced Configuration

For more control over formatting:

```json
{
  "plugins": ["prettier-plugin-jinja-template"],
  "overrides": [
    {
      "files": ["**/{templates,jinja2}/**/*.html"],
      "options": {
        "parser": "jinja-template",
        "printWidth": 100,
        "tabWidth": 2,
        "useTabs": false,
        "singleQuote": false,
        "htmlWhitespaceSensitivity": "css",
        "endOfLine": "lf"
      }
    },
    {
      "files": ["**/components/**/*.html"],
      "options": {
        "parser": "jinja-template",
        "printWidth": 80,
        "tabWidth": 2
      }
    }
  ]
}
```

## Component Formatting

### Before and After Examples

**Before formatting:**
```html
<include:card title="Long Title Here" subtitle="An equally long subtitle" class="my-card"><p>Content here</p><content:footer><button>Action</button></content:footer></include:card>
```

**After Prettier formatting:**
```html
<include:card
  title="Long Title Here"
  subtitle="An equally long subtitle"
  class="my-card"
>
  <p>Content here</p>
  <content:footer>
    <button>Action</button>
  </content:footer>
</include:card>
```

### Multi-line Template Tags

**Before:**
```django
{% includecontents "components/complex.html" title="Title" author=article.author date=article.created_at featured=article.is_featured %}Content{% endincludecontents %}
```

**After:**
```django
{% includecontents "components/complex.html"
  title="Title"
  author=article.author
  date=article.created_at
  featured=article.is_featured
%}
  Content
{% endincludecontents %}
```

## Formatting Features

### Attribute Formatting

Prettier automatically formats component attributes:

```html
<!-- Input -->
<include:button variant="primary" size="large" disabled class="my-button" data-action="submit">Submit</include:button>

<!-- Formatted -->
<include:button
  variant="primary"
  size="large"
  disabled
  class="my-button"
  data-action="submit"
>
  Submit
</include:button>
```

### Content Block Formatting

```html
<!-- Input -->
<include:article><content:header><h1>Title</h1><p>Subtitle</p></content:header><p>Main content</p></include:article>

<!-- Formatted -->
<include:article>
  <content:header>
    <h1>Title</h1>
    <p>Subtitle</p>
  </content:header>
  <p>Main content</p>
</include:article>
```

### Template Expression Formatting

```html
<!-- Input -->
<include:user-card user="{{ user }}" avatar-url="{% if user.avatar %}{{ user.avatar.url }}{% endif %}" active="{{ user.is_active|yesno:'true,false' }}">

<!-- Formatted -->
<include:user-card
  user="{{ user }}"
  avatar-url="{% if user.avatar %}{{ user.avatar.url }}{% endif %}"
  active="{{ user.is_active|yesno:'true,false' }}"
>
```

## Editor Integration

### VS Code

Install the Prettier VS Code extension:

```bash
code --install-extension esbenp.prettier-vscode
```

Add to your VS Code settings (`settings.json`):

```json
{
  "[django-html]": {
    "editor.defaultFormatter": "esbenp.prettier-vscode",
    "editor.formatOnSave": true
  },
  "[jinja-html]": {
    "editor.defaultFormatter": "esbenp.prettier-vscode",
    "editor.formatOnSave": true
  },
  "prettier.documentSelectors": [
    "**/*.html"
  ]
}
```

### Sublime Text

Install Package Control, then install:
- SublimeJsPrettier
- Django

Configure in Preferences > Package Settings > JsPrettier > Settings:

```json
{
  "prettier_cli_path": "/usr/local/bin/prettier",
  "node_path": "/usr/local/bin/node",
  "auto_format_on_save": true,
  "custom_file_extensions": ["html"]
}
```

### Vim/Neovim

Using vim-prettier plugin:

```vim
" Install vim-prettier
Plug 'prettier/vim-prettier', { 'do': 'yarn install' }

" Configure for Django templates
let g:prettier#autoformat = 1
let g:prettier#autoformat_require_pragma = 0
autocmd BufWritePre *.html PrettierAsync
```

## Script Integration

### Package.json Scripts

Add formatting scripts to your `package.json`:

```json
{
  "scripts": {
    "format": "prettier --write \"**/{templates,jinja2}/**/*.html\"",
    "format:check": "prettier --check \"**/{templates,jinja2}/**/*.html\"",
    "format:components": "prettier --write \"**/components/**/*.html\""
  },
  "devDependencies": {
    "prettier": "^3.0.0",
    "prettier-plugin-jinja-template": "^1.0.0"
  }
}
```

### Pre-commit Hooks

Using pre-commit framework, add to `.pre-commit-config.yaml`:

```yaml
repos:
  - repo: https://github.com/pre-commit/mirrors-prettier
    rev: v3.0.0
    hooks:
      - id: prettier
        files: \.(html)$
        additional_dependencies:
          - prettier@3.0.0
          - prettier-plugin-jinja-template@1.0.0
```

### GitHub Actions

Add to your CI workflow:

```yaml
name: Format Check
on: [push, pull_request]

jobs:
  format-check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '18'
      - run: npm install
      - run: npm run format:check
```

## Configuration Tips

### Handling Django Template Tags

Configure to preserve Django template tag formatting:

```json
{
  "overrides": [
    {
      "files": ["**/*.html"],
      "options": {
        "parser": "jinja-template",
        "htmlWhitespaceSensitivity": "strict"
      }
    }
  ]
}
```

### Component-Specific Settings

Different formatting for different component types:

```json
{
  "overrides": [
    {
      "files": ["**/components/ui/**/*.html"],
      "options": {
        "printWidth": 80,
        "tabWidth": 2
      }
    },
    {
      "files": ["**/components/layout/**/*.html"],
      "options": {
        "printWidth": 120,
        "tabWidth": 4
      }
    }
  ]
}
```

### Ignore Patterns

Use `.prettierignore` to exclude certain files:

```
# .prettierignore
node_modules/
venv/
static/
dist/
*.min.html
third_party/
```

## Common Issues and Solutions

### Issue: Prettier Breaking Django Template Tags

**Problem:**
```django
<!-- Before -->
{% if user.is_authenticated and user.is_staff %}

<!-- Prettier breaks it to -->
{% if user.is_authenticated and user.is_staff %}
```

**Solution:** Use the jinja-template parser in your config:

```json
{
  "parser": "jinja-template"
}
```

### Issue: Long Attribute Values

**Problem:** Long template expressions in attributes get awkwardly formatted.

**Solution:** Use shorter variable names or break into multiple steps:

```django
<!-- Before -->
<include:card title="{% if article.is_featured %}Featured: {{ article.title }}{% else %}{{ article.title }}{% endif %}">

<!-- Better -->
{% with display_title=article.get_display_title %}
  <include:card title="{{ display_title }}">
{% endwith %}
```

### Issue: AlpineJS Attributes

**Problem:** Prettier removes quotes from AlpineJS attributes:

```html
<!-- Input -->
<div x-data="{ open: false }">

<!-- Prettier removes quotes -->
<div x-data={ open: false }>
```

**Solution:** Use template variables:

```html
<!-- Workaround -->
<div x-data="{{ '{ open: false }' }}">
```

Or configure Prettier to preserve certain attributes:

```json
{
  "htmlWhitespaceSensitivity": "strict"
}
```

## Advanced Configuration

### Custom Prettier Plugin

Create a custom configuration for your project:

```javascript
// prettier.config.js
module.exports = {
  plugins: ['prettier-plugin-jinja-template'],
  overrides: [
    {
      files: ['**/*.html'],
      options: {
        parser: 'jinja-template',
        printWidth: 100,
        tabWidth: 2,
        useTabs: false,
        singleQuote: false,
        // Custom formatting for components
        htmlWhitespaceSensitivity: 'css',
        endOfLine: 'lf',
      },
    },
  ],
  // Custom rules for different directories
  ...(process.env.NODE_ENV === 'development' && {
    overrides: [
      ...module.exports.overrides,
      {
        files: ['**/components/**/*.html'],
        options: {
          printWidth: 80,
          tabWidth: 2,
        },
      },
    ],
  }),
};
```

### Team Configuration

Share configuration across your team:

```json
{
  "name": "myproject",
  "prettier": {
    "plugins": ["prettier-plugin-jinja-template"],
    "overrides": [
      {
        "files": ["**/*.html"],
        "options": {
          "parser": "jinja-template",
          "printWidth": 100,
          "tabWidth": 2
        }
      }
    ]
  }
}
```

## Best Practices

### 1. Consistent Configuration

Use the same Prettier configuration across all developers:

```bash
# Install exact versions
npm install --save-dev --save-exact prettier@3.0.0 prettier-plugin-jinja-template@1.0.0
```

### 2. Format on Save

Enable format-on-save in your editor for consistent formatting.

### 3. Pre-commit Formatting

Always format before committing:

```bash
# Add to git hooks
npm run format && git add .
```

### 4. Component Guidelines

Follow consistent patterns in components:

```html
<!-- ✅ Good: Consistent attribute ordering -->
<include:button
  variant="primary"
  size="large"
  disabled="{{ is_disabled }}"
  class="my-button"
  data-action="submit"
>
  Submit
</include:button>

<!-- ❌ Avoid: Inconsistent formatting -->
<include:button variant="primary" size="large"
disabled="{{ is_disabled }}"
class="my-button" data-action="submit">Submit</include:button>
```

### 5. Documentation

Document your Prettier configuration:

```markdown
## Code Formatting

This project uses Prettier for consistent code formatting.

### Setup
1. Install dependencies: `npm install`
2. Format all templates: `npm run format`
3. Check formatting: `npm run format:check`

### Editor Setup
- VS Code: Install Prettier extension and enable format-on-save
- Other editors: See docs/prettier-setup.md
```

## Troubleshooting

### Debug Prettier Issues

```bash
# Check what files Prettier will format
npx prettier --find-config-path templates/

# Test formatting a specific file
npx prettier --write templates/components/button.html

# Debug parser issues
npx prettier --parser jinja-template --write templates/test.html
```

### Performance Tips

For large codebases:

```bash
# Format only changed files
npx prettier --write $(git diff --name-only --diff-filter=ACMRTUXB | grep '\.html$')

# Use ignore patterns
echo "node_modules/" >> .prettierignore
echo "static/" >> .prettierignore
```

## Next Steps

- Set up [VS Code Integration](vscode.md) for the complete development experience
- Configure [Tailwind CSS](tailwind.md) for utility-first styling
- Check the [Component Patterns](../advanced/component-patterns.md) guide for formatting examples