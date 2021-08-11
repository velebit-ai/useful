from useful.modules import installed

if installed("munch"):
    from useful.config._config import from_dict, from_env, from_url  # noqa
    from useful.config._config import get_hook, load  # noqa
