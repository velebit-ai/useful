import logging
import time
from functools import wraps

_log = logging.getLogger(__name__)


def retry(retries=1, delay=0, exception=Exception):
    """
    Decorator that retries given function multiple times with specified delay
    between re-runs.

    Args:
        retries (int): number of times to retry
        delay (float): seconds to delay between re-runs
        exception (class): specify exception type to retry on. Defaults to
            Exception.
    """
    assert retries >= 0
    assert delay >= 0

    def decorator(func):
        def function(*args, **kwargs):
            for i in range(retries + 1):
                try:
                    return func(*args, **kwargs)
                except exception as e:
                    if i == retries:
                        _log.warning(
                            f"[{retries + 1} / {retries + 1}] All retries "
                            f"failed. Caught error '{str(e)}'. Not retrying"
                            f"anymore.", exc_info=True)
                        raise
                    _log.warning(
                        f"[{i + 1} / {retries + 1}] Caught error '{str(e)}', "
                        f"retrying in {delay} seconds", exc_info=True)
                    time.sleep(delay)
        return function
    return decorator


def timing(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        start = time.time()
        result = f(*args, **kwargs)
        end = time.time()
        delta = end - start
        _log.debug(f"Function call '{f.__name__}({args=}, {kwargs=})' took "
                   f"{delta:2.6f} sec")
        return result
    return wrap
