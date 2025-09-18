# Metadata Reference

Component templates can be enriched with structured documentation by dropping a YAML or TOML file next to the template. Keep the filename identical to the component template, just with the new extension (`button.html` → `button.yaml`). Metadata augments the registry with human-friendly descriptions, prop details, and runnable examples.

## Naming Conventions

- Match the template path exactly. If your component lives at `templates/components/forms/button.html`, store metadata at `templates/components/forms/button.yaml` (or `.toml`).
- Both `.yaml`/`.yml` and `.toml` are supported. YAML is the default in examples below; TOML requires Python 3.11+ or the `tomli` backport.

## Supported Fields

```yaml
name: Button
category: Forms
description: Concise sidebar summary
best_practices: |
  - Short actionable tips
accessibility: |
  - Accessibility considerations
related:
  - forms:input
props:
  text:
    description: Label text rendered inside the button
    type: string
    default: Submit
  variant:
    description: Visual treatment
    type: enum
    values: [primary, secondary, danger]
examples:
  - name: Primary CTA
    description: Dominant action button
    code: |
      <include:button variant="primary">Continue</include:button>
    props:
      variant: primary
      text: Continue
```

Fields are optional—provide only the information that helps your team. Prop entries extend definitions parsed from the `{# props ... #}` comment, letting you add descriptions, defaults, and enum lists.

## Content Blocks

If a component exposes `{% contents sidebar %}` or similar slots, you can showcase interesting layouts by supplying example markup inside the `code` snippet or by including named keys within `examples[].props` to populate block editors programmatically.
