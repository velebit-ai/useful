import builtins
import collections
import importlib
import logging
from abc import ABC, abstractmethod
from keyword import iskeyword

_log = logging.getLogger(__name__)


def _is_non_string_iterable(x):
    """
    Test whether `x` is a non-string iterable.

    Args:
        x (object): Test subject.

    Returns:
        bool: True if non-string iterable. False otherwise
    """
    return (isinstance(x, collections.abc.Iterable) and
            not isinstance(x, str))


def is_valid_variable_name(name):
    """
    A function that checks if a string can be a variable name in Python. This
    is used to restrict the allowed placeholder names to allow them being
    forwarded into `inject_placeholder` as variables.
    """
    return name.isidentifier() and not iskeyword(name)


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
                       f"non string, non-dict iterable",
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


class Placeholder:
    """
    A placeholder object that will be created in place of <placeholder_name>
    values in the config by ShorthandCreator.
    """
    def __init__(self, name):
        self.name = name


class ShorthandCreator(GenericCreator):
    """
    A shorthand instance creator. Dictionaries of shape

                    {
                        "class.module.ClassName": {
                            "param": "eters",
                            "other": 123
                        }
                    }

    can be parsed and instances of `class.module.ClassName` created. This
    creator also implements internal cache to take advantage of input configs
    with multiple occuring references. For example, in case we have

                    configuration = {
                        "class.module.ClassName": {
                            "param": "eters",
                            "other": 123
                        }
                    }

    and

                    config = {
                        "first": configuration,
                        "second": configuration
                    }

    the ShorthandCreator will return a dictionary

                    {
                        "first": instance_from_configuration,
                        "second": instance_from_configuration
                    }

    where instance is created only once, and afterwards simply a reference is
    used, the same way it happens in the input config. On the other hand, if we
    have

                    config = {
                        "first": {
                            "class.module.ClassName": {
                                "param": "eters",
                                "other": 123
                            }
                        },
                        "second": {
                            "class.module.ClassName": {
                                "param": "eters",
                                "other": 123
                            }
                        }
                    }

    the ShorthandCreator will return a dictionary

                    {
                        "first": instance_1_from_configuration,
                        "second": instance_2_from_configuration
                    }

    where instance_1_from_configuration and instance_2_from_configuration are
    separate instances of the same class.

    An addition to the original version also supports placeholder values. This
    means whenever a string value '<placeholder_name>' exists in a config, it
    will be evaluated as `Placeholder(name="placeholder_name")`. Starting and
    ending placeholder character can be configured via `left_placeholder_char`
    and `right_placeholder_char` parameters.

    Args:
        left_placeholder_char (str, optional): A left placeholder character.
            Everything between left and right chars is a placeholder name.
            Defaults to '<'
        right_placeholder_char (str, optional): A right placeholder character.
            Everything between left and right chars is a placeholder name.
            Defaults to '>'
        class_key (str, optional): A dictionary key to read when selecting
            a sub-dictionary containing keys "name" and "module" with class
            name and module, respectively. Defaults to "class".
        params_key (str, optional): A dictionary key to read when selecting
            values forwared to a class from key "class". Defaults to
            "params".
    """
    _builtin_types = {
        t for t in builtins.__dict__.values() if isinstance(t, type)}

    def __init__(self, left_placeholder_char='<', right_placeholder_char='>',
                 class_key="class", params_key="params"):
        super().__init__(class_key=class_key, params_key=params_key)
        self.left_placeholder_char = left_placeholder_char
        self.right_placeholder_char = right_placeholder_char

    @staticmethod
    def parse_dotted_key(key):
        """
        Parse "module.submodule.object" to 2-tuple
        ("module.submodule", "object"). In case input string contains no dots,
        raise an exception.

        Args:
            key (str): An input string to parse

        Returns:
            tuple: A 2-tuple containing information about `(module, object)`
                parsed from the input string.

        Raises:
            ValueError: In case input contains no dots
        """
        if '.' not in key:
            raise ValueError(f"Input string *must* contain both module and an "
                             f"object. String '{key}' does not.")

        return key.rsplit('.', 1)

    def _create_list(self, config, cache):
        return [self.create(item, cache) for item in config]

    def _create_dict(self, config, cache):
        return {k: self.create(v, cache) for k, v in config.items()}

    def _create_instance(self, config, cache):
        """
        Convert

                    {
                        "class.module.ClassName": {
                            "param": "eters",
                            "other": 123
                        }
                    }

        to `class.module.ClassName(param="eters", other=123)` instance.

        Args:
            config (dict): A config dictionary to use for extraction of class
                name, module and params.
            cache (dict): Cache to use when creating instance recursively.

        Returns:
            object: Instance created from config.
        """
        # take first (and only) key, extract module and class
        key = next(iter(config))
        module, class_ = self.parse_dotted_key(key)
        # preorder instance creation: parse instance params before using them
        # to recursively instantiate objects without any configuration
        params = self.create(config[key], cache)

        # use GenericCreator.create to make an actual instance
        return super().create({
            "class": {
                "name": class_,
                "module": module
            },
            "params": params
        })

    def _create_anything(self, config, cache=None):
        """
        Main function for actual config parsing and object creation. Here we
        recursively create instances from config. Try to create instance from
        the config object and if that fails, recursively iterate through list
        or dict elements/values. If the config is a string, check whether it
        is a string that can be parsed as a Placeholder, and create one if it
        is. If everything fails, leave the input config as-is.

        Args:
            config (dict): A config dictionary to use for extraction of class
                name, module and params.
            cache (dict): Cache to use when creating instance recursively.

        Returns:
            object: Object created from config.
        """
        if isinstance(config, list):
            return self._create_list(config, cache)
        elif isinstance(config, dict):
            # only try to create an instance from dictionaries with a single
            # key
            if len(config) == 1:
                key = next(iter(config))
                # only create an instance from "dotted keys"
                if '.' in key:
                    return self._create_instance(config, cache)

            # if we are unable to create an instance from dict, assume it is a
            # dictionary
            return self._create_dict(config, cache)
        # if config is a string try to create an instance of Placeholder
        elif isinstance(config, str) and len(config) >= 2:
            first = config[0]
            placeholder_name = config[1:-1]
            last = config[-1]

            # check if first and last characters are valid
            first_is_valid = first == self.left_placeholder_char
            last_is_valid = last == self.right_placeholder_char

            if first_is_valid and last_is_valid:
                if not is_valid_variable_name(placeholder_name):
                    raise ValueError(f"Placeholder name '{placeholder_name}' "
                                     "is not a valid Python identifier")
                return Placeholder(name=placeholder_name)

        # if everything else fails, return raw config
        return config

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

    def _smart_cache(self, cache, hash_, instance, config):
        """
        There is no need to cache everything. Cache only non-builtin types.

        Args:
            cache (dict): Cache to use when creating instance recursively.
            hash_ (int): A hash used for differentiating different
                configs/objects.
            instance (object): Actual instance to cache (or not).
            config (dict): Config from which instance was created. Passed
                merely for the purpose of more verbose logging.

        Returns:
            dict: updated input cache. Returned for convenience only.
        """
        if type(instance) in self._builtin_types:
            _log.debug(f"Ignore caching builtin type {type(instance)} from "
                       f"hash '{hash_}'",
                       extra={"config": config})
            return cache

        _log.debug(f"Saving {type(instance)} to cache with hash '{hash_}'",
                   extra={"config": config})
        cache[hash_] = instance
        return cache

    def create(self, config, cache=None):
        """
        Reuse cached instance if current config was already parsed, which is
        determined by a custom hash value. In case it wasn't parsed already,
        parse it and possibly* add it to cache.

        * see `ShorthandCreatorWithCache._smart_cache` for more details

        Args:
            config (dict): A config dictionary to use for extraction of class
                name, module and params.
            cache (dict): Cache to use when creating instance recursively.

        Returns:
            object: Object created from config.
        """
        if cache is None:
            cache = {}

        hash_ = self._calc_config_hash(config)
        if hash_ not in cache:
            instance = self._create_anything(config, cache)
            _log.debug(f"Creating {type(instance)} from hash '{hash_}'",
                       extra={"config": config})
            cache = self._smart_cache(cache, hash_, instance, config)
        else:
            instance = cache[hash_]
            _log.debug(f"Using cached {type(instance)} from hash '{hash_}'",
                       extra={"config": config})

        return instance


def apply(config, f):
    """
    Apply a function f on the leafs of the config. This function works inplace,
    which means that the input argument `config` *MIGHT* be modified.

    Args:
        config (dict, list or anything): A config to apply the function on.
        f (function): A function to apply on the leaf elements of the config.
    """
    if isinstance(config, dict):
        keys_or_indices = list(config.keys())
    elif _is_non_string_iterable(config):
        keys_or_indices = range(len(config))
    else:
        return f(config)

    for ki in keys_or_indices:
        value = config[ki]
        config[ki] = apply(value, f)

    return config


def _inject_placeholder(value, **kwargs):
    """
    A function intended to be used with the function apply and ShorthandCreator
    to add full support for placeholders. It checks whether a value is an
    instance of the Placeholder class, and if its, it returns the actual value
    if provided within kwargs.
    """
    if isinstance(value, Placeholder):
        if value.name in kwargs:
            return kwargs[value.name]

    return value


def inject_placeholders(config, **kwargs):
    """
    A simple function combining apply and _inject_placeholders intendend to be
    used together with ShorthandCreator.
    """
    return apply(config, lambda value: _inject_placeholder(value, **kwargs))


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

    Args:
        key (str): A string of form "module.submodule.object", parseable by
            ShorthandCreator.parse_dotted_key method. A valid example would
            be "math.sqrt".

    Returns:
        object: imported object
    """
    module_name, object_name = ShorthandCreator.parse_dotted_key(key)
    module = importlib.import_module(module_name)
    return getattr(module, object_name)
