"""
Parsers for discovering design tokens from various sources.

This package provides parsers for extracting design tokens from:
- Tailwind CSS 4.0 @theme directives
- Traditional tailwind.config.js theme configurations
- Custom CSS custom properties
"""

from .base import BaseTokenParser
from .css import CSSThemeParser
from .js import TailwindConfigParser
from .transformer import TailwindTokenTransformer

__all__ = [
    'BaseTokenParser',
    'CSSThemeParser',
    'TailwindConfigParser',
    'TailwindTokenTransformer',
]