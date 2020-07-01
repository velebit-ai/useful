import os

from munch import munchify

import useful.resource
from useful.creator import shorthand_creator_with_cache


def get_hook(validator=None):
    """
    Get useful.resource.load compatible hook validating input dictionary and
    creating a Munch object.

    Args:
        validator (Callable): Callable to use for validation

    Returns:
        function: A function for validating and converting dictionary to Munch
    """
    if validator is None:
        validator = shorthand_creator_with_cache

    def hook(dictionary):
        """
        Validate and munchify input dictionary.

        Args:
            dictionary (dict): Input to validate and munchify.

        Returns:
            Munch: Validated output.
        """
        return munchify(validator(dictionary))
    return hook


def from_dict(dictionary, validator=None):
    """
    Validate and munchify dictionary using custom validator.

    Args:
        dictionary (dict): Input dictionary
        validator (Callable): Callable to use for validation

    Returns:
        Munch: Validated output.
    """
    return get_hook(validator)(dictionary)


def from_url(url, validator=None):
    """
    Validate and munchify dictionary loaded from url.

    Args:
        url (str): Resource URL containing dictionary.
        validator (Callable): Callable to use for validation

    Returns:
        Munch: Validated output.
    """
    hook = get_hook(validator)
    return useful.resource.load(url, hook=hook)


def from_env(environment_variable, validator=None):
    """
    Validate and munchify dictionary loaded from url saved in an environment
    variable with the name `environment_variable`.

    Args:
        environment_variable (str): Environment variable name containing
            URL to the resource containing a dictionary
        validator (Callable): Callable to use for validation

    Returns:
        Munch: Validated output.
    """
    assert environment_variable in os.environ
    url = os.environ[environment_variable]
    return from_url(url, validator)
