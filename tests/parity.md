# Test Parity Overview

This document tracks coverage differences between the Django and Jinja test suites.

## Current Confidence

- Core rendering behaviours (basic includes, named contents, nesting, prop defaults, enum validation, context isolation) have coverage in both engines.
- The Jinja suite exercises icon HTML preprocessing helpers that are not asserted in Django.

## Known Gaps (Django only)

- Django framework integration (context processors, request/CSRF propagation, `includecontents` template tag class).
- Advanced attribute handling (class append/prepend/negation, JS framework event attrs, mixed template logic inside attrs, HTML `<content:*>` syntax).
- Prop definition caching, concurrency, and performance scenarios.
- Enhanced error messaging (enum suggestions, missing template guidance).

## Gaps To Port

1. Decide which Django behaviours must exist for Jinja and add matching tests:
   - Attribute syntax coverage.
   - Prop/object passing behaviour where relevant.
   - Error message assertions once the Jinja extension exposes similar feedback.
2. If features are intentionally Django-only, document that decision here and in code comments.
3. Mirror the icon preprocessing checks in the Django engine if that functionality is supported there.

## Next Review

Revisit this matrix whenever new engine features land or parity work ships. Update the sections above to reflect the new baseline.
