# VS Code Integration

Visual Studio Code provides excellent support for Django IncludeContents through extensions and configuration. This guide covers setting up the optimal development environment.

## Required Extensions

Install these essential extensions for the best Django IncludeContents experience:

### Core Extensions

```bash
# Install via command line
code --install-extension ms-python.python
code --install-extension batisteo.vscode-django
code --install-extension esbenp.prettier-vscode
code --install-extension bradlc.vscode-tailwindcss
```

Or install manually from the VS Code marketplace:

1. **[Python](https://marketplace.visualstudio.com/items?itemName=ms-python.python)** - Python language support
2. **[Django](https://marketplace.visualstudio.com/items?itemName=batisteo.vscode-django)** - Django template syntax highlighting
3. **[Prettier](https://marketplace.visualstudio.com/items?itemName=esbenp.prettier-vscode)** - Code formatting
4. **[Tailwind CSS IntelliSense](https://marketplace.visualstudio.com/items?itemName=bradlc.vscode-tailwindcss)** - Tailwind CSS support

### Optional But Helpful

```bash
# Additional extensions
code --install-extension ms-python.black-formatter
code --install-extension charliermarsh.ruff
code --install-extension streetsidesoftware.code-spell-checker
code --install-extension formulahendry.auto-rename-tag
code --install-extension christian-kohler.path-intellisense
```

## VS Code Configuration

### Workspace Settings

Create `.vscode/settings.json` in your project root:

```json
{
  "python.defaultInterpreterPath": "./venv/bin/python",
  "python.terminal.activateEnvironment": true,
  
  // Django template settings
  "[django-html]": {
    "editor.defaultFormatter": "esbenp.prettier-vscode",
    "editor.formatOnSave": true,
    "editor.quickSuggestions": {
      "other": true,
      "comments": false,
      "strings": true
    }
  },
  
  // HTML settings for components
  "[html]": {
    "editor.defaultFormatter": "esbenp.prettier-vscode",
    "editor.formatOnSave": true
  },
  
  // File associations
  "files.associations": {
    "**/templates/**/*.html": "django-html",
    "**/components/**/*.html": "django-html"
  },
  
  // Emmet support
  "emmet.includeLanguages": {
    "django-html": "html"
  },
  
  // Prettier configuration
  "prettier.requireConfig": true,
  "prettier.documentSelectors": ["**/*.html"],
  
  // Tailwind CSS
  "tailwindCSS.includeLanguages": {
    "django-html": "html"
  },
  "tailwindCSS.experimental.classRegex": [
    ["class\\s*[=:]\\s*['\"]([^'\"]*)['\"]", "['\"]([^'\"]*)['\"]"],
    ["class:[\\w-]+\\s*=\\s*['\"]([^'\"]*)['\"]", "['\"]([^'\"]*)['\"]"]
  ],
  
  // Editor behavior
  "editor.tabSize": 2,
  "editor.insertSpaces": true,
  "editor.rulers": [80, 100],
  "editor.wordWrap": "bounded",
  "editor.wordWrapColumn": 100
}
```

### User Settings

Add to your global VS Code settings:

```json
{
  // File explorer
  "explorer.fileNesting.enabled": true,
  "explorer.fileNesting.patterns": {
    "*.html": "${capture}.css, ${capture}.js"
  },
  
  // Search
  "search.exclude": {
    "**/node_modules": true,
    "**/venv": true,
    "**/.git": true,
    "**/static": true,
    "**/media": true
  }
}
```

## Code Snippets

### Django IncludeContents Snippets

Create `.vscode/django-includecontents.code-snippets`:

```json
{
  "Include Component": {
    "scope": "django-html,html",
    "prefix": ["inc", "include"],
    "body": [
      "<include:${1:component-name}${2: ${3:prop}=\"${4:value}\"}>",
      "\t$0",
      "</include:${1:component-name}>"
    ],
    "description": "Include component with props"
  },
  
  "Self-closing Component": {
    "scope": "django-html,html",
    "prefix": ["incs", "include-self"],
    "body": [
      "<include:${1:component-name}${2: ${3:prop}=\"${4:value}\"} />"
    ],
    "description": "Self-closing component"
  },
  
  "Content Block": {
    "scope": "django-html,html",
    "prefix": ["content", "cb"],
    "body": [
      "<content:${1:block-name}>",
      "\t$0",
      "</content:${1:block-name}>"
    ],
    "description": "Named content block"
  },
  
  "Component Props Definition": {
    "scope": "django-html,html",
    "prefix": ["props"],
    "body": [
      "{# props ${1:prop1}, ${2:prop2}=${3:default} #}"
    ],
    "description": "Component props definition"
  },
  
  "Attrs Tag": {
    "scope": "django-html,html",
    "prefix": ["attrs"],
    "body": [
      "{% attrs ${1:class}=\"${2:default-class}\" %}"
    ],
    "description": "Attrs template tag"
  },
  
  "Conditional Class": {
    "scope": "django-html,html",
    "prefix": ["class-if"],
    "body": [
      "class:${1:class-name}=${2:condition}"
    ],
    "description": "Conditional class attribute"
  },
  
  "IncludeContents Tag": {
    "scope": "django-html,html",
    "prefix": ["ict", "includecontents"],
    "body": [
      "{% includecontents \"${1:template-path}\"${2: ${3:prop}=${4:value}} %}",
      "\t$0",
      "{% endincludecontents %}"
    ],
    "description": "Traditional includecontents tag"
  },
  
  "Wrapif Tag": {
    "scope": "django-html,html", 
    "prefix": ["wrapif"],
    "body": [
      "{% wrapif ${1:condition} then \"${2:tag}\"${3: ${4:attr}=\"${5:value}\"} %}",
      "\t$0",
      "{% endwrapif %}"
    ],
    "description": "Wrapif conditional wrapper"
  }
}
```

### HTML Snippets

Create `.vscode/html-components.code-snippets`:

```json
{
  "Button Component": {
    "scope": "django-html,html",
    "prefix": ["btn", "button"],
    "body": [
      "<include:button variant=\"${1|primary,secondary,danger}\" ${2:size=\"${3|small,medium,large}\"}>",
      "\t${4:Button Text}",
      "</include:button>"
    ],
    "description": "Button component"
  },
  
  "Card Component": {
    "scope": "django-html,html",
    "prefix": ["card"],
    "body": [
      "<include:card title=\"${1:Card Title}\">",
      "\t${2:Card content}",
      "\t<content:footer>",
      "\t\t${3:Footer content}",
      "\t</content:footer>",
      "</include:card>"
    ],
    "description": "Card component with footer"
  },
  
  "Form Field": {
    "scope": "django-html,html",
    "prefix": ["field", "form-field"],
    "body": [
      "<include:forms:field",
      "\tname=\"${1:field-name}\"",
      "\tlabel=\"${2:Field Label}\"",
      "\ttype=\"${3|text,email,password,number}\"",
      "\t${4:required=\"true\"}",
      "/>"
    ],
    "description": "Form field component"
  }
}
```

## IntelliSense Configuration

### Custom IntelliSense

Create `.vscode/html.json` for component autocomplete:

```json
{
  "html": {
    "customData": [
      {
        "version": "1.0",
        "tags": [
          {
            "name": "include:button",
            "description": "Button component",
            "attributes": [
              {
                "name": "variant",
                "description": "Button variant",
                "values": [
                  { "name": "primary" },
                  { "name": "secondary" },
                  { "name": "danger" }
                ]
              },
              {
                "name": "size", 
                "description": "Button size",
                "values": [
                  { "name": "small" },
                  { "name": "medium" },
                  { "name": "large" }
                ]
              },
              {
                "name": "disabled",
                "description": "Disabled state",
                "valueSet": "v"
              }
            ]
          },
          {
            "name": "include:card",
            "description": "Card component",
            "attributes": [
              {
                "name": "title",
                "description": "Card title"
              },
              {
                "name": "subtitle",
                "description": "Card subtitle"
              }
            ]
          }
        ]
      }
    ]
  }
}
```

### Django Template IntelliSense

For better Django template support, add to settings:

```json
{
  "django.snippets.exclude": [],
  "django.snippets.use": true,
  "emmet.variables": {
    "lang": "en",
    "charset": "UTF-8"
  }
}
```

## Tasks and Debugging

### Tasks Configuration

Create `.vscode/tasks.json`:

```json
{
  "version": "2.0.0",
  "tasks": [
    {
      "label": "Django: Run Server",
      "type": "shell",
      "command": "${workspaceFolder}/venv/bin/python",
      "args": ["manage.py", "runserver"],
      "group": "build",
      "presentation": {
        "echo": true,
        "reveal": "always",
        "focus": false,
        "panel": "new"
      },
      "problemMatcher": []
    },
    {
      "label": "Format Templates",
      "type": "shell",
      "command": "npm",
      "args": ["run", "format"],
      "group": "build",
      "presentation": {
        "echo": true,
        "reveal": "silent"
      }
    },
    {
      "label": "Build Docs",
      "type": "shell",
      "command": "mkdocs",
      "args": ["build"],
      "group": "build"
    },
    {
      "label": "Serve Docs",
      "type": "shell", 
      "command": "mkdocs",
      "args": ["serve"],
      "group": "build",
      "presentation": {
        "reveal": "always",
        "panel": "new"
      }
    }
  ]
}
```

### Launch Configuration

Create `.vscode/launch.json`:

```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Django: Debug Server",
      "type": "python",
      "request": "launch",
      "program": "${workspaceFolder}/manage.py",
      "args": ["runserver", "--noreload"],
      "django": true,
      "justMyCode": false,
      "env": {
        "DJANGO_DEBUG": "True"
      }
    },
    {
      "name": "Django: Test",
      "type": "python",
      "request": "launch",
      "program": "${workspaceFolder}/manage.py",
      "args": ["test"],
      "django": true,
      "justMyCode": false
    }
  ]
}
```

## Key Bindings

### Custom Keybindings

Add to your `keybindings.json`:

```json
[
  {
    "key": "ctrl+shift+f",
    "command": "editor.action.formatDocument",
    "when": "editorHasDocumentFormattingProvider && !editorReadonly && resourceExtname == .html"
  },
  {
    "key": "ctrl+k ctrl+c",
    "command": "editor.action.insertSnippet",
    "when": "editorTextFocus && resourceExtname == .html",
    "args": {
      "snippet": "<include:${1:component}>$0</include:${1:component}>"
    }
  }
]
```

## Workspace Recommendations

### Extensions Recommendations

Create `.vscode/extensions.json`:

```json
{
  "recommendations": [
    "ms-python.python",
    "batisteo.vscode-django", 
    "esbenp.prettier-vscode",
    "bradlc.vscode-tailwindcss",
    "ms-python.black-formatter",
    "charliermarsh.ruff"
  ],
  "unwantedRecommendations": [
    "ms-python.pylint"
  ]
}
```

### Workspace File

Create a `.code-workspace` file:

```json
{
  "folders": [
    {
      "path": "."
    }
  ],
  "settings": {
    "python.defaultInterpreterPath": "./venv/bin/python",
    "files.associations": {
      "**/templates/**/*.html": "django-html"
    }
  },
  "extensions": {
    "recommendations": [
      "ms-python.python",
      "batisteo.vscode-django",
      "esbenp.prettier-vscode"
    ]
  }
}
```

## Productivity Tips

### 1. Template Navigation

Quick navigation between templates:

- **Ctrl+P**: Quick file open
- **Ctrl+Shift+F**: Search across templates
- **F12**: Go to definition (for included templates)

### 2. Component Development

Efficient component development workflow:

1. Create component file in `templates/components/`
2. Use snippets for quick component structure
3. Format on save with Prettier
4. Test component in browser with hot reload

### 3. Multi-Cursor Editing

Use multi-cursor for repetitive edits:

- **Ctrl+D**: Select next occurrence
- **Ctrl+Shift+L**: Select all occurrences
- **Alt+Click**: Add cursor at position

### 4. Folding

Fold component blocks for better overview:

```html
<!-- Foldable region -->
<include:complex-component>
  <!-- This content can be folded -->
  <content:header>...</content:header>
  <content:body>...</content:body>
  <content:footer>...</content:footer>
</include:complex-component>
```

## Troubleshooting

### Common Issues

**Issue**: Django templates not highlighting correctly

**Solution**: Check file associations in settings:

```json
{
  "files.associations": {
    "**/templates/**/*.html": "django-html"
  }
}
```

**Issue**: Prettier not formatting templates

**Solution**: Ensure parser is set correctly:

```json
{
  "[django-html]": {
    "editor.defaultFormatter": "esbenp.prettier-vscode"
  }
}
```

**Issue**: Emmet not working in Django templates

**Solution**: Add emmet language support:

```json
{
  "emmet.includeLanguages": {
    "django-html": "html"
  }
}
```

### Performance Optimization

For large Django projects:

```json
{
  "files.watcherExclude": {
    "**/node_modules/**": true,
    "**/venv/**": true,
    "**/.git/**": true,
    "**/static/**": true,
    "**/media/**": true
  },
  "search.exclude": {
    "**/node_modules": true,
    "**/venv": true,
    "**/static": true,
    "**/media": true
  }
}
```

## Team Setup

### Shared Configuration

Commit these files to share configuration:

```
.vscode/
├── settings.json          # Workspace settings
├── tasks.json            # Build tasks
├── launch.json           # Debug configuration
├── extensions.json       # Extension recommendations
└── *.code-snippets       # Custom snippets
```

### Project README

Document VS Code setup in your project:

```markdown
## VS Code Setup

This project includes VS Code configuration for optimal development experience.

### Quick Setup
1. Install recommended extensions when prompted
2. Python interpreter should auto-detect virtual environment
3. Templates will auto-format on save

### Manual Setup
1. Install extensions: `Ctrl+Shift+P` → "Extensions: Show Recommended Extensions"
2. Select Python interpreter: `Ctrl+Shift+P` → "Python: Select Interpreter"
3. Verify formatting: Open any .html file and save

### Available Tasks
- `Ctrl+Shift+P` → "Tasks: Run Task"
  - Django: Run Server
  - Format Templates
  - Build Docs
  - Serve Docs
```

## Advanced Configuration

### Custom Theme for Components

Create a custom VS Code theme for better component visibility:

```json
{
  "editor.tokenColorCustomizations": {
    "textMateRules": [
      {
        "scope": "entity.name.tag.include",
        "settings": {
          "foreground": "#61AFEF",
          "fontStyle": "bold"
        }
      },
      {
        "scope": "entity.name.tag.content",
        "settings": {
          "foreground": "#98C379",
          "fontStyle": "italic"
        }
      }
    ]
  }
}
```

### Integrated Terminal Setup

Configure terminal for Django development:

```json
{
  "terminal.integrated.profiles.linux": {
    "Django": {
      "path": "/bin/bash",
      "args": ["-c", "source venv/bin/activate && exec bash"]
    }
  },
  "terminal.integrated.defaultProfile.linux": "Django"
}
```

## Next Steps

- Set up [Prettier Integration](../tooling-integration/prettier-formatting.md) for consistent formatting
- Configure [Tailwind CSS](../tooling-integration/tailwind-css.md) for utility-first styling
- Explore [Component Patterns](../building-components/component-patterns.md) for development best practices