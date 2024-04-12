"""Simple sign version."""

from importlib.metadata import PackageNotFoundError, version


def get_version():
    """Return information about the version of this application."""
    __version__ = "0.0.0-dev"
    try:
        __version__ = version("simple-sign")
    except PackageNotFoundError:
        # package is not installed
        pass
    return __version__
