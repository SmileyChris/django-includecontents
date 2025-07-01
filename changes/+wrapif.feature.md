Add {% wrapif %} template tag for conditional wrapping.

The new `{% wrapif %}` tag provides a clean way to conditionally wrap content with HTML elements:

- **Shorthand syntax**: `{% wrapif condition then "tag" attr=value %}content{% endwrapif %}`
- **Full template syntax**: Supports `{% contents %}` blocks for complex wrappers
- **Multiple conditions**: `{% wrapelif %}` and `{% wrapelse %}` for if/elif/else patterns
- **Complex conditions**: Inherits all Django template operators (and, or, not, comparisons, in)
- **Multiple named contents**: Support for multiple content blocks in full syntax
- **Attribute handling**: Proper escaping and boolean attribute support

This reduces template boilerplate and improves readability when conditionally wrapping content.