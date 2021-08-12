import logging
import os
import threading
from functools import lru_cache

import s3fs

from useful.resource.util import maybe_urlparse
from useful.resource.downloaders._downloaders import add_downloader
from useful.decorators import threaded_decorator

_log = logging.getLogger(__name__)
threaded_lru_cache = threaded_decorator(lru_cache(maxsize=1024))


@threaded_lru_cache
def get_s3fs_filesystem(anon=False, **client_kwargs):
    _log.debug("Initializing s3fs.S3FileSystem for thread: "
               f"{threading.current_thread().ident}")
    return s3fs.S3FileSystem(anon=anon, client_kwargs=client_kwargs)


def _s3fs(url, *args, **kwargs):
    """
    An S3 on-demand downloader. Returns a file-like object that is being
    downloaded as it is being read.
    """
    parsed = maybe_urlparse(url)
    bucket_name = parsed.netloc
    path = parsed.path.lstrip("/")
    _log.debug(f"Parsing url '{url}' into '{bucket_name=}' and '{path=}'")

    # allow the s3 endpoint to be changed through env variable. This makes it
    # possible to use self-hosted S3 alternatives
    endpoint_url = os.environ.get('AWS_S3_ENDPOINT_URL', None)
    client_kwargs = {}
    if endpoint_url is not None:
        client_kwargs["endpoint_url"] = endpoint_url

    _log.debug("Initializing s3fs.S3FileSystem client")
    fs = get_s3fs_filesystem(anon=False, **client_kwargs)

    _log.debug(f"Opening the object '{bucket_name}/{path}' for on-demand"
               f" download")
    return fs.open(f"{bucket_name}/{path}", *args, **kwargs)


# register downloader for s3fs:// schema
add_downloader("s3fs", _s3fs)
