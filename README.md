# Django IncludeContents tag

Provides a component-like `{% includecontents %}` tag to Django.

For example:

```jinja
{% load includecontents %}
{% includecontents "hello.html" %}
    <p>World</p>
{% endincludecontents %}
```

It also provides a simple Django template engine that extends this tag to work
like an HTML component.

In this example, it will include and render `components/card.html`:

```html
<include:card title="Hello">
  <p>World</p>
</include:card>
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

To use the custom template engine, replace the default `DjangoTemplates` backend in your settings:

```python
TEMPLATES = [
    {
        'BACKEND': 'includecontents.backend.Templates',
        ...
    },
]
```

This engine also adds `includecontents` to the built-in tags so there is no need to load it.

If you don't want the custom engine, just add this app to your `INSTALLED_APPS` and load the tag in your templates:

```python
INSTALLED_APPS = [
    ...
    'includecontents',
]
```

```jinja
{% load includecontents %}

...

{% includecontents %}...{% endincludecontents %}
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

Create a `components` directory in your templates directory. This is where you will put your component templates that are used via the HTML component format.
These components are normal Django templates that will be rendered with an isolated context. The context is passed to the component via component's attributes.

Components must be CamelCase and not match any standard HTML tags.

For example, a `components/card.html` template could look like:

```html
<div class="card">
  <h2>{{ title }}</h2>
  <div class="content">
    {{ contents }}
  </div>
</div>
```

Which will allow you to use it like this (without the need to load any template library):

```html
<include:card title="Hello">
  <p>World</p>
</include:card>
```

You can use named [`{% contents %}` blocks](#named-contents-blocks), just like with the `includecontents` tag.

Some HTML formatters (like prettier) insist on quoting HTML attribute values, you can avoid this by optionally wrapping template values in `{}`:

```html
<include:card title={mytitle}></include:card>
``` 

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

If you want to provide multiple groups of undefined attributes, you can use `group.name` as the format.
Then render them with `{{ attrs.group }}` (or `{% attrs.group %}` if you want fallback values).

For example to call a component like this:

```html
<include:field label="Name" name="first_name" value="John" input.class="wide"></include:field>
```

It could be defined like this:

```jinja
{# props value, label="" #}

<div {% attrs class="field" %}>
  {% if label %}{{ '<label>'|safe }}{% endif %}
  {{ label }}
  <input {% attrs.input type="text" value=value %}>
  {% if label %}{{ '</label>'|safe }}{% endif %}
</div>
```

#### Extended / conditional classes

Prepend your class list with `"& "` to have it extended rather than replaced:

```jinja
{% attrs class="lg" %}        {# sets default class attribute to "lg" but can be overridden #}
{% attrs class="& lg p-3" %}  {# always add 'lg p-3' classes #}
```

You can provide conditional classes for the `class` attribute using the svelte class directive format:

```jinja
{# props large=False #}

{% attrs class:lg=large %} {# adds 'lg' class if large prop is truthy #}
{% attrs class:lg %}       {# always adds 'lg' class #}
```

You can use this same conditional format on the component attributes directly:

```html
<include:card title="Hello" class:lg={is_large}>
  <p>World</p>
</include:card>
```
