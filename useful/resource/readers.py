import hashlib
import logging
from abc import ABC, abstractmethod

try:
    import botocore
    import boto3
    import s3fs
    EXTRA_S3_INSTALLED = True
except ModuleNotFoundError:
    EXTRA_S3_INSTALLED = False

try:
    import gcsfs
    EXTRA_GS_INSTALLED = True
except ModuleNotFoundError:
    EXTRA_GS_INSTALLED = False

from useful.resource import mimetypes

_log = logging.getLogger(__name__)


class ResourceURL:
    """
    An object that parses url and defines a resource by its location, schema
    and mimetype.

    Args:
        url (str): String represeting URL specified in RFC 1738.
        mimetype (str, optional): MIME type conforming definions in RFC 2045,
            RFC 2046, RFC 2047, RFC 4288, RFC 4289 and RFC 2049. Allow
            additional non-standard "application/yaml" mimetype for ".yaml" and
            ".yml" extensions. Override extracted mimetype from url if
            specified. Defaults to None.
    """
    def __init__(self, url, mimetype=None):
        self.url = url
        split = url.split("://", 1)
        if len(split) == 1:
            self.scheme, self.path = "file", split[0]
        else:
            self.scheme, self.path = split

        # specify mimetype from argument or read from url extension
        self.mimetype = mimetype or mimetypes.guess_type(url)[0]


class Reader(ABC):
    def __init__(self, url):
        """
        Wrap ResourceURL in a way that provides an interface to open resource,
        read through it and also calculate the hash sum without opening the
        file.

        Args:
            url (ResourceURL): resource URL representing mimetype, scheme and
                location of the resource.
        """
        self.url = url

    @abstractmethod
    def open(*args, **kwargs):
        pass

    @abstractmethod
    def hash(self):
        pass


class LocalFile(Reader):
    def __init__(self, url):
        """
        Read data and calculate sha256sum for a resource from local storage.

        Args:
            url (ResourceURL): resource URI representing mimetype, scheme and
                location of the resource.

        Raises:
            AssertionError: If ResourceURL.scheme is not `file` the resource is
                not a local file.
        """
        assert url.scheme == "file"
        super().__init__(url)

    def open(self, *args, **kwargs):
        """
        Method with arguments compatible with open() with `file=self.path`.
        For more details check out

                https://docs.python.org/3/library/functions.html#open
        """
        return open(self.url.path, *args, **kwargs)

    def hash(self):
        """
        Calculate sha256sum of a local file.

        Returns:
            str: sha256sum for file located on `self.path`
        """
        _log.debug(f"Started calculating sha256sum for '{self.url.path}'",
                   extra={"path": self.url.path})
        h = hashlib.sha256()
        b = bytearray(128 * 1024)
        mv = memoryview(b)
        with open(self.url.path, 'rb', buffering=0) as f:
            for n in iter(lambda: f.readinto(mv), 0):
                h.update(mv[:n])

        sha256sum = h.hexdigest()
        _log.debug(f"Finished calculating sha256sum for '{self.url.path}'",
                   extra={"path": self.url.path, "sha256sum": sha256sum})
        return sha256sum


class S3File(Reader):
    def __init__(self, url):
        """
        Read data from s3 and use etag as hash.

        Args:
            url (ResourceURL): resource URI representing mimetype, scheme and
                location of the resource.
        Raises:
            AssertionError: If extra useful-resource[s3] is not installed
            AssertionError: If ResourceURL.scheme is not `s3` the resource is
                not an s3 resource.
        """
        assert EXTRA_S3_INSTALLED is True
        assert url.scheme == "s3"
        super().__init__(url)
        self.bucket, self.key = self.url.path.split("/", 1)
        self.fs = s3fs.S3FileSystem(anon=False)

    def open(self, *args, **kwargs):
        """
        Method with arguments compatible with open() with `file=path`. For more
        details check out

                    https://s3fs.readthedocs.io/en/latest/api.html
        """
        return self.fs.open(f"{self.bucket}/{self.key}", *args, **kwargs)

    def hash(self):
        """
        Get etag for s3 document.

        Returns:
            str: etag hash string
        """
        try:
            return boto3.client('s3').head_object(Bucket=self.bucket,
                                                  Key=self.key)['ETag'][1:-1]
        except botocore.exceptions.ClientError:
            _log.warning(f"Document {self.url.url} not found",
                         extra={"url": self.url.url})


class GSFile(Reader):
    def __init__(self, url):
        """
        Read data from Google Storage and use crc32c sum as hash.

        Args:
            url (ResourceURL): resource URI representing mimetype, scheme and
                location of the resource.
        Raises:
            AssertionError: If extra useful-resource[gs] is not installed
            AssertionError: If ResourceURL.scheme is not `gs` the resource is
                not an Google Storage resource.
        """
        assert EXTRA_GS_INSTALLED is True
        assert url.scheme == "gs"
        super().__init__(url)
        self.fs = gcsfs.GCSFileSystem()

    def open(self, *args, **kwargs):
        """
        Method with arguments compatible with open() with `file=path`. For more
        details check out

                https://gcsfs.readthedocs.io/en/latest/api.html
        """
        return self.fs.open(self.url.path, *args, **kwargs)

    def hash(self):
        """
        Get crc32c sum for a google storage document.

        Returns:
            str: crc32c checksum
        """
        try:
            return self.fs.info(self.url.path)["crc32c"]
        except FileNotFoundError:
            _log.warning(f"Document {self.url.url} not found",
                         extra={"url": self.url.url})
        except KeyError:
            _log.warning(f"Checksum 'crc32c' for {self.url.url} not found",
                         extra={"url": self.url.url})


# a simple dict of supported resource readers
readers = {
    "file": LocalFile,
    "s3": S3File,
    "gs": GSFile
}
