# useful

## description

This repo contains a collection of solutions to often ocurring problems. We deal with unified way to setup and standardize logs, along with a way to simply load both local and remote configuration files and other resources.

For more details check out the [docs](docs/docs.md).

## installation

You can find the module on [pypi.org](https://pypi.org/project/velebit-useful) and install it and **all** of the dependencies using

```sh
pip install velebit-useful[all]
```

For more details and options like installing only required dependencies check out [install.md](docs/install.md)

## velebit-useful-logs

Another useful submodule not included here is [`useful.logs`](https://github.com/velebit-ai/useful-logs). This sub-module contracted most feedback and usage, thus we decided to separate it into a completely separate package. Even though they share the same namespace `useful`, both packages are structured in such a way that they can be installed and used together, without any collisions.

If the need arises, other submodules can also be converted into separate packages.
