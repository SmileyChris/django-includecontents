# Live Preview & Prop Editor

Every component page in the showcase combines a rendered preview, prop editor form, and copyable code snippets so you can evaluate changes instantly.

## Prop Inputs

The showcase builds a Django form from the parsed prop definitions. Each field is tagged with `data-prop`, allowing the browser script to collect values as you type. Boolean props become checkboxes, numeric props use number inputs, and enums render as select boxes.

## Preview Workflow

1. Any change triggers a debounced update.
2. The browser sends a JSON payload containing props, free-form content, and named block content to the `/preview/` endpoint.
3. The server renders the component with the supplied data inside a safe template context.
4. HTML output and fresh template code snippets are returned to the page.

CSRF protection stays enabled; the bundled JavaScript retrieves the `csrftoken` cookie and includes it in the `X-CSRFToken` header automatically.

## Code Generation

The response includes two strings:

- A `{% includecontents %}` block showing how to render the component in standard Django syntax
- An HTML-style tag (`<include:component>`) representing usage through the custom template engine

Both snippets stay aligned with the props entered in the form, so you can copy them straight into your app after tweaking values.
