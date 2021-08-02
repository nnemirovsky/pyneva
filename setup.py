from setuptools import find_packages, setup
import os

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

here = os.path.abspath(os.path.dirname(__file__))
init_path = os.path.join(here, 'pyneva', '__init__.py')
with open(init_path, 'r', encoding='utf-8') as f:
    for line in f.read().splitlines():
        if line.startswith('__version__'):
            delim = '"' if '"' in line else "'"
            __version__ = line.split(delim)[1]

setup(
    name="pyneva",
    version=__version__,
    description="Custom library for electricity meters Neva MT",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Nikita Nemirovsky",
    author_email="vaze.legend@gmail.com",
    url="https://github.com/vazelegend/pyneva",
    license="MIT",
    packages=find_packages(include=("pyneva",)),
    install_requires=["pyserial>=3.5"],
    python_requires=">=3.9",
    platforms="any",
)
