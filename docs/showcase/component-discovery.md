# Component Discovery

The showcase registry walks every template directory recognised by the includecontents engine, looking for component templates under a `components/` folder. It builds an index the first time a page is requested and caches the results for quick navigation.

## Discovery Rules

- Only `.html` files are treated as components.
- Files or directories starting with `_` are skipped, letting you keep prototypes private.
- Subdirectories become categories (for example `forms/button.html` → “Forms”).
- Components without explicit categories fall back to a heuristic based on the filename.

## Component Naming

File paths are normalised into colon-delimited names: `forms/button.html` becomes `forms:button`, while a root component `hero.html` is exposed as `hero`. Named content blocks are detected by scanning for `{% contents block_name %}` tags, so slot inputs appear in the editor automatically.

## Refreshing the Registry

The registry only rescans when it has not yet run or when `discover(force=True)` is called. During development, simply refreshing the browser after changing templates is enough because Django reloads code and templates while `DEBUG` is enabled. For scripted workflows you can import the registry and force a refresh:

```python
from showcase.registry import registry
registry.discover(force=True)
```

Use this hook if you generate components or metadata dynamically during a build step.
