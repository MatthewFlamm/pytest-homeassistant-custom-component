#!/usr/bin/env python
import os
from setuptools import setup, find_packages

requirements = [
    "sqlalchemy",
]
with open("requirements_test.txt","r") as f:
    for line in f:
        if "txt" not in line and "#" not in line:
            requirements.append(line)

with open("version", "r") as f:
    __version__ = f.read()

setup(
    author="Matthew Flamm",
    name="pytest-homeassistant-custom-component",
    version=__version__,
    packages=find_packages(),
    python_requires=">=3.9",
    install_requires=requirements,
    license="MIT license",
    url="https://github.com/MatthewFlamm/pytest-homeassistant-custom-component",
    author_email="matthewflamm0@gmail.com",
    description="Experimental package to automatically extract test plugins for Home Assistant custom components",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Framework :: Pytest",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3.9",
        "Topic :: Software Development :: Testing",
    ],
    entry_points={"pytest11": ["homeassistant = pytest_homeassistant_custom_component.plugins"]},
)
