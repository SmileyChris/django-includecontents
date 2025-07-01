Add class prepend syntax for component attrs.

Classes can now be prepended with `{% attrs class="card &" %}` syntax.

- Append `" &"` to prepend component classes before user-provided classes
- Complements existing `"& "` syntax which appends after user classes
- Useful when CSS specificity or utility class ordering matters