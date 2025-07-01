Add enum validation for component props.

Props can now be defined with allowed values: `{# props variant=primary,secondary,accent #}`

- Validates prop values against the allowed list
- Sets both the prop value and a camelCased boolean (e.g., `variant="primary"` and `variantPrimary=True`)
- Optional enums start with empty: `size=,small,medium,large`
- Hyphens are camelCased: `dark-mode` → `variantDarkMode`