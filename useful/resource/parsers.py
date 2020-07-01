import json
import logging
import pickle
import time

import ruamel.yaml

from useful.resource import mimetypes

_log = logging.getLogger(__name__)


class Parser:
    def __init__(self, reader):
        """
        Abstract Parser class providing the parser interface, a single
        Parser.parse() method.

        Args:
            reader (useful.resource.Reader): A Reader instance
                to use for reading data when parsing.
        """
        self.reader = reader

    def parse(self, parse_method):
        """
        Read through resource and call parse_method on the file object.

        Args:
            parse_method (function): function to call on file-like object
                provided by the Reader.open method.

        Returns:
            object: Parsed data
        """
        with self.reader.open("rb") as f:
            _log.debug(f"Started reading '{self.reader.url.url}'",
                       extra={"url": self.reader.url.url})
            start_time = time.time()
            data = parse_method(f)
            end_time = time.time()
            _log.debug(f"Finished reading '{self.reader.url.url}'",
                       extra={"url": self.reader.url.url,
                              "reading_time": end_time - start_time})
        return data


class JSON(Parser):
    def __init__(self, reader):
        """
        A class for parsing JSON resources.

        Args:
            reader (useful.resource.Reader): A Reader instance
                to use for reading data when parsing.

        Raises:
            AssertionError: If mimetype is not "application/json"
        """
        assert reader.url.mimetype == "application/json"
        super().__init__(reader)

    def parse(self):
        return super().parse(json.load)


class YAML(Parser):
    def __init__(self, reader):
        """
        A class for parsing YAML resources using.

        Args:
            reader (useful.resource.Reader): A Reader instance
                to use for reading data when parsing.

        Raises:
            AssertionError: If mimetype is not "application/yaml"
        """
        assert reader.url.mimetype == "application/yaml"
        super().__init__(reader)
        self.yaml = ruamel.yaml.YAML()

    def parse(self):
        return super().parse(self.yaml.load)


class Pickle(Parser):
    def __init__(self, reader):
        """
        A class for parsing pickle resources.

        Args:
            reader (useful.resource.Reader): A Reader instance
                to use for reading data when parsing.

        Raises:
            AssertionError: If mimetype is not "application/pickle"
        """
        assert reader.url.mimetype == "application/pickle"
        super().__init__(reader)

    def parse(self):
        return super().parse(pickle.load)


class Generic(Parser):
    def parse(self):
        return super().parse(lambda x: x.read())


# add custom yaml mime type
mimetypes.add_type("application/yaml", ".yaml")
mimetypes.add_type("application/yaml", ".yml")
# add custom pickle mime type
mimetypes.add_type("application/pickle", ".pkl")

# a simple dict of supported parsers
parsers = {
    "application/json": JSON,
    "application/yaml": YAML,
    "application/pickle": Pickle,
    None: Generic
}
