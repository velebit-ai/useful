# useful

This repo contains a collection of solutions to often ocurring problems. We deal with unified way to setup and standardize logs, along with a way to simply load both local and remote configuration files and other resources.

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

### 1. Scheme and format extraction

The only information we must have before we start is an URI for an object we want to access. Using URI `<scheme>://<string>.<extension>` we can easily extract scheme/protocol and format/extension.

### 2. Downloading the resource

In this step, depending on the scheme, we provide a `downloader` function that returns a file-like object and allows us to read data byte by byte, in the same way as built-in function `open()` does for local files. Currently we support multiple schemas

* `file://` - local storage - using built-in `open()` (on-demand)
* `<no scheme>` - local storage - using built-in `open()` (on-demand)
* `http://` - HTTP resource - in-memory download beforehand
* `https://` - HTTPS resource - in-memory download beforehand
* `ssh://` - SSH/SFTP - save the whole object in-memory beforehand
* `scp://` - SSH/SFTP - save the whole object in-memory beforehand
* `sftp://` - SSH/SFTP - save the whole object in-memory beforehand
* `s3://` - AWS S3 storage - save the whole object in-memory beforehand
* `s3fs://` - AWS S3 storage - read the object on-demand
* `gs://` - Google Cloud Storage - save the whole object in-memory beforehand
* `gsfs://` - Google Cloud Storage - read the object on-demand

but more can be easily added by using `useful.resource.downloaders.add_downloader` function.

### 3. Parsing the actual bytes

From step (2) we have a file-like object and now we want to parse the data inside. In the step (1) we extracted the format/extension and now we can use a `parser` function to actually parse the data. At the moment we only support:

* `.json` - JSON format
* `.yaml` - YAML format
* `.csv` - CSV format
* `.text` - plain text format
* `.yml` - YAML format
* `.pkl` - Python pickle format
* `.pickle` - Python pickle format
* `<anything else>` - raw binary data

but more can be easily added by using `useful.resource.parsers.add_parser` function.

### 4. [Optional] hook

`hook` is an optional argument for the function `useful.resource.load`. It is a `callable` that accepts the output from the step (3) and runs additional modification and/or creation of objects instances. For example, we could simply run

```python
model = useful.resource.load('s3://bucket/weights.json', hook=Model)
```

instead of running

```python
weights = useful.resource.load('s3://bucket/weights.json')
model = Model(weights)
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

environment_variable = "EXAMPLE_CONFIG"

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
EXAMPLE_CONFIG=/useful/config.yaml python3 -m main
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
