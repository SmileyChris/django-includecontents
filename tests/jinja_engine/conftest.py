"""Shared Jinja2 test fixtures and skip logic."""

from __future__ import annotations

import pytest

pytest.importorskip("jinja2")
