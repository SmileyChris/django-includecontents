# Django IncludeContents tag

Provides a component-like `{% includecontents %}` tag to Django. Also includes a `{% wrapif %}` tag for conditional wrapping.

For example:

```jinja
{% load includecontents %}
{% includecontents "hello.html" %}
    <p>World</p>
{% endincludecontents %}
```

It also provides an optional Django template engine that extends this tag to
work like an HTML component.

In this example, it will include and render `components/pretty-card.html`:

```html
<include:pretty-card title="Hello">
  <p>World</p>
</include:pretty-card>
```

This engine also allows for multi-line template tags. For example:

```jinja
{% if 
  user.is_authenticated
  and user.is_staff
%}
...
{% endif %}
```

## Installation

```bash
pip install django-includecontents
```

Either install the custom template engine or just add this app to your `INSTALLED_APPS`.

### Install with template engine

Replace the default `django.template.backends.django.DjangoTemplates` backend in your settings:

```python
TEMPLATES = [
    {
        'BACKEND': 'includecontents.django.DjangoTemplates',
        ...
    },
]
```

This engine also adds `includecontents` to the built-in tag libraries so there is no need to load it in your templates.

### Install without template engine

Alternatively, add this app to your `INSTALLED_APPS` and use `{% load includecontents %}` in your templates:

```python
INSTALLED_APPS = [
    ...
    'includecontents',
]
```

## Template tag usage

The `includecontents` tag works like the `include` tag but the contents is rendered and passed to the included template as a `contents` variable.

```jinja
{% includecontents "hello.html" %}
    <p>World</p>
{% endincludecontents %}
```

### Named contents blocks

You can also have named contents blocks within the component content.

For example:

```jinja
{% includecontents "hello.html" %}
    <p>World</p>
    {% contents footer %}Footer{% endcontents %}
{% endincludecontents %}
```

Where `hello.html` template could look something like:

```jinja
<div class="card">
  <div class="content">
    {{ contents }}
  </div>
  {% if contents.footer %}
  <div class="footer">
    {{ contents.footer }}
  </div>
  {% endif %}
</div>
```

## HTML Components Usage

This requires the custom template engine to be installed.

Create a `components` directory in your templates directory. This is where you will put your component templates that are used via the HTML component format.
These components are normal Django templates that will be rendered with an isolated context. The context is passed to the component via component's attributes.

Components must not match any standard HTML tags. Actually, it's best practice to name them as HTML custom elements (1 or more ASCII letters; a hyphen; 1 or more more ASCII letters, digits or hyphens).

For example, a `components/my-card.html` template could look like:

```html
<div class="card">
  <h2>{{ title }}</h2>
  <div class="content">
    {{ contents }}
  </div>
</div>
```

Components are always rendered isolated from the parent template, so they should not rely on any context variables from the parent template.

Which will allow you to use it like this (without the need to load any template library):

```html
<include:my-card title="Hello">
  <p>World</p>
</include:my-card>
```

You can use directories within `components` to group your components. For example, `components/forms/field.html`:

```html
<include:forms:field ... />
```

You can use named [`{% contents %}` blocks](#named-contents-blocks), just like with the `includecontents` tag.

### HTML Content Syntax

When using the custom template engine, you can also use HTML-style syntax for named content blocks with `<content:name>` tags:

```html
<include:my-card title="Hello">
  <p>Main content</p>
  <content:footer>Footer content</content:footer>
  <content:sidebar>Sidebar content</content:sidebar>
</include:my-card>
```

This is equivalent to using the traditional `{% contents %}` syntax:

```html
<include:my-card title="Hello">
  <p>Main content</p>
  {% contents footer %}Footer content{% endcontents %}
  {% contents sidebar %}Sidebar content{% endcontents %}
</include:my-card>
```

The HTML content syntax provides a more consistent HTML-like experience and integrates better with HTML formatters and editors. Both syntaxes can be mixed within the same component if needed.

Some HTML formatters (like prettier) insist on quoting HTML attribute values. You can wrap the string contents in `{{ }}` to still read this as a template variable rather than a string:

```html
<include:my-card title="{{ mytitle }}" />
``` 

You can also use short-hand syntax for HTML attributes when the attribute name matches the variable name:

```html
<include:my-card {title} />
```

#### Template Tags in Attributes

Component attributes fully support Django template tags, allowing you to use dynamic URLs, conditionals, and variables:

```html
<include:ui-button 
  variant="primary" 
  href="{% url 'settings' %}" 
  class="btn {% if large %}btn-lg{% endif %}"
>
  Save Settings
</include:ui-button>
```

This works with all Django template syntax including `{% url %}`, `{{ variables }}`, `{% if %}`, `{% for %}`, and custom tags.

### Component Props

You can define the required or default props of the component in a comment at the top of its template that begins with `props `  (or `def ` to match what JinjaX uses). An exception will be raised if a required prop is not provided.

Any other attributes passed to the component that are not listed in this definition will be added to an `attrs` context variable that can render them as HTML attributes.

```jinja
{# props #}
<div {{ attrs }}>
  {{ contents }}
</div>
```

You can also provide default values for these attributes via the `{% attrs %}` template tag.

```jinja
{# props title, large=False #}

<div {% attrs class="card" %}>
...
```

This example component above would require a `title` attribute and allow an optional `large` attribute. Any other attributes will be rendered on the div, with a default class of `card` if you don't specify a class attribute.

#### Enum Props

Props can be defined with a list of allowed values (enums) by using a comma-separated list without spaces:

```jinja
{# props variant=primary,secondary,accent #}

<button {% attrs class="btn" class:btn-primary=variantPrimary class:btn-secondary=variantSecondary class:btn-accent=variantAccent %}>
  {{ contents }}
</button>
```

This component requires a `variant` prop that must be one of `primary`, `secondary`, or `accent`. Invalid values will raise a `TemplateSyntaxError`.

When an enum prop is set, the component context receives:
- The original prop value: `variant="primary"`
- A camelCased boolean for the selected value: `variantPrimary=True`

This makes it easy to conditionally apply CSS classes based on the enum value, which works particularly well with Tailwind CSS.

To make an enum prop optional, start the list with an empty value:

```jinja
{# props size=,small,medium,large #}
```

Enum values can contain hyphens, which will be converted to camelCase for the boolean variables:

```jinja
{# props theme=light-mode,dark-mode #}
{# When theme="dark-mode", themeDarkMode=True #}
```

If you want to provide multiple groups of undefined attributes, you can use `group.name` as the format.
Then render them with `{{ attrs.group }}` (or `{% attrs.group %}` if you want fallback values).

For example to call a component like this:

```html
<include:form-field label="Name" name="first_name" value="John" input.class="wide"></include:form-field>
```

It could be defined like this:

```jinja
{# props value, label="" #}

<div {% attrs class="field" %}>
  {% wrapif label then "label" %}
    {{ label }}
    <input {% attrs.input type="text" value=value %}>
  {% endwrapif %}
</div>
```

#### Kebab-cased props

Non-defined props can be "kebab-cased", for example: 

```html
<include:example my-prop="value">
```

To access a kebab-cased prop to a via the ``attrs`` variable, use its CamelCase equivalent. The ``{% attrs %}`` tag works with kebab-case fine though::

```jinja
{# props #}

{% attrs my-prop="fallback" %}

{% if attrs.myProp %}
my-prop is explicitly set to {{ attrs.myProp }}
{% endif %}
```

#### Extended / conditional classes

Prepend your class list with `"& "` to have it extended rather than replaced:

```jinja
{% attrs class="lg" %}        {# sets default class attribute to "lg" but can be overridden #}
{% attrs class="& lg p-3" %}  {# always add 'lg p-3' classes after user's classes #}
```

Append `" &"` to your class list to prepend rather than replace:

```jinja
{% attrs class="card &" %}    {# prepends 'card' class before user's classes #}
```

This allows you to control the order of classes - useful when CSS specificity or utility class ordering matters.

You can provide conditional classes for the `class` attribute using the svelte class directive format:

```jinja
{# props large=False #}

{% attrs class:lg=large %} {# adds 'lg' class if large prop is truthy #}
{% attrs class:lg %}       {# always adds 'lg' class #}
```

You can use this same conditional format on the component attributes directly:

```html
<include:my-card title="Hello" class:lg={{ is_large }}> 
  <p>World</p>
</include:my-card>
```

For negating boolean values in conditions, use the included `|not` filter:

```jinja
{% load includecontents %}
<include:my-card title="Hello" class:active="{{ disabled|not }}">
  <p>World</p>
</include:my-card>
```

#### Conditional classes in tailwindcss

Add this transform in your `tailwind.config.js` so that Tailwind picks up the
Svelte-like class directives:

```js
/** @type {import('tailwindcss').Config} */
module.exports = {
  content: {
    files: ["**/*.{html,js}", "!node_modules"],
    transform: {
      // Also handle Svelte-like class:class-name directives
      html: (content) => content.replace(/(\w):([-\w]+)/g, '$1 "$2" '),
    },
  },
  ...
```

## Prettier formatting

While not part of this package, `django-includecontents` plays very well with the [`prettier-plugin-jinja-template` plugin](https://www.npmjs.com/package/prettier-plugin-jinja-template) for Prettier.
This plugin can provide consistent formatting for your Django (and Jinja, obviously) templates.

First install it with `npm install --save-dev prettier-plugin-jinja-template`.

Then create a `.prettierrc` file in your project root with the following content:

```json
{
  "plugins": ["prettier-plugin-jinja-template"],
  "overrides": [
    {
      "files": ["**/{templates,jinja2}/**/*.html"],
      "options": {
        "parser": "jinja-template"
      }
    }
  ]
}
```

### VScode formatting

To use this Prettier formatting within VScode, use the following two extensions:

* [Django](https://marketplace.visualstudio.com/items?itemName=batisteo.vscode-django)
* [Prettier - Code formatter](https://marketplace.visualstudio.com/items?itemName=esbenp.prettier-vscode)

Add this to your settings (`Ctrl-P`, paste `>Preferences: Open Workspace Settings (JSON)`):

```json
{
  "[django-html]": {
    "editor.formatOnSave": true,
    "editor.defaultFormatter": "esbenp.prettier-vscode"
  },
}
```

## Wrapif tag usage

The `wrapif` tag allows you to conditionally wrap content with HTML elements, providing a clean way to avoid repeating opening and closing tags based on conditions.

### Basic syntax

You can use the full template syntax with `{% contents %}` blocks:

```jinja
{% load includecontents %}
{% wrapif show_link %}
<a href="{{ url }}">
  {% contents %}Click here{% endcontents %}
</a>
{% endwrapif %}
```

When `show_link` is true, this outputs: `<a href="...">Click here</a>`
When `show_link` is false, this outputs: `Click here`

### Shorthand syntax

For simpler cases, use the `then` shorthand:

```jinja
{% wrapif show_link then "a" href=url class="link" %}
  Click here
{% endwrapif %}
```

### Wrapelse

Use `{% wrapelse %}` to provide an alternative wrapper when the condition is false:

```jinja
{% wrapif is_active then "a" href=url %}
{% wrapelse "span" class="disabled" %}
  {{ label }}
{% endwrapif %}
```

This outputs either `<a href="...">{{ label }}</a>` or `<span class="disabled">{{ label }}</span>`.

### Multiple conditions with wrapelif

```jinja
{% wrapif level == 1 then "h1" %}
{% wrapelif level == 2 then "h2" %}
{% wrapelif level == 3 then "h3" %}
{% wrapelse "p" %}
  {{ title }}
{% endwrapif %}
```

### Complex conditions

The tag supports all Django template conditional operators:

```jinja
{% wrapif user.is_authenticated and user.is_staff then "div" class="admin" %}
  Admin content
{% endwrapif %}

{% wrapif price > 100 then "span" class="expensive" %}
  ${{ price }}
{% endwrapif %}

{% wrapif status in active_statuses then "strong" %}
  {{ status }}
{% endwrapif %}
```

### Multiple named contents blocks

When using full template syntax, you can have multiple named content blocks:

```jinja
{% wrapif show_card %}
<div class="card">
  <header>{% contents header %}{{ title }}{% endcontents %}</header>
  <div class="body">
    {% contents %}{{ body_text }}{% endcontents %}
  </div>
  <footer>{% contents footer %}{{ footer_text }}{% endcontents %}</footer>
</div>
{% endwrapif %}
```

### Nested wrapif

Wrapif tags can be nested for complex conditional structures:

```jinja
{% wrapif show_section then "section" class="main" %}
  {% wrapif show_header then "header" %}
    <h1>{{ title }}</h1>
  {% endwrapif %}
  {{ content }}
{% endwrapif %}
```