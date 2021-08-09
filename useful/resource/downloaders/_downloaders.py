import logging
import requests
from io import BytesIO

from useful.resource.util import maybe_urlparse, maybe_urlunparse

_log = logging.getLogger(__name__)


def is_binary(path):
    """
    Check whether existing local path is binary.
    """
    _log.debug(f"Checking if file '{path}' is binary")

    fin = open(path, 'rb')
    try:
        CHUNKSIZE = 1024
        while 1:
            chunk = fin.read(CHUNKSIZE)
            if b'\0' in chunk:  # found null byte
                return True
            if len(chunk) < CHUNKSIZE:
                break
    finally:
        fin.close()

    return False


def local_storage(url, *args, **kwargs):
    """
    A local-storage on-demand "downloader". It simply opens a file.
    """
    parsed = maybe_urlparse(url)
    path = f"{parsed.netloc}{parsed.path}"
    mode = "rb" if is_binary(path) else "r"
    return open(path, mode, *args, **kwargs)


def http(url, *args, **kwargs):
    """
    An http/https in-memory downloader. Downloads the file in-memory and
    returns an io.BytesIO object with downloaded bytes.
    """
    raw_url = maybe_urlunparse(url)

    _log.debug(f"Sending HTTP request: GET {raw_url}")
    response = requests.get(raw_url, *args, **kwargs)
    return BytesIO(response.content)


# a simple dict of supported resource downloaders
downloaders = {
    "file": local_storage,
    "http": http,
    "https": http
}


def add_downloader(scheme, downloader):
    """
    Add a {scheme: downloader} mapping. The end result is that specific
    downloader function will be used when handling the provided scheme.

    Args:
        scheme (str): scheme to use for downloader registration
        downloader (function): function to use as a downloader for specific
            scheme
    """
    downloaders[scheme] = downloader


def remove_downloader(scheme):
    """
    Remove downloader function for the provided scheme.

    Args:
        scheme (str): Remove downloader function for this scheme
    """
    return downloaders.pop(scheme, None)


def get_downloader(url, scheme=None):
    """
    Get a downloader for specific url. If argument scheme is provided, enforce
    that scheme. Otherwise, extract the scheme from input url.

    Args:
        url (str): url to use for scheme extraction
        scheme (str, optional): scheme to enforce if provided. Defaults to None

    Raises:
        ValueError: No downloader function for provided url scheme
    """
    parsed = maybe_urlparse(url)
    if scheme is None:
        scheme = parsed.scheme or 'file'

    try:
        downloader = downloaders[scheme]
    except KeyError:
        raise ValueError(
            f"Unsupported downloader scheme '{scheme}'")

    return downloader


def open_(url, *args, **kwargs):
    """
    A "smart" function similar to Python's built-in open function. The logic is
    very simple and can be separated in 3 steps:

                1. select the scheme
                2. select the downloader function
                3. download the object from provided url

    Args:
        url (str): the location of the resource we want to download
        args (tuple): Args to pass to downloader function
        kwargs (dict): Kwargs to pass to downloader function

    Returns:
        file: A file-like object containing bytes from resource at provided url
    """
    parsed = maybe_urlparse(url)
    downloader = get_downloader(parsed)
    return downloader(url=parsed, *args, **kwargs)
