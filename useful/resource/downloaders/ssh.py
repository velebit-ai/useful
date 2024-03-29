import logging
import threading
from io import BytesIO
from functools import lru_cache

import paramiko

from useful.resource.util import maybe_urlparse
from useful.resource.downloaders._downloaders import add_downloader
from useful.decorators import threaded_decorator

_log = logging.getLogger(__name__)
threaded_lru_cache = threaded_decorator(lru_cache(maxsize=1024))


@threaded_lru_cache
def get_paramiko_sshclient():
    _log.debug("Initializing paramiko.SSHClient for thread: "
               f"{threading.current_thread().ident}")
    ssh_client = paramiko.SSHClient()
    _log.debug("Setting missing host key policy - auto add")
    ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    _log.debug("Loading system SSH keys")
    ssh_client.load_system_host_keys()

    return ssh_client


def ssh(url, *args, **kwargs):
    """
    An ssh/scp in-memory downloader. Downloads the file in-memory and returns
    an io.BytesIO object with downloaded bytes.
    """
    parsed = maybe_urlparse(url)
    port = parsed.port or 22

    _log.debug("Initializing paramiko.SSHClient client")
    ssh_client = get_paramiko_sshclient()

    _log.debug(f"Opening SSH connection to "
               f"{parsed.username}@{parsed.hostname}:{port}")
    ssh_client.connect(parsed.hostname, port=port,
                       username=parsed.username, password=parsed.password,
                       *args, **kwargs)
    _log.debug("Opening an SFTP connection")
    sftp = ssh_client.open_sftp()

    _log.debug(f"Downloading file '{parsed.path}' into file-like object")
    buffer = BytesIO()
    sftp.getfo(parsed.path, buffer)
    buffer.seek(0)

    _log.debug("Closing SFTP connection")
    sftp.close()
    _log.debug("Closing SSH connection")
    ssh_client.close()

    return buffer


# register downloader for ssh:// schema
add_downloader("ssh", ssh)
# register downloader for scp:// schema
add_downloader("scp", ssh)
# register downloader for sftp:// schema
add_downloader("sftp", ssh)
