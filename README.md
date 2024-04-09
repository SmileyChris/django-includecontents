# Django IncludeContents tag

Provides a component-like `{% includecontents %}` tag to Django.

For example:

```html
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

```html
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
        'BACKEND': 'includecontents.backends.Templates',
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

```html
{% load includecontents %}

...

{% includecontents %}...{% endincludecontents %}
```

## Template tag usage

The `includecontents` tag works like the `include` tag but the contents is rendered and passed to the included template as a `contents` variable.

```html
{% includecontents "hello.html" %}
    <p>World</p>
{% endincludecontents %}
```

### Named contents blocks

You can also have named contents blocks within the component content.

For example:

```html
{% includecontents "hello.html" %}
    <p>World</p>
    {% contents footer %}Footer{% endcontents %}
{% endincludecontents %}
```

Where `hello.html` template could look something like:

```html
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

### Attrs

You can define which attributes should be passed to the component in a comment at the top of the component template, and others that can have a default value.

Any other attributes passed to the component will be added to an `attrs` context variable that can render them as HTML attributes.
You can also provide default values for these attributes via the `default_attrs` filter.

```html
{# def title, large=False #}
<div {{ attrs|default_attrs:'class="card"' }}>
```

This would require a `title` attribute and allow an optional `large` attribute. Any other attributes will be rendered on the div, with a default class of `card` if you don't specify any other class.
So the following tags would all be valid:

```html
<include:card title="Hello"></include:card>
<include:card title="Hello" large></include:card>
<include:card title="Hello" id="topcard" class="my-card"></include:card>
```