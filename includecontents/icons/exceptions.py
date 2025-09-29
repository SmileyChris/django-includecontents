"""
Custom exception classes for the icons subsystem.
"""


class IconError(Exception):
    """Base exception for all icon-related errors."""

    pass


class IconNotFoundError(IconError):
    """Raised when a requested icon cannot be found."""

    pass


class IconBuildError(IconError):
    """Raised when sprite building fails."""

    pass


class IconConfigurationError(IconError):
    """Raised when icon configuration is invalid."""

    pass


class IconAPIError(IconError):
    """Raised when Iconify API requests fail."""

    pass
