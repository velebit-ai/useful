import importlib
import inspect
import logging
import sys
from functools import wraps

_log = logging.getLogger(__name__)


def import_modules(*modules, raise_on_fail=True):
    """
    Import modules using their string name and set appropriate attribute in the
    module that called this function, in the same way regular import works.

    Args:
        modules ([str]): A list of strings each representing a module
        raise_on_fail (bool): If set to `True`, all modules must be imported
            successfully. If `False`, silently ignore failures. Defaults to
            True.

    Raises:
        ImportError: When `raise_on_fail = True` and the module is not found.
    """
    _caller = inspect.currentframe().f_back
    _name = _caller.f_globals['__name__']
    _this = sys.modules[_name]

    try:
        for module in modules:
            name = module.split(".", 1)[0]
            module_ = __import__(module, globals(), locals())
            setattr(_this, name, module_)
            _log.debug(f"Importing '{module}' into '{_name}'")
    except ImportError:
        if raise_on_fail:
            raise
        _log.debug(f"Failed to import '{module}' into '{_name}'")


def installed(*modules):
    """
    Check if all modules from the list are installed by importing them.

    Args:
        modules ([str]): A list of strings each representing a module

    Returns:
        bool: An indicator whether all modules from the provided list are
            installed or not.
    """
    try:
        for module in modules:
            importlib.import_module(module)
    except ImportError:
        return False
    
    return True
