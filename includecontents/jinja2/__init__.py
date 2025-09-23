"""Jinja2 support package for includecontents.

This subpackage houses an experimental Jinja2 extension that mirrors the
component-centric features exposed through the Django template integration.
The goal is to provide an opt-in API without impacting existing Django users.

Modules are intentionally skeletal for now; they will be fleshed out as the
prototype matures and test coverage is added.
"""

from __future__ import annotations

from .extension import IncludeContentsExtension

__all__ = ["IncludeContentsExtension"]
