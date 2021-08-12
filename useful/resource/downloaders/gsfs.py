import logging
import threading
from functools import lru_cache

import gcsfs

from useful.resource.util import maybe_urlparse
from useful.resource.downloaders._downloaders import add_downloader
from useful.decorators import threaded_decorator

_log = logging.getLogger(__name__)
threaded_lru_cache = threaded_decorator(lru_cache(maxsize=1024))


@threaded_lru_cache
def get_gsfs_client():
    _log.debug("Initializing GCSFileSystem for thread: "
               f"{threading.current_thread().ident}")
    return gcsfs.GCSFileSystem()


def google_storage_fs(url, *args, **kwargs):
    """
    A Google Storage on-demand downloader. Returns a file-like object that is
    being downloaded as it is being read.
    """
    parsed = maybe_urlparse(url)
    bucket_name = parsed.netloc
    path = parsed.path.lstrip("/")
    _log.debug(f"Parsing url '{url}' into '{bucket_name=}' and '{path=}'")

    _log.debug("Initializing GCSFileSystem client")
    fs = get_gsfs_client()

    _log.debug(f"Opening the object '{bucket_name}/{path}' for on-demand"
               f" download")
    return fs.open(f"{bucket_name}/{path}", *args, **kwargs)


# register downloader for gsfs:// schema
add_downloader("gsfs", google_storage_fs)
