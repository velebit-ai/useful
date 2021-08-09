import logging
from io import BytesIO

import boto3

from useful.resource.util import maybe_urlparse
from useful.resource.downloaders._downloaders import add_downloader

_log = logging.getLogger(__name__)


def s3(url, *args, **kwargs):
    """
    An S3 in-memory downloader. Downloads the file in-memory and returns an
    io.BytesIO object with downloaded bytes.
    """
    parsed = maybe_urlparse(url)
    bucket_name = parsed.netloc
    path = parsed.path.lstrip("/")
    _log.debug(f"Parsing url '{url}' into '{bucket_name=}' and '{path=}'")

    _log.debug("Initializing boto3 s3 client")
    s3 = boto3.client('s3', *args, **kwargs)  # noqa

    _log.debug(f"Downloading the object '{bucket_name}/{path}' into file-like"
               f" object")
    buffer = BytesIO()
    s3.download_fileobj(bucket_name, path, buffer)

    return buffer


# register downloader for s3:// schema
add_downloader("s3", s3)
