import collections
import importlib
import logging
from abc import ABC, abstractmethod

_log = logging.getLogger(__name__)


def _is_non_string_iterable(x):
    """
    Test whether `x` is a non-string iterable.

    Args:
        x (object): Test subject.

    Returns:
        bool: True if non-string iterable. False otherwise
    """
    return (isinstance(x, collections.Iterable) and
            not isinstance(x, str))


class BaseCreator(ABC):
    """
    Base creator class containing abstract method BaseCreator.create(). This
    pattern is used for creating instances from pure dictionaries, allowing
    complete configuration of classes used in a program.
    """
    @abstractmethod
    def create(self, config, *args, **kwargs):
        pass

    def __call__(self, config, *args, **kwargs):
        return self.create(config, *args, **kwargs)

    @staticmethod
    def unpack_and_create(cls, config):
        """
        Unpack if config is a dict or non-string iterable and pass it when
        calling `cls.__init__`.

        Args:
            cls (type): A class to make an instance of
            config (object): An object to use as when creating an instance

        Returns:
            object: An instance of class `cls`
        """
        # if config is dictionary, unpack it using **config
        if isinstance(config, dict):
            instance = cls(**config)
            _log.debug(f"Created instance of class '{cls.__name__}' from a"
                       f"dictionary",
                       extra={
                           "class": {
                               "module": cls.__module__,
                               "name": cls.__name__
                           },
                           "config": config,
                           "config_type": type(config)})
        # if config is an iterable but not a string, unpack it using *config
        elif _is_non_string_iterable(config):
            instance = cls(*config)
            _log.debug(f"Created instance of class '{cls.__name__}' from a"
                       f"non string iterable",
                       extra={
                           "class": {
                               "module": cls.__module__,
                               "name": cls.__name__
                           },
                           "config": config,
                           "config_type": type(config)})
        # in any other case, do not unpack config
        else:
            instance = cls(config)
            _log.debug(f"Created instance of class '{cls.__name__}' from a"
                       f"single argument of type ({type(config)})",
                       extra={
                           "class": {
                               "module": cls.__module__,
                               "name": cls.__name__
                           },
                           "config": config,
                           "config_type": type(config)})

        return instance


class RegistryCreator(BaseCreator):
    def __init__(self, registry):
        """
        A simple creator that requires a registry mapping from key to python
        class. This way it is easy to create an instance from dictionaries such
        as

                            {
                                "name": {
                                    "param": "eters",
                                    "other": 123
                                }
                            }

        In dictionary above the class requiring parameters `param` and `other`
        must be registered in `registry` using key "name". A class with key
        `key` is registered if value of `key in registry` is True. The value
        for the key must be a Python class.

        Args:
            registry (dict): A registry mapping from keys to classes.
        """
        self.registry = registry

    def create(self, config):
        """
        Extract registry key along with params from config and create an
        instance.

        Args:
            config (dict): A config dictionary to use for extraction of
                registry key and class params.

        Returns:
            object: Instance created from config.

        Raises:
            AssertionError: When `config` is empty or contains more than a
                single key
            KeyError: When registry key extracted from the config is not
                registered
        """
        assert len(config) == 1
        name, params = next(iter(config.items()))
        if params is None:
            params = {}

        # get class
        try:
            cls = self.registry[name]
        except KeyError as e:
            raise KeyError(f"Class with key '{name}' is not registered") from e

        # create instance
        instance = BaseCreator.unpack_and_create(cls, params)
        _log.debug(f"RegistryCreator created instance "
                   f"'{cls.__module__}.{cls.__name__}'",
                   extra={
                       "class": {
                           "name": cls.__name__,
                           "module": cls.__module__
                       },
                       "config": config,
                       "params": params
                   })

        return instance


class GenericCreator(BaseCreator):
    def __init__(self, class_key="class", params_key="params"):
        """
        A generic instance creator. With default values `class_key="class"` and
        `params_key="params"`, dictionaries of shape

                        {
                            "class": {
                                "name": "ClassName",
                                "module": "class.module"
                            },
                            "params": {
                                "param": "eters",
                                "other": 123
                            }
                        }

        can be parsed and instances of `class.module.ClassName` created.

        Args:
            class_key (str, optional): A dictionary key to read when selecting
                a sub-dictionary containing keys "name" and "module" with class
                name and module, respectively. Defaults to "class".
            params_key (str, optional): A dictionary key to read when selecting
                values forwared to a class from key "class". Defaults to
                "params".
        """
        self.class_key = class_key
        self.params_key = params_key

    def create(self, config):
        """
        Extract and get class along with params and create an instance.

        Args:
            config (dict): A config dictionary to use for extraction of class
                name, module and params.

        Returns:
            object: Instance created from config.
        """
        # extract dict containing class module and name
        cls_config = config[self.class_key]

        # extract class name and module
        name = cls_config["name"]
        module = cls_config["module"]
        module = importlib.import_module(module)

        # extract params
        params = config.get(self.params_key)
        if params is None:
            params = {}

        # get class
        cls = getattr(module, name)
        # create instance
        instance = BaseCreator.unpack_and_create(cls, params)
        _log.debug(f"GenericCreator created instance "
                   f"'{cls.__module__}.{cls.__name__}'",
                   extra={
                       "class": {
                           "name": cls.__name__,
                           "module": cls.__module__
                       },
                       "config": config,
                       "params": params
                   })

        return instance
