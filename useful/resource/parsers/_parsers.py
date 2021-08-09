"""
In this module we have a parser registry in the form of {mimetype: parser}
dictionary. A parser is any function that accepts one required argument - a
file-like object.
"""

import csv
import json
import pickle

from useful.resource import mimetypes
from useful.resource.util import maybe_urlparse


# a simple dict of supported parsers
parsers = {
    "application/json": json.load,
    "application/pickle": pickle.load,
    "text/csv": lambda f, *args, **kwargs: list(csv.reader(f, *args, **kwargs)),  # noqa
    "text/plain": lambda f, *args, **kwargs: f.read(*args, **kwargs)
}


def add_parser(mimetype, parser, *extensions):
    """
    Add a {mimetype: parser} and/or {mimetype: extension} mappings. The
    purpose is to easily allow connecting specific parser function with a
    specific mimetype, while also registering zero or more extensions with that
    mimetype. The end result is that specific parser function will be used when
    handling any of these extensions or the mimetype.

    Args:
        mimetype (str): mimetype to use for parser and extension registration
        parser (function): function to use as a parser for specific mimetype
        *extensions ([str]): A list of file extensions to connect with provided
            mimetype.
    """
    for extension in extensions:
        mimetypes.add_type(mimetype, extension)

    parsers[mimetype] = parser


def remove_parser(mimetype):
    """
    Remove {mimetype: function} from a registry of parsers.

    Args:
        mimetype (str): mimetype to remove
    """
    return parsers.pop(mimetype, None)


def get_parser(url, mimetype=None):
    """
    Guess mimetype from url and get its parser function. If mimetype parser
    is not registered, return the "identity" parser that does nothing. Another
    optional parameter is `mimetype` which allows us to enforce mimetype and
    remove the guessing part.

    Args:
        url (str|urllib.parse.ParseResult): url possibly representing mimetype
        mimetype (str, optional): Enforce mimetype. Defaults to None which does
            no enforcing.

    Returns:
        function: A parser function
    """
    parsed = maybe_urlparse(url)
    if mimetype is None:
        mimetype = mimetypes.guess_type(parsed.path)[0]

    identity_parser = lambda x: x  # noqa
    return parsers.get(mimetype, identity_parser)
