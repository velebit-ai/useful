# useful

## description

This repo contains a collection of solutions to often ocurring problems. We deal with unified way to setup and standardize logs, along with a way to simply load both local and remote configuration files and other resources.

The submodules currently included are:

* [useful.config](useful-config.md) - Easily handle configuration files, no matter where they are
* [useful.creator](useful-creator.md) - Create objects directly from config files
* useful.decorators - `@retry`, `@timing`, ...
* useful.dictionary - Useful functions for manipulating Python dictionaries
* useful.modules - Check if module exists/is installed, import module from string name, etc.
* [useful.resource](useful-resource.md) - Single interface to download and parse a resource from multiple locations
* useful.time - Extension to Python's incomplete datetime ISO format support
* useful.version - dummy module, only contains the general package version

## installation

You can find the module on [`pypi`](https://pypi.org/project/velebit-useful) and install it and **all** of the dependencies using

```sh
pip install velebit-useful[all]
```

For more details and options like installing only required dependencies check out [install.md](install.md)
