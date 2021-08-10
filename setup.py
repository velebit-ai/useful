from setuptools import setup


def merge_extras_reqs(extras_requirements, pattern):
    """
    Merge extras requirements dictionary keys if they start with string
    `pattern`.

    Args:
        extras_requirements ({str: [str]}): A dictionary containing extras
            names and its requirements list.
        pattern (str): Pattern to use for selecting keys to merge.

    Returns:
        list: A list of strings representing merged requirements from all of
            the extras groups matching the pattern.
    """
    requirements = []
    for key in extras_requirements:
        if key.startswith(pattern):
            requirements.extend(extras_requirements[key])

    return list(set(requirements))


def read_requirements(*paths):
    """
    Open multiple requirements.txt files and concatenate results into a single
    requirements list without repeats.

    Args:
        paths ([str]): A list of requirements file paths

    Returns:
        list: A list of requirements from all of the files
    """
    reqs = []
    for path in paths:
        with open(path, 'r') as f:
            nth_reqs = f.read().splitlines()
            reqs.extend(nth_reqs)

    return list(set(reqs))


# load package version
exec(open("useful/version/version.py").read())

# load minimal requirements
requirements = []

# load "atomic" extras requirements
extras_requirements = {
    "config": read_requirements("requirements/extras/config.txt"),
    "resource-downloader-gs": read_requirements("requirements/extras/resource-downloader-gs.txt"),  # noqa
    "resource-downloader-gsfs": read_requirements("requirements/extras/resource-downloader-gsfs.txt"),  # noqa
    "resource-downloader-s3": read_requirements("requirements/extras/resource-downloader-s3.txt"),  # noqa
    "resource-downloader-s3fs": read_requirements("requirements/extras/resource-downloader-s3fs.txt"),  # noqa
    "resource-downloader-ssh": read_requirements("requirements/extras/resource-downloader-ssh.txt"),  # noqa
    "resource-parser-yaml": read_requirements("requirements/extras/resource-parser-yaml.txt"),  # noqa
    "resource-parser-numpy": read_requirements("requirements/extras/resource-parser-numpy.txt"),  # noqa
}

# create artifical groupings for easier install on user-side
extras_groups = {}
extras_groups["resource-downloader-all"] = merge_extras_reqs(extras_requirements, pattern="resource-downloader")  # noqa
extras_groups["resource-parser-all"] = merge_extras_reqs(extras_requirements, pattern="resource-parser")  # noqa
extras_groups["resource-all"] = merge_extras_reqs(extras_requirements, pattern="resource")  # noqa
extras_groups["all"] = merge_extras_reqs(extras_requirements, pattern="")

# add to extras_requirements
extras_requirements.update(extras_groups)

setup(
    name="useful",
    version=__version__,  # noqa
    description="A collection of somewhat useful modules solving repetitive "
                "problems",
    classifiers=[
        "License :: OSI Approved :: MIT License",

        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6"
        "Programming Language :: Python :: 3.7"
        "Programming Language :: Python :: 3.8"
    ],
    url="https://github.com/velebit-ai/useful",
    author="Velebit AI",
    author_email="dev@velebit.ai",
    packages=[
        "useful.config",
        "useful.creator",
        "useful.decorators",
        "useful.dictionary",
        "useful.modules",
        "useful.resource",
        "useful.time",
        "useful.version",
    ],
    install_requires=requirements,
    extras_require=extras_requirements,
    include_package_data=True
)
