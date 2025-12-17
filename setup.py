#!/usr/bin/env python
import os
from setuptools import setup, find_packages

requirements = [
    "sqlalchemy",
]
with open("requirements_test.txt","r") as f:
    for line in f:
        line = line.strip()
        # Skip empty lines and lines that reference other files
        if not line or line.startswith("-") or ".txt" in line:
            continue
        # Strip inline comments but keep the requirement
        if "#" in line:
            line = line.split("#")[0].strip()
        if line:
            requirements.append(line)

with open("version", "r") as f:
    __version__ = f.read()

setup(
    author="Matthew Flamm",
    name="pytest-homeassistant-custom-component",
    version=__version__,
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    python_requires=">=3.13",
    install_requires=requirements,
    license="MIT license",
    url="https://github.com/MatthewFlamm/pytest-homeassistant-custom-component",
    author_email="matthewflamm0@gmail.com",
    description="Experimental package to automatically extract test plugins for Home Assistant custom components",
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Framework :: Pytest",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3.13",
        "Topic :: Software Development :: Testing",
    ],
    entry_points={"pytest11": ["homeassistant = pytest_homeassistant_custom_component.plugins"]},
)
