# useful

This repo contains a collection of solutions to often ocurring problems. We deal with unified way to setup and standardize logs, along with a way to simply load both local and remote configuration files and other resources.

## useful.logs

A simple function for Python logging setup. Using this allows for the consistent log format across multiple programs, which is very convenient when using microservice architecture. Usage is quite simple, with `useful.logs.setup` requiring only a single call, presumably from the `main` script, for example

```python
import logging
import useful.logs

useful.logs.setup()
_log = logging.getLogger(__name__)


if __name__ == '__main__':
    _log.info("testing", extra={"app": "AppName", "metric": 1.2})
```

Now every other part of the program called from the `main` script uses logging without any
knowledge of log format. An example would be

```python
import logging

_log = logging.getLogger("test")


def test():
    _log.debug("log message", extra={"app": "AppName", "metric": 1.2})
```

When argument `extra` is provided with `JSON` logging enabled, all of the values provided are logged together with timestamps and log message in a `JSON` log.

With this approach you can even have some level of control over log format from other Python modules you do not maintain yourself.

***

## useful-creator

A part of the `useful` Python modules collection dedicated to creating object instances from a configuration dictionary. Working with dictionaries instead of `JSON` or `Yaml` allows us to decouple from handling/parsing configuration files. The general idea is

```python
creator = Creator(...)
configuration = {...}
obj = creator.create(configuration)
```

where `Creator` is an implementation of the `useful.creator.BaseCreator` class. At the moment, provided implementations are:

* `RegistryCreator`
* `GenericCreator`
* `ShorthandCreator`

***

### `RegistryCreator`

`RegistryCreator(registry)` implementation requires a `registry` object that provides a mapping from string values to class objects ready to be instantiated, i.e. `cls = registry[key]`. `registry` argument can be a simple Python `dict`. This way, we have to register every class implementation we want to allow to be created from a config dictionary. This also gives us the freedom to use simpler names in configuration files, for example:

```python
from useful.creator import RegistryCreator

import example


class SomeExample:
    def __init__(self, argument):
        self.argument = argument

    def test(self):
        print("SomeExample:", self.argument)


configuration = {
    "Example": {
        "argument": 1
    }
}

registry = {}
registry["Another"] = example.AnotherExample
registry["Example"] = SomeExample

creator = RegistryCreator(registry)
obj = creator.create(configuration)
obj.test()
```

which would output

```python
SomeExample: 1
````

Using RegistryCreator allows us to simply use names `Example` or `Another` in configuration dictionaries. In general, the configuration format is

```json
{
    str: dict
}
```

Here is another example configuration

```json
{
    "name": {
        "param": "eters",
        "other": 123
    }
}
```

where `name` is interpreted as a key in the registry, and the dictionary value under that key is unpacked (`**kwargs`). The end result is basically

```python
cls = registry["name"]
obj = cls(param="eters", other=123)
```

### `GenericCreator`

This implementation requires a more verbose configuration, but doesn't need a prior registration of classes. Here is a simple usage example

```python
from useful.creator import GenericCreator

configuration = {
    "class": {
        "name": "ClassName",
        "module": "class.module"
    },
    "params": {
        "param": "eters",
        "other": 123
    }
}

creator = GenericCreator()
obj = creator.create(configuration)
```

which would basically execute

```python
obj = class.module.ClassName(param="eters", other=123)
```

### `ShorthandCreator`

A shorthand instance creator. Dictionaries of shape

```python
{
    "class.module.ClassName": {
        "param": "eters",
        "other": 123
    }
}
```

can be parsed and instances of `class.module.ClassName` created. This creator also implements internal cache to take advantage of input configs with multiple occuring references. For example, in case we have input config

```python
configuration = {
    "class.module.ClassName": {
        "param": "eters",
        "other": 123
    }
}

config = {
    "first": configuration,
    "second": configuration
}
```

the `ShorthandCreator` will return a dictionary

```python
{
    "first": instance_from_configuration,
    "second": instance_from_configuration
}
```

where instance is created only once, and afterwards simply a reference is used, the same way it happens in the input config. On the other hand, if we have

```python
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
```

the `ShorthandCreator` will return a dictionary

```python
{
    "first": instance_1_from_configuration,
    "second": instance_2_from_configuration
}
```

where `instance_1_from_configuration` and `instance_2_from_configuration` are separate instances of the same class.

Below is a minimal working example

```python
from useful.creator import ShorthandCreator


configuration = {
    "class.module.ClassName": {
        "param": "eters",
        "other": 123
    }
}

creator = ShorthandCreator()
obj = creator.create(configuration)
```

which would basically execute

```python
obj = class.module.ClassName(param="eters", other=123)
```

**Note.** When working with objects from the main file, you can use `__main__.ClassName`

***

## useful-resource

The purpose of function `useful.resource.load` is to provide unified access and parsing for resources on various locations. The usage is extremely simple:

```python
import useful.resource

config = useful.resource.load('s3://bucket/config.yaml')
```

We achieve this unified access in multiple stages:

### 0. Cache

`useful.resource.load` provides an implementation of config caching. This means that you can call `useful.resource.load(uri)` twice in a row, and the second call can simply use cached version from the first call. The behaviour options can be modified either by providing an aditional argument `timeout` to `useful.resource.load`, or by changing the `useful.resource.DEFAULT_TIMEOUT` value which is a value used in case `timeout` argument is not provided when calling `useful.resource.load`. We differentiate three separate cases:

1. `timeout < 0` - Do not use caching. This is the default behaviour.
2. `timeout = 0` - Use caching. On every `useful.resource.load(uri)` call check if the content at `uri` changed (Check out step 3 for more details).
3. `timeout > 0` - Use caching. If less time than `timeout` passed between two calls of `useful.resource.load` on the same `uri`, don't even check if the content on the `uri` has changed or not. Simply return the cached value immediately. This options exists to prevent constant access to files in case `useful.resource.load` gets called often on the same `uri`. A good example would be an API where you dynamically load resources when handling the request.

### 1. Scheme and format extraction

The only information we must have before we start is an URI for an object we want to access. Using URI `<schema>://<string>.<extension>` we can easily extract schema/protocol and format/extension.

### 2. Accessing and reading the resource

In this step, depending on the schema, we provide a `Reader` object that implements method `Reader.open()`. This provides a file-like object and allows us to read data byte by byte, in the same way as built-in function `open()` does for local files. Currently we support multiple schemas

* `s3://` - AWS S3 storage
* `gs://` - Google Cloud Storage
* `file://` - local storage
* `<no schema>` - local storage

but more can be easily added by editing `useful.resource.readers.readers` dictionary, a schema to reader implementation mapping. `useful.resource.load` function implements result caching with invalidation based on file changes. That is the reason we also implement method `Reader.hash()` which is also used to calculate object checksum without reading/downloading the whole resource. See step (4) for more details.

### 3. Parsing the actual data

From step (2) we have a file-like object and now we want to parse the data inside. In the step (1) we extracted the format/extension and now we can use a `Parser` object to actually parse the data. At the moment we only support:

* `.json` - JSON format
* `.yaml` - YAML format
* `.yml` - YAML format
* `.pkl` - Python pickle format
* `<anything else>` - raw binary data

but more can be easily added by editing `useful.resource.parsers.parsers` dictionary, an extension to parser implementation mapping.

### 4. [Optional] hook

Let's say we wanted to initialize our object `Model` with pretrained weights stored in a file `s3://bucket/weights.json`. Both downloading the weights and loading them into the program are slow because we are working with large models. This is why we need to avoid downloading the resource again if we can. We do this by checking the return value after calling `Reader.hash()`. Since we also want to avoid frequent loading of weights into our model, we want to cache the `Model` instance itself, instead of raw weights resource. This is where `hook` comes in. `hook` is an optional argument for the function `useful.resource.load`. It is a `callable` that accepts the output from the step (3) and runs additional modification and/or creation of objects instances. In our example, we would simply run

```python
model = useful.resource.load('s3://bucket/weights.json', hook=Model)
```

***

## useful-config

Simple functions for config parsing and validation. The main idea is to provide a simple and powerful way to load configuration files. The simplest option is to use

```python
from useful.config import from_url

config = from_url("path/to/config.yml")
```

Besides `useful.config.from_url`, you can also use `useful.config.from_dict` to work directly with already loaded config `dict` and `useful.config.from_env` to load the URL from environment variable. Function `useful.config.load` is implemented to use `useful.config.from_dict` when `dict` argument is provided, `useful.config.from_env` when environment variable name for variable containing resource url is provided and `useful.config.from_url` when resource url string is provided directly.

Each of those functions accepts an additional argument `validator` - a callable which will get called on the loaded config `dict`. If there are no exceptions, the config is deemed valid. It is important to note that, when using default value of `None`, we use the `useful.creator.ShorthandCreator` instance as a validator - where any parseable config is deemed valid. This means that this way of using it will implicitly call the `useful.creator.ShorthandCreator` instance on the input config and create instances if specified in the configuration.

An object returned from `useful.config.from_env` (and other config functions) is a [`Munch`](https://github.com/Infinidat/munch) instance, which allows for a more "human-readable" access to config data, i.e. `config.key` instead of `config["key"]` - but both options work.

### production - good practices

Our experience is that when working with production services `useful.config.from_env` is a way to go for ease of configuration. You simply need to specify which environment variable to use. When working with production services validation is very important and to solve this issue we tend to use [`voluptuous`](https://github.com/alecthomas/voluptuous). Example usage would be a program containing two files, `config.py` and `main.py`, for example

> `config.py`

```python
from voluptuous import Schema

environment_variable = "USEFUL_CONFIG"

schema = Schema({
    "test": int
})
```

and

> `main.py`

```python
import useful.config
from config import environment_variable, schema


if __name__ == "__main__":
    config = useful.config.from_env(environment_variable, schema)
```

Since an object returned from `useful.config.from_env` is a [`Munch`](https://github.com/Infinidat/munch) instance, we can simply access `config.test` for the config above. You can run the program above by executing

```bash
USEFUL_CONFIG=/useful/config.yaml python3 -m main
```

where file `/useful/config.yaml` contains

```yaml
test: 456
```

This provides a simple and unified way to configure multiple microservices.

### YAML config examples

#### using YAML anchors and aliases to refer objects

With configuration file `config.yml` containing

> `config.yml`

```yaml
first: &instance
    class.module.ClassName:
        param: eters
        other: 123
second: *instance
```

and running `main.py`

> `main.py`

```python
from useful.config import load

config = load("config.yml")

# this will print True
print(id(config["first"]) == id(config["second"]))
```

`True` will be printed to `stdout`.

#### creating multiple instances using the same configuration

With configuration file `config.yml` containing

> `config.yml`

```yaml
first:
    class.module.ClassName:
        param: eters
        other: 123
second:
    class.module.ClassName:
        param: eters
        other: 123
```

and running `main.py`

> `main.py`

```python
from useful.config import load

config = load("config.yml")

# this will print False
print(id(config["first"]) == id(config["second"]))
```

`False` will be printed to `stdout`.
