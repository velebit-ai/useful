from urllib.parse import urlparse, ParseResult, urlunparse


def maybe_urlparse(url, *args, **kwargs):
    """
    urllib.parse.urlparse wrapper that also accepts ParseResult as an input. In
    that case it simply returns the `url` argument.

    Args:
        url (str|urllib.parse.ParseResult): Input url to process
        *args (tuple): Args to be passed through to urllib.parse.urlparse
        *kwargs (dict): Kwargs to be passed through to urllib.parse.urlparse

    Returns:
        urllib.parse.ParseResult: parsed url
    """
    if isinstance(url, ParseResult):
        return url

    return urlparse(url, *args, **kwargs)


def maybe_urlunparse(url, *args, **kwargs):
    """
    urllib.parse.unurlparse wrapper that also accepts str as an input. In
    that case it simply returns the `url` argument.

    Args:
        url (str|urllib.parse.ParseResult): Input url to process
        *args (tuple): Args to be passed through to urllib.parse.urlunparse
        *kwargs (dict): Kwargs to be passed through to urllib.parse.urlunparse

    Returns:
        urllib.parse.ParseResult: parsed url
    """
    if isinstance(url, ParseResult):
        return urlunparse(url, *args, **kwargs)

    return url
