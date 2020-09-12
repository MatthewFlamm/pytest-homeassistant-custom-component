#!/usr/bin/env python
import os
from setuptools import setup, find_packages

requirements = [
    "homeassistant",
    "sqlalchemy",
]
with open("requirements_test.txt","r") as f:
    for line in f:
        if "txt" not in line and "#" not in line:
            requirements.append(line)

setup(
    author="Matthew Flamm",
    name="pytest-homeassistant-custom-component",
    version="0.0.7",
    packages=find_packages(),
    python_requires=">=3.7.1",
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
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Topic :: Software Development :: Testing",
    ],
    entry_points={"pytest11": ["homeassistant = pytest_homeassistant_custom_component.plugins"]},
)
