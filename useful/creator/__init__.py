from useful.creator._creators import BaseCreator, RegistryCreator  # noqa
from useful.creator._creators import GenericCreator, ShorthandCreator  # noqa
from useful.creator._creators import ShorthandCreatorWithCache, get_object  # noqa

generic_creator = GenericCreator()
shorthand_creator = ShorthandCreator()
shorthand_creator_with_cache = ShorthandCreatorWithCache()
