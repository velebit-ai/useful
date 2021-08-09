from useful.modules import depend

_config_deps = depend("munch", raise_on_fail=False)

if _config_deps.installed():
    from useful.config._config import from_dict, from_env, from_url  # noqa
    from useful.config._config import get_hook, load  # noqa
