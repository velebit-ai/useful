import logging

from useful.resource.util import maybe_urlparse
from useful.resource.downloaders import open_
from useful.resource.parsers import get_parser

_log = logging.getLogger(__name__)


def load(url, mimetype=None, parser=None, hook=None,
         downloader_args=(), downloader_kwargs=None,
         parser_args=(), parser_kwargs=None,
         hook_args=(), hook_kwargs=None):
    """
    1. Load resource from uri, if schema is supported
    2. Parse it you know how, if not, return file-like object.
    3. call hook on (potentially) parsed data

    Args:
        url (str): String represeting URL specified in RFC 1738.
        mimetype (str, optional): Forced MIME type if not None. Defaults to
            None.
        parser (function, optional): A parser function to use instead of
            predefined parsers from useful.resource.parsers.parsers. Function
            accepts only one argument: a file-like object to access the file
            intended for parsing. Defaults to None.
        hook (callable, optional): An optional function to call after
            reading and parsing the data. Defaults to None.
        downloader_args (tuple, optional): Args to pass to downloader. Defaults
            to ().
        downloader_kwargs (dict, optional): Kwargs to pass to downloader.
            Defaults to None.
        parser_args (tuple, optional): Args to pass to parser. Defaults to ().
        parser_kwargs (dict, optional): Kwargs to pass to parser. Defaults to
            None.
        hook_args (tuple, optional): Args to pass to hook. Defaults to ().
        hook_kwargs (dict, optional): Kwargs to pass to hook. Defaults to None.

    Returns:
        object: Final data after running reader, parser and hook on the
            resource url
    """
    if downloader_kwargs is None:
        downloader_kwargs = {}

    if parser_kwargs is None:
        parser_kwargs = {}

    if hook_kwargs is None:
        hook_kwargs = {}

    # get the downloader from url
    resource_url = maybe_urlparse(url)
    _log.debug(f"Download resource '{url}'")
    in_memory_file = open_(resource_url, *downloader_args, **downloader_kwargs)
    parser = parser or get_parser(resource_url, mimetype=mimetype)
    _log.debug(f"Parse resource '{url}'")
    data = parser(in_memory_file, *parser_args, **parser_kwargs)

    # call hook on data
    if hook is not None:
        _log.debug(f"Call hook on resource '{url}'")
        return hook(data, *hook_args, **hook_kwargs)
    else:
        _log.debug(f"Do not call hook on resource '{url}'")

    return data
