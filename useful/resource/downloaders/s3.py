import logging
import os
import threading
from io import BytesIO
from functools import lru_cache

import boto3

from useful.resource.util import maybe_urlparse
from useful.resource.downloaders._downloaders import add_downloader
from useful.decorators import threaded_decorator

_log = logging.getLogger(__name__)
threaded_lru_cache = threaded_decorator(lru_cache(maxsize=1024))


@threaded_lru_cache
def get_s3_resource(*args, **kwargs):
    _log.debug("Initializing boto.resource for thread: "
               f"{threading.current_thread().ident}")
    return boto3.resource('s3', *args, **kwargs)


def s3(url, *args, **kwargs):
    """
    An S3 in-memory downloader. Downloads the file in-memory and returns an
    io.BytesIO object with downloaded bytes.
    """
    parsed = maybe_urlparse(url)
    bucket_name = parsed.netloc
    path = parsed.path.lstrip("/")
    _log.debug(f"Parsing url '{url}' into '{bucket_name=}' and '{path=}'")

    # allow the s3 endpoint to be changed through env variable. This makes it
    # possible to use self-hosted S3 alternatives
    final_kwargs = {}
    endpoint_url = os.environ.get('AWS_S3_ENDPOINT_URL', None)
    if endpoint_url is not None:
        final_kwargs["endpoint_url"] = endpoint_url

    final_kwargs.update(kwargs)

    _log.debug("Initializing boto3 s3 resource")
    s3 = get_s3_resource(*args, **final_kwargs)
    bucket = s3.Bucket(bucket_name)

    _log.debug(f"Downloading the object '{bucket_name}/{path}' into file-like"
               f" object")
    buffer = BytesIO()
    bucket.download_fileobj(path, buffer)

    buffer.seek(0)
    return buffer


# register downloader for s3:// schema
add_downloader("s3", s3)
