# DjangoX

DjangoX is a simple Django template engine that provides a simple way to use component based architecture in Django.

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
pip install djangox
```

Replace the default `DjangoTemplates` backend in your settings with the `DjangoXTemplates` backend:

```python
TEMPLATES = [
    {
        'BACKEND': 'djangox.backends.DjangoXTemplates',
        ...
    },
]
```

## Usage

Create a `components` directory in your templates directory. This is where you will put your component templates.

Components are normal Django templates which will be rendered with an isolated context. The context is passed to the component via component's attributes.

A ``contents`` attribute is always passed to the component which contains the contents of the component.


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