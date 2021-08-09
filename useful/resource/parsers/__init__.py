from useful.resource.parsers._parsers import add_parser  # noqa
from useful.resource.parsers._parsers import remove_parser  # noqa
from useful.resource.parsers._parsers import get_parser  # noqa
from useful.resource.parsers._parsers import parsers  # noqa

from useful.modules import installed

# add optional parsers if dependencies are installed
if installed("ruamel.yaml"):
    from useful.resource.parsers import yaml  # noqa

if installed("numpy"):
    from useful.resource.parsers import numpy  # noqa

del installed
