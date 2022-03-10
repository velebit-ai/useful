import logging
import time
import threading
from functools import wraps

_log = logging.getLogger(__name__)


def _no_log(*args, **kwargs):
    """
    Dummy function that does not log anything.
    """
    return None


def _get_logger_func(logger, log_level):
    """
    Get logger's logging function for specific log level.

    Args:
        logger (logging.Logger): Which logger to use
        log_level (int or str): Integer value or string name for the logging
            level wanted.

    Returns:
        function: logger's logging function for the specific log level.
    """
    original_log_level = log_level
    # if log_level = None, disable logging completely
    if log_level is None:
        return _no_log

    # if log_level is str, convert into int
    if isinstance(log_level, str):
        log_level = logging.getLevelName(log_level)

    if not isinstance(log_level, int):
        raise ValueError(f"log_level='{original_log_level}' is not a valid "
                         "log_level name")

    if not logger.isEnabledFor(log_level):
        return _no_log

    # if logs are enabled, get custom logger log function for specific level
    return lambda msg, *a, **kw: logger._log(log_level, msg, a, **kw)


def retry(retries=1, delay=0, exception=Exception, retry_callback=None,
          final_callback=None, retry_log_level=logging.WARNING,
          retry_log_traceback=True):
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
        retry_log_level (int or str): log level to be used for logging retry
            fails. Defaults to logging.WARNING. If set to None, no logging will
            be used.
        retry_log_traceback (bool): A flag indicating whether or not retry logs
            should contain exception traceback.
    """
    assert delay >= 0
    if retries < 0:
        retries = float('+inf')

    retry_log_func = _get_logger_func(_log, retry_log_level)

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
                        retry_log_func(
                           f"{m} All retries failed. Not retrying anymore.",
                           exc_info=retry_log_traceback)

                        if final_callback is not None:
                            final_callback(e, *args, **kwargs)
                        raise
                    retry_log_func(
                       f"{m} Retrying in {delay} seconds",
                       exc_info=retry_log_traceback)

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
