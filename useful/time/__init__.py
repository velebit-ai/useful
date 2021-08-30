import logging
import re
import datetime

_log = logging.getLogger(__name__)


def string_to_datetime(dt_str):
    """
    Convert an ISO 8601 compatible string to datetime.datetime. Convert into
    UTC timezone and then convert to offset-naive for simplicity.

    Note. Python doesn't natively support UTC timezone specified by Z. We add
        support for this.

    Args:
        dt_str (string): ISO 8601 compatible string

    Returns:
        datetime.datetime: An instance created from input string
    """
    _log.debug("Replacing Z with +00:00, if it exists")
    dt_str = dt_str.replace('Z', '+00:00')
    # Add support for "2020-06-02T00:31:57+0000" (HHSS) format by converting it
    # into python ISO format "2020-06-02T00:31:57+00:00" (HH:SS)
    _log.debug("Replacing +HHSS with +HH:SS, if it exists")
    dt_str = re.sub(r"\+([0-9][0-9])([0-9][0-9])$", "+\g<1>:\g<2>", dt_str)  # noqa
    _log.debug(f"Read date from iso format: {dt_str}")
    dt = datetime.datetime.fromisoformat(dt_str)
    _log.debug("Convert to UTC timezone")
    dt_utc = dt.astimezone(datetime.timezone.utc)
    _log.debug("Remove timezone info")
    dt_naive = dt_utc.replace(tzinfo=None)
    return dt_naive


def datetime_to_string(dt, Z=False):
    """
    Convert datetime.datetime object into a ISO 8601 compatible string. Treat
    as offset-naive, which is interpreted as UTC.

    Note. Python doesn't natively support UTC timezone specified by Z. We add
        support for this.

    Args:
        dt (datetime.datetime): Input datetime object
        Z (bool): A flag indicating whether or not to replce +00:00 with Z

    Returns:
        string: ISO 8601 compatible string with seconds precisions.
    """
    dt_utc = dt
    if dt_utc.tzinfo is None:
        _log.debug("Pretending input date is UTC: insert UTC as timezone info")
        dt_utc = dt_utc.replace(tzinfo=datetime.timezone.utc)

    _log.debug("Converting to ISO format string")
    dt_utc = dt_utc.isoformat(timespec='seconds')

    if Z is True:
        _log.debug("Replacing +00:00 with Z, if it exists")
        dt_utc = dt_utc.replace('+00:00', 'Z')

    return dt_utc
