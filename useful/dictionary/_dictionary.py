import logging

_log = logging.getLogger(__name__)


def clean_dict(dictionary):
    """
    Filter out keys with values equal to None.

    Args:
        dictionary (dict): A dictionary to clean.

    Returns:
        dict: Cleaned input dictionary.
    """
    _log.debug("Cleaning the dictionary")
    return {k: v for k, v in dictionary.items() if v is not None}
