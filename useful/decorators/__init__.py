import logging
import time
import threading
from functools import wraps

_log = logging.getLogger(__name__)


def retry(retries=1, delay=0, exception=Exception, retry_callback=None,
          final_callback=None):
    """
    Decorator that retries given function multiple times with specified delay
    between re-runs.

    Args:
        retries (int): number of times to retry
        delay (float): seconds to delay between re-runs
        exception (class): specify exception type to retry on. Defaults to
            Exception.
        retry_callback (function): function to call every time after wrapped
            function fails with `exception` and retry will happen. The function
            prototype is `function(e, *args, **kwargs)` where e is the raised
            exception, and args and kwargs argument passed to the original func
        final_callback (function): function to call after wrapped fails with
            `exception` for the last time and retry won't happen. The function
            prototype is `function(e, *args, **kwargs)` where e is the raised
            exception, and args and kwargs argument passed to the original func
    """
    assert delay >= 0
    if retries < 0:
        retries = float('+inf')

    def decorator(func):
        @wraps(func)
        def function(*args, **kwargs):
            call_count = 0
            max_calls = 1 + retries
            while call_count < max_calls:
                try:
                    call_count += 1
                    return func(*args, **kwargs)
                except exception as e:
                    m = f"[{call_count} / {max_calls}] Caught error '{e}'."

                    if call_count == max_calls:
                        _log.warning(
                           f"{m} All retries failed. Not retrying anymore.",
                           exc_info=True)

                        if final_callback is not None:
                            final_callback(e, *args, **kwargs)
                        raise
                    _log.warning(
                       f"{m} Retrying in {delay} seconds", exc_info=True)

                    if retry_callback is not None:
                        retry_callback(e, *args, **kwargs)
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


def threaded_decorator(decorator):
    @wraps(decorator)
    def _decorator(f):
        memory = threading.local()

        @wraps(f)
        def wrapper(*args, **kwargs):
            try:
                memory.f
            except AttributeError:
                memory.f = decorator(f)

            return memory.f(*args, **kwargs)

        return wrapper

    return _decorator
