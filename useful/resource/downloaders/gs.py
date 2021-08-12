import logging
import threading
from io import BytesIO
from functools import lru_cache

from google.cloud import storage

from useful.resource.util import maybe_urlparse
from useful.resource.downloaders._downloaders import add_downloader
from useful.decorators import threaded_decorator

_log = logging.getLogger(__name__)
threaded_lru_cache = threaded_decorator(lru_cache(maxsize=1024))


@threaded_lru_cache
def get_gs_client(*args, **kwargs):
    _log.debug("Initializing google-cloud-storage client for thread: ",
               f"{threading.current_thread().ident}")
    return storage.Client(*args, **kwargs)


def google_storage(url, *args, **kwargs):
    """
    A Google Storage in-memory downloader. Downloads the file in-memory and
    returns an io.BytesIO object with downloaded bytes.
    """
    parsed = maybe_urlparse(url)
    bucket_name = parsed.netloc
    path = parsed.path.lstrip("/")
    _log.debug(f"Parsing url '{url}' into '{bucket_name=}' and '{path=}'")

    _log.debug("Initializing Google Cloud Storage client")
    storage_client = get_gs_client(*args, **kwargs)
    bucket = storage_client.bucket(bucket_name)

    _log.debug(f"Downloading the object '{bucket_name}/{path}' into file-like"
               f" object")
    blob = bucket.blob(path)
    buffer = BytesIO(blob.download_as_bytes())

    return buffer


# register downloader for gs:// schema
add_downloader("gs", google_storage)
