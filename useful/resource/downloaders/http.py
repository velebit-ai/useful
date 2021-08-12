import logging
import requests
import threading
from io import BytesIO
from functools import lru_cache

from useful.resource.downloaders._downloaders import add_downloader
from useful.resource.util import maybe_urlunparse
from useful.decorators import threaded_decorator

_log = logging.getLogger(__name__)
threaded_lru_cache = threaded_decorator(lru_cache(maxsize=1024))


@threaded_lru_cache
def get_session():
    _log.debug(f"Initializing HTTP requests.Session for thread: "
               f"{threading.current_thread().ident}")
    return requests.Session()


def http(url, *args, **kwargs):
    """
    An http/https in-memory downloader. Downloads the file in-memory and
    returns an io.BytesIO object with downloaded bytes.
    """
    raw_url = maybe_urlunparse(url)

    session = get_session()
    _log.debug(f"Sending HTTP request: GET {raw_url}")
    response = session.get(raw_url, *args, **kwargs)
    return BytesIO(response.content)


# register downloader for http:// schema
add_downloader("http", http)
# register downloader for https:// schema
add_downloader("https", http)
