import re
import setuptools

with open("README.md") as f:
    long_description = f.read()

with open("eepyc.py") as f:
    _source = f.read()
    version = re.search('__version__ = "(.*?)"', _source).group(1)
    author = re.search('__author__ = "(.*?)"', _source).group(1)

setuptools.setup(
    name="eepyc",
    version=version,
    author=author,
    author_email="justinyaodu@gmail.com",
    description="Evaluate embedded Python code in textual data",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/justinyaodu/eepyc",
    py_modules=["eepyc"],
    entry_points={'console_scripts': ['eepyc=eepyc:_main']},
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Environment :: Console",
        "Topic :: Text Processing :: Filters"
    ],
    python_requires='>=3.6'
)
