from useful.resource.downloaders._downloaders import add_downloader  # noqa
from useful.resource.downloaders._downloaders import downloaders  # noqa
from useful.resource.downloaders._downloaders import get_downloader  # noqa
from useful.resource.downloaders._downloaders import open_  # noqa
from useful.resource.downloaders._downloaders import remove_downloader  # noqa

from useful.modules import installed

# add optional downloaders if dependencies are installed
if installed("google.cloud.storage"):
    from useful.resource.downloaders import gs  # noqa

if installed("gcsfs"):
    from useful.resource.downloaders import gsfs  # noqa

if installed("boto3"):
    from useful.resource.downloaders import s3  # noqa

if installed("s3fs"):
    from useful.resource.downloaders import s3fs  # noqa

if installed("paramiko"):
    from useful.resource.downloaders import ssh  # noqa

if installed("requests"):
    from useful.resource.downloaders import http  # noqa

del installed
