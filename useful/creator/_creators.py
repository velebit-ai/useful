import builtins
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
            _log.debug(f"Created instance of class '{cls.__name__}' from a "
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
            _log.debug(f"Created instance of class '{cls.__name__}' from a "
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
            _log.debug(f"Created instance of class '{cls.__name__}' from a "
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


class ShorthandCreator(GenericCreator):
    """
    A shorthand instance creator. Dictionaries of shape

                    {
                        "class.module.ClassName": {
                            "param": "eters",
                            "other": 123
                        }
                    }

    can be parsed and instances of `class.module.ClassName` created.
    """
    @staticmethod
    def parse_cls_string(string):
        """
        Parse "module.submodule.object" to 2-tuple
        ("module.submodule", "object"). In case input string contains no dots,
        assume the module in question is '__main__' and the whole string is an
        object name.

        Args:
            string (str): An input string to parse
        
        Returns:
            tuple: A 2-tuple containing information about `(module, object)`
                parsed from the input string.
        """
        try:
            module, class_ = string.rsplit('.', 1)
        except ValueError:
            module, class_ = '__main__', string

        return module, class_

    def _create_list(self, config):
        return [self.create(item) for item in config]
    
    def _create_dict(self, config):
        return {k: self.create(v) for k, v in config.items()}

    def _create_instance(self, config):
        if len(config) != 1:
            raise ValueError("Invalid instance config")

        # take first (and only) key, extract module and class
        key = next(iter(config))
        module, class_ = self.parse_cls_string(key)
        # preorder instance creation: parse instance params before using them
        # to recursively instantiate objects without any configuration
        params = self.create(config[key])

        # use GenericCreator.create to make an actual instance
        return super().create({
            "class": {
                "name": class_,
                "module": module
            },
            "params": params
        })    

    def create(self, config):
        """
        Recursively create instances from config. Try to create instance from
        the config object and if that fails, recursively iterate through list
        or dict elements/values.

        Args:
            config (dict): A config dictionary to use for extraction of class
                name, module and params.

        Returns:
            object: Object created from config.
        """
        try:
            return self._create_instance(config)
        except Exception:
            pass

        if isinstance(config, list):
            return self._create_list(config)
        elif isinstance(config, dict):
            return self._create_dict(config)

        # if everything else fails, return raw config
        return config


class ShorthandCreatorWithCache(ShorthandCreator):
    """
    Cache only "non-builtin" instantiated objects from config by using
    ShorthandCreator. We define "non-builtin" as not having the exactly same
    type as any of the builtin types.
    """
    _cache = {}
    _builtin_types = {
        t for t in builtins.__dict__.values() if isinstance(t, type)}

    @staticmethod
    def _calc_config_hash(config):
        """
        When working with ruamel.yaml, we can use YAML anchors (&) and aliases
        (*) to refer to already created objects. This also means that the
        dictionary produced by ruamel.yaml will share actual memory with the
        original anchor dictionary. The consequence of this is that we can
        freely use object id to cache instances by.

        Args:
            config (object): Any Python object.
        
        Returns:
            int: A hash used for differentiating different configs/objects.
        """
        return id(config)

    def _smart_cache(self, hash_, instance, config):
        """
        There is no need to cache everything. Cache only non-builtin types.
        """
        if type(instance) in self._builtin_types:
            _log.debug(f"Ignore caching builtin type {type(instance)} from "
                       f"hash '{hash_}'",
                       extra={"config": config})
            return

        _log.debug(f"Saving {type(instance)} to cache with hash '{hash_}'",
                   extra={"config": config})
        self._cache[hash_] = instance

    def create(self, config):
        """
        Reuse cached instance if current config was already parsed, which is
        determined by a custom hash value. In case it wasn't parsed already,
        parse it and possibly* add it to cache.
        
        * see `ShorthandCreatorWithCache._smart_cache` for more details

        Args:
            config (dict): A config dictionary to use for extraction of class
                name, module and params.

        Returns:
            object: Object created from config.
        """
        hash_ = self._calc_config_hash(config)
        if hash_ not in self._cache:
            instance = super().create(config)
            _log.debug(f"Creating {type(instance)} from hash '{hash_}'",
                       extra={"config": config})
            self._smart_cache(hash_, instance, config)
        else:
            _log.debug(f"Using cached {type(instance)} from hash '{hash_}'",
                       extra={"config": config})
            instance = self._cache[hash_]

        return instance


def get_object(key):
    """
    A ShorthandCreator companion function used for getting any object from
    the configuration. For example, config

                    {
                        "function": {
                            "useful.creators.get_object": "math.sqrt",
                        }
                    }

    will be parsed as

                    {
                        "function": math.sqrt
                    }

    This allows us to access variables, classes, functions etc.
    """
    module_name, object_name = ShorthandCreator.parse_cls_string(key)
    module = importlib.import_module(module_name)
    return getattr(module, object_name)
