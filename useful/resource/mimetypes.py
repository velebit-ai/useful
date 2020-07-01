"""
This is a temporary solution with functions `add_type` and `guess_type`
compatible with standard `mimetypes` library implementations. The reason for
this implementation is a bug introduced in mimetypes library for Python
versions 3.7 and higher. The bug was introduced while solving another bug

                    https://bugs.python.org/issue4963
"""

import posixpath
import urllib

types_map = {
    ".json": "application/json"
}


def add_type(type, ext, strict=True):
    """
    Arguments type, ext, and strict are named in a way to be compatible with
    standard library function mimetypes.add_type(). Since here we use a subset
    of its capabilities, argument strict is not used at all.
    """
    global types_map
    types_map[ext.lower()] = type.lower()


def guess_type(url, strict=True):
    """
    Arguments url and strict are named in a way to be compatible with standard
    library function mimetypes.guess_type(). Since here we use a subset of its
    capabilities, argument strict is not used at all.
    """
    url = urllib.parse.splittype(url)[1]
    ext = posixpath.splitext(url)[1].lower()

    if ext in types_map:
        return types_map[ext], None

    return None, None
