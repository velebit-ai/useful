# useful-config

Simple functions for config parsing and validation. Relies heavily on `useful.resource`. The main idea is to provide a simple and powerful way to load configuration files. The simplest option is to use

```python
from useful.config import from_url

config = from_url("path/to/config.yml")
```

Besides `useful.config.from_url`, you can also use `useful.config.from_dict` to work directly with already loaded config `dict` and `useful.config.from_env` to load the URL from environment variable. Function `useful.config.load` is implemented to use `useful.config.from_dict` when `dict` argument is provided, `useful.config.from_env` when environment variable name for variable containing resource url is provided and `useful.config.from_url` when resource url string is provided directly.

Each of those functions accepts an additional argument `validator` - a callable which will get called on the loaded config `dict`. If there are no exceptions, the config is deemed valid. It is important to note that, when using default value of `None`, we use the `useful.creator.ShorthandCreator` instance as a validator - where any parseable config is deemed valid. This means that this way of using it will implicitly call the `useful.creator.ShorthandCreator` instance on the input config and create instances if specified in the configuration.

An object returned from `useful.config.from_env` (and other config functions) is a [`Munch`](https://github.com/Infinidat/munch) instance, which allows for a more "human-readable" access to config data, i.e. `config.key` instead of `config["key"]` - but both options work.

## production - good practices

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

## YAML config examples

### using YAML anchors and aliases to refer objects

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

### creating multiple instances using the same configuration

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
