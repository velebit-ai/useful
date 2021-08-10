import logging
import requests
from io import BytesIO

from useful.resource.downloaders._downloaders import add_downloader
from useful.resource.util import maybe_urlunparse

_log = logging.getLogger(__name__)


def http(url, *args, **kwargs):
    """
    An http/https in-memory downloader. Downloads the file in-memory and
    returns an io.BytesIO object with downloaded bytes.
    """
    raw_url = maybe_urlunparse(url)

    _log.debug(f"Sending HTTP request: GET {raw_url}")
    response = requests.get(raw_url, *args, **kwargs)
    return BytesIO(response.content)


# register downloader for http:// schema
add_downloader("http", http)
# register downloader for https:// schema
add_downloader("https", http)
