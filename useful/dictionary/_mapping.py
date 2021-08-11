"""
Convert multi-level dictionaries into mappings (single level dictionaries).
"""

DEFAULT_SEPARATOR = "."


def _concat_keys(keys, separator):
    """
    Concatenate non-empty strings in list `keys` using `separator` as a
    separator between them.

    Args:
        keys (list): A list of keys to concatenate
        separator (str): A separator to use between concatenated keys

    Returns:
        str: Concatenated keys
    """
    # convert key to strings in case some of the keys are numbers
    keys = map(lambda x: str(x), keys)
    # filter out empty strings
    keys = filter(lambda x: len(x) > 0, keys)
    return separator.join(keys)


def _dictionary_to_mapping(x, separator):
    """
    Convert a Python dict to a mapping. This works purely with dictionaries, so
    a main function `to_mapping` is used for converting generic objects and
    dictionaries containing non-dictionaries as values.

    Args:
        x (dict): A dictionary to convert into mapping
        separator (str): Separator to use when concatenating keys

    Returns:
        dict: Mapping containing all of the data from the input dictionary
    """
    assert isinstance(x, dict)
    mapping = {}
    # iterate through input dictionary
    for key, value in x.items():
        # convert every value inside x to a mapping
        value_mapping = to_mapping(value, separator)
        # insert converted mapping into "parent" mapping by concatenating keys
        for k, v in value_mapping.items():
            mapping[_concat_keys([key, k], separator)] = v
    return mapping


def _list_to_mapping(x, separator):
    """
    Convert a Python list to a mapping. This works purely with a list, so
    a main function `to_mapping` is used for converting generic objects and
    lists containing non-lists as values.

    Args:
        x (list): A list to convert into mapping
        separator (str): Separator to use when concatenating keys

    Returns:
        dict: Mapping containing all of the data from the input dictionary
    """
    assert isinstance(x, list)
    # create a dictionary with list indices used as keys and values converted
    # to mappings
    dictionary = {str(i): to_mapping(v, separator) for i, v in enumerate(x)}
    # convert newly created dictionary to a mapping
    return _dictionary_to_mapping(dictionary, separator)


def _anything_to_mapping(x, separator):
    """
    Convert `x` of any type to a dictionary `{"": x}`. This gives us a
    convention to pack (and unpack) values that are neither dicts nor lists to
    mappings.

    Args:
        x (object): Object to convert into mapping
        separator (str): Separator to use when concatenating keys. Unused in
            this function. Here only to comply with "to_mapping" functions
            prototype.

    Returns:
        dict: A dictionary `{"": x}`, where `x` is an input object
    """
    return {"": x}


def to_mapping(x, separator=DEFAULT_SEPARATOR, additional_functions=None):
    """
    Convert an object `x` to a mapping using `separator` when concatenating
    keys. Python dicts and lists are mapped a bit smarter, and everything else
    is mapped very simple using
                `useful.mapping._mapping._anything_to_mapping()`.
    A list of additional functions can be passed as an argument to provide
    custom functions for converting different types to mappings.

    Args:
        x (object): Input object to convert to mapping
        separator (str, optional): Separator to use when concatenating keys.
            Defaults to useful.mapping._mapping.DEFAULT_SEPARATOR
        additional_functions ([function], optional): A list of additional
            functions to use for converting objects. Defaults to None, which is
            interpreted as an empty list of additional functions.

    Returns:
        dict: A mapping containing all of the data from the input dictionary
    """
    if additional_functions is None:
        additional_functions = []

    # build a list of functions to use when converting to mappings
    functions = [
        *additional_functions,
        _dictionary_to_mapping,
        _list_to_mapping,
        _anything_to_mapping
    ]

    # find the first function that "knows" how to convert `x` to mapping
    for function in functions:
        try:
            # since `_anything_to_mapping` does not raise AssertionError in the
            # worst case it will get called and we will return that result.
            return function(x, separator)
        except AssertionError:
            pass


def _create_dict(*keys, value=None):
    """
    From `keys = [key_1, key_2, ..., key_n]` and `value = value` generate a
    dictionary

                        ```
                        {
                            key_1: {
                                key_2: {
                                    ...: {
                                        key_n: value
                                    }
                                }
                            }
                        }
                        ```

    Args:
        *keys (list): A list of keys to use for creating a dict
        value (object, optional): A value to use when creating a dict. Defaults
            to None.

    Returns:
        dict: A dictionary constructed from provided keys and value.
    """
    if len(keys) == 0:
        return value

    return {keys[0]: _create_dict(*keys[1:], value=value)}


def _merge_dicts(x, y):
    """
    Merge dictionary `y` into dictionary `x` recursively. When merging dicts

                            ```
                            x = {
                                "first": {
                                    "second": 2
                                }
                            }
                            ```

    and

                            ```
                            y = {
                                "first": {
                                    "third": 3
                                }
                            }
                            ```

    by calling `_merge_dicts(x, y)`, we expect the result

                            ```
                            {
                                "first": {
                                    "second": 2,
                                    "third": 3
                                }
                            }
                            ```

    instead of the usual result by merging only over first-level keys.

    Args:
        x (dict): A dictionary to merge into
        y (dict): A dictionary to merge from

    Returns:
        dict: Merged dictionary
    """
    # trivial case when x is None
    if x is None:
        return y

    # trivial case when y is None
    if y is None:
        return x

    # when neither x nor y are None, we expect dictionaries
    assert isinstance(x, dict)
    assert isinstance(y, dict)

    new = x.copy()
    # iterate through y and merge every key, value pair into x
    for key, value in y.items():
        new[key] = _merge_dicts(new.get(key), value)

    return new


def _convert_to_list(x):
    """
    Try to convert dict into a list. If `x` is not a dict, we do not know how
    to convert it so we return it. On the other hand, when `x` is a dict, we
    only want to convert dictionaries of form

                            ```
                            {
                                "0": value_0,
                                "1": value_1,
                                ...
                                "n", value_n
                            }
                            ```

    For every other dict form, only recursively convert values to lists and
    return the dict containing converted values.

    Args:
        x (object): An object to convert to list.

    Returns:
        object or list: Input object after applying all conversion methods
    """
    # we don't know how to work with non-dictionaries
    if not isinstance(x, dict):
        return x

    # recursively convert every value in x to a list
    y = {}
    for k, v in x.items():
        y[k] = _convert_to_list(v)

    # try to convert newly created dict y into list
    try:
        lst = []
        for index in range(len(y)):
            # if str(index) is not a key in y, KeyError is raised which means
            # we cannot convert this dictionary into a list
            lst.append(y[str(index)])
        return lst
    except KeyError:
        # return "unconverted" y with converted values only
        return y


def from_mapping(mapping, separator=DEFAULT_SEPARATOR):
    """
    Convert mapping into multi-level dictionaries by spliting keys using
    `separator` value.

    Args:
        mapping (dict): A single-level dictionary to convert into multi-level
            dictionary.
        separator (str, optional): The separator to use when splitting key.
            Defaults to useful.mapping._mapping.DEFAULT_SEPARATOR.

    Returns:
        object: Multi-level dictionary generated from input mapping.
    """
    x = {}
    for key, value in mapping.items():
        # parse key using separator
        keys = key.split(separator)
        # create a dictionary from keys list and value
        tmp = _create_dict(*keys, value=value)
        # merge newly created dictionary into x
        x = _merge_dicts(x, tmp)

    # if possible, (recursively) convert x to a list
    x = _convert_to_list(x)
    if isinstance(x, dict):
        # if x is still a dict and its shape is {"": value}, return only value
        if len(x.keys()) == 1 and "" in x:
            x = x[""]
    return x
