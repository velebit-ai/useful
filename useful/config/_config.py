import os

from munch import munchify
from voluptuous import Schema

import useful.resource


def get_hook(schema):
    """
    Get useful.resource.load compatible hook validating input dictionary and
    creating a Munch object.

    Args:
        schema (voluptuous.Schema): A config schema

    Returns:
        function: A function for validating and converting dictionary to Munch

    Raises:
        AssertionError: If schema is not an instance of voluptuous.Schema
    """
    assert isinstance(schema, Schema)

    def hook(dictionary):
        """
        Validate and munchify input dictionary.

        Args:
            dictionary (dict): Voluptuous validation and munchify input.

        Returns:
            Munch: Validated output.
        """
        return munchify(schema(dictionary))
    return hook


def from_dict(dictionary, schema):
    """
    Validate and munchify dictionary using schema.

    Args:
        dictionary (dict): Input dictionary
        schema (voluptuous.Schema): Voluptuous schema to use for validation

    Returns:
        Munch: Validated output.
    """
    return get_hook(schema)(dictionary)


def from_url(url, schema):
    """
    Validate and munchify dictionary loaded from url.

    Args:
        url (str): Resource URL containing dictionary.
        schema (voluptuous.Schema): Voluptuous schema to use for validation

    Returns:
        Munch: Validated output.
    """
    hook = get_hook(schema)
    return useful.resource.load(url, hook=hook)


def from_env(environment_variable, schema):
    """
    Validate and munchify dictionary loaded from url saved in an environment
    variable with the name `environment_variable`.

    Args:
        environment_variable (str): Environment variable name containing
            URL to the resource containing a dictionary
        schema (voluptuous.Schema): Voluptuous schema to use for validation

    Returns:
        Munch: Validated output.
    """
    assert environment_variable in os.environ
    url = os.environ[environment_variable]
    return from_url(url, schema)
