import numpy as np

from useful.resource.parsers._parsers import add_parser

add_parser("application/numpy", np.load, ".npy", ".npz")
