from setuptools import find_packages, setup

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="pyneva",
    version="0.1.0",
    description="Custom library for electricity meters Neva MT 3xx",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Nikita Nemirovsky",
    author_email="vaze.legend@gmail.com",
    url="https://github.com/vazelegend/pyneva",
    license="MIT",
    package_dir={"": "src"},
    packages=find_packages("src"),
    install_requires=["pyserial"],
    python_requires=">=3.6",
    # setup_requires=["pytest-runner"],
    # tests_require=["pytest==6.2.4"],
    # test_suite="tests",
)