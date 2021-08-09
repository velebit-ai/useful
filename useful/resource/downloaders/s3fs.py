import logging

import s3fs

from useful.resource.util import maybe_urlparse
from useful.resource.downloaders._downloaders import add_downloader

_log = logging.getLogger(__name__)


def _s3fs(url, *args, **kwargs):
    """
    An S3 on-demand downloader. Returns a file-like object that is being
    downloaded as it is being read.
    """
    parsed = maybe_urlparse(url)
    bucket_name = parsed.netloc
    path = parsed.path.lstrip("/")
    _log.debug(f"Parsing url '{url}' into '{bucket_name=}' and '{path=}'")

    _log.debug("Initializing s3fs.S3FileSystem client")
    fs = s3fs.S3FileSystem(anon=False)

    _log.debug(f"Opening the object '{bucket_name}/{path}' for on-demand"
               f" download")
    return fs.open(f"{bucket_name}/{path}", *args, **kwargs)


# register downloader for s3fs:// schema
add_downloader("s3fs", _s3fs)
