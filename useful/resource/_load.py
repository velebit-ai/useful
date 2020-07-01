import logging
import time

from useful.resource.readers import ResourceURL, readers
from useful.resource.parsers import parsers

_log = logging.getLogger(__name__)


def cached_load(timeout=300):
    """
    Define timeout to be used in `load()` function.

    Args:
        timeout (int, optional): Number of seconds to cache data without
            checking if it has changed in any way. Defaults to 300.

    Returns:
        function: A function using timeout variable
    """
    memory = {}

    def load(url, mimetype=None, parser=None, hook=None):
        """
        Load resource from uri or cache if already used before.

        Args:
            url (str): String represeting URL specified in RFC 1738.
            mimetype (str, optional): Forced MIME type if not None. Defaults to
                None.
            parser (useful.resource.parsers.Parser, optional): A parser class
                to use instead of parsers from useful.resource.parsers.parsers.
                Defaults to None.
            hook (callable, optional): An optional function to call after
                reading and parsing the data. Defaults to None.

        Raises:
            ValueError: No reader supports provided url scheme
            ValueError: No parser supports provided mimetype

        Returns:
            object: Final data after running reader, parser and hook on the
                resource url
        """
        hash_ = None

        # get the reader from url
        resource_url = ResourceURL(url, mimetype=mimetype)
        try:
            reader = readers[resource_url.scheme]
        except KeyError:
            raise ValueError(
                f"Unsupported reader scheme '{resource_url.scheme}'")

        reader = reader(url=resource_url)

        # if url has been cached for less than `timeout` or hash sum of the
        # resource is still equal, return cached value
        if url in memory:
            now = time.time()
            if now - memory[url]['time'] < timeout:
                _log.debug(
                    f"Url '{url}' in memory for less then {timeout} seconds",
                    extra={"url": url, "timeout": timeout})
                return memory[url]['data']
            else:
                hash_ = reader.hash()
                if hash_ == memory[url]['hash']:
                    _log.debug(
                        f"Url '{url}' in memory hasn't changed hash sum",
                        extra={"url": url, "hash": hash_})
                    # update object timestamp in memory
                    memory[url]['time'] = now
                    return memory[url]['data']

        # if url has been cached but needs to update use cached hook as a
        # hook, otherwise use function parameter hook as hook object
        hook = memory.get(url, {}).get("hook", hook)
        # use already calculated above hash sum or calculate hash sum if it was
        # never calculated
        hash_ = hash_ or reader.hash()

        # use user-provided parser or get parser from mimetype
        try:
            parser = parser or parsers[resource_url.mimetype]
            parser = parser(reader=reader)
        except KeyError:
            raise ValueError(
                f"Unsupported parser mimetype {resource_url.mimetype}")

        # parse data provided by reader
        data = parser.parse()

        # call hook on data
        if hook is not None:
            data = hook(data)

        # cache results and other relevant data
        memory[url] = {
            'time': time.time(),
            'hash': hash_,
            'data': data,
            'hook': hook
        }
        _log.debug(f"Upserting url '{url}' in memory",
                   extra={"url": url, "hash": hash_})
        return data

    return load


load = cached_load(timeout=300)
