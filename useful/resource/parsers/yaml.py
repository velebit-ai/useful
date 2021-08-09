import ruamel.yaml

from useful.resource.parsers._parsers import add_parser

add_parser("application/yaml", ruamel.yaml.safe_load, ".yml", ".yaml")
