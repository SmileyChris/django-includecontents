# Changelog

This page shows the complete changelog for Django IncludeContents.

The full changelog is maintained in [CHANGES.md](https://github.com/yourusername/django-includecontents/blob/main/CHANGES.md) and is automatically generated using [towncrier](https://towncrier.readthedocs.io/).

## Latest Changes

--8<-- "CHANGES.md"

## Contributing Changes

This project uses towncrier for changelog management. When contributing:

1. **Create a news fragment** for your changes in the `changes/` directory
2. **Use the appropriate fragment type**: `.feature.md`, `.bugfix.md`, `.doc.md`, `.removal.md`, or `.misc.md`
3. **Follow the naming convention**:
   - For new features: `+descriptive-name.feature.md`
   - For GitHub issues: `123.bugfix.md` (where 123 is the issue number)
   - For other fixes: `+fix-description.bugfix.md`

### Example

```bash
# New feature
echo "Add support for nested component namespaces" > changes/+nested-namespaces.feature.md

# Bug fix for GitHub issue #42
echo "Fix component rendering with special characters" > changes/42.bugfix.md

# Other bug fix
echo "Fix memory leak in template caching" > changes/+fix-memory-leak.bugfix.md
```

See the [Contributing Guide](https://github.com/yourusername/django-includecontents/blob/main/CONTRIBUTING.md) for more details.