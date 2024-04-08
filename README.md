# Django IncludeContents tag

Provides a component-like `{% includecontents %}` tag to Django, also providing
a simple Django template engine that extends this tag to work like an HTML
component.

For example:

```html
<Card title="Hello">
  <p>World</p>
</Card>
```

Will render a `components/Card.html` template which could look something like:

```html
<div class="card">
  <h2>{{ title }}</h2>
  <div class="content">
    {{ contents }}
  </div>
</div>
```

## Installation

```bash
pip install django-includecontents
```

To use the custom template engine, replace the default `DjangoTemplates` backend in your settings:

```python
TEMPLATES = [
    {
        'BACKEND': 'includecontents.backends.DjangoTemplates',
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

## Usage

Create a `components` directory in your templates directory. This is where you will put your component templates that are used via the HTML component format.
These components are normal Django templates that will be rendered with an isolated context. The context is passed to the component via component's attributes.

A ``contents`` attribute is always passed to the component which contains the contents of the component.

### Attrs

You can define which attributes should be passed to the component in a comment at the top of the component template, and others that can have a default value.

For example:

```html
{# def title, large=False #}
```

This will define that the `title` attribute is required and the `large` attribute is optional with a default value of `False`.

Any other attributes passed to the component will be added to an `attrs` context variable that can render them as HTML attributes.
You can also provide default values for these attributes via the `default_attrs` filter.

```
{# def title, large=False #}
<div {{ attrs|default_attrs:'class="card"' }}>
```


### Named contents blocks

You can also have named contents blocks within the component content.

For example:

```html
<Card title="Hello">
  <p>World</p>
  {% contents footer %}Footer{% endcontents %}
</Card>
```

Will render a `components/Card.html` template which could look something like:

```html
<div class="card">
  <h2>{{ title }}</h2>
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