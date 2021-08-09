"""
This is a temporary solution with functions `add_type` and `guess_type`
compatible with standard `mimetypes` library implementations. The reason for
this implementation is a bug introduced in mimetypes library for Python
versions 3.7 and higher. The bug was introduced while solving another bug

                    https://bugs.python.org/issue4963
"""

import logging
import os.path

from useful.resource.util import maybe_urlparse

types_map = {
    ".json": "application/json",
    ".csv": "text/csv",
    ".txt": "text/plain",
    ".pkl": "application/pickle",
    ".pickle": "application/pickle",
}

_log = logging.getLogger(__name__)


def add_type(type, ext, strict=True):
    """
    Arguments type, ext, and strict are named in a way to be compatible with
    standard library function mimetypes.add_type(). Since here we use a subset
    of its capabilities, argument strict is not used at all.
    """
    _log.debug(f"Adding extension-mimetype mapping: {ext.lower()} -> "
               f"{type.lower()}")
    global types_map
    types_map[ext.lower()] = type.lower()


def guess_type(url, strict=True):
    """
    Arguments url and strict are named in a way to be compatible with standard
    library function mimetypes.guess_type(). Since here we use a subset of its
    capabilities, argument strict is not used at all.

    The only difference is that mimetypes.guess_type() only accepts url as a
    string and we also support the urllib.parse.ParseResult.
    """
    parsed = maybe_urlparse(url)
    path = parsed.path
    ext = os.path.splitext(path)[1].lower()

    if ext in types_map:
        _log.debug(f"Known type for '{url}': ({types_map[ext], None})")
        return types_map[ext], None

    _log.debug(f"Unknown type for '{url}': (None, None)")
    return None, None


def remove_ext(ext):
    """
    A helpful function to remove an extension if it exists.

    Args:
        ext (str): Extension to be removed.
    """
    _log.debug(f"Removing extension: {ext.lower()}")
    return types_map.pop(ext.lower(), None)


def remove_type(type):
    """
    A helpful function to remove all extensions that map into specific mimetype

    Args:
        type (str): A mimetype to remove
    """
    drop = set()
    for key, value in types_map.items():
        if value == type:
            drop.add(key)

    _log.debug(f"Selected extensions to remove: {list(drop)}")
    for ext in drop:
        remove_ext(ext)
