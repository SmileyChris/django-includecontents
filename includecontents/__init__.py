from importlib.metadata import PackageNotFoundError, version

from packaging.version import Version

try:
    __version__ = Version(version("django-includecontents")).public
except PackageNotFoundError:
    __version__ = "unknown"
