from setuptools import setup


def read_requirements(path):
    with open(path, 'r') as f:
        return f.read().splitlines()


# load package version
exec(open("useful/core/version.py").read())

# load minimal requirements
requirements = []

# load extras requirements
extras_requirements = {
    "config": read_requirements("requirements/extras/config.txt"),
    "resource-gs": read_requirements("requirements/extras/resource-gs.txt"),
    "resource-s3": read_requirements("requirements/extras/resource-s3.txt"),
    "resource-yaml": read_requirements("requirements/extras/resource-yaml.txt"),
}
extras_requirements["all"] = []
for reqs in extras_requirements.values():
    extras_requirements["all"].extend(reqs)

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
        "useful.core",
        "useful.creator",
        "useful.logs",
        "useful.modules",
        "useful.resource"
    ],
    install_requires=requirements,
    extras_require=extras_requirements,
    include_package_data=True
)
