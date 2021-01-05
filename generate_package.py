#! /usr/bin/env python

import pathlib
import shutil
import os

TMP_DIR = "tmp_dir"
PACKAGE_DIR = "pytest_homeassistant_custom_component"
REQUIREMENTS_FILE = "requirements_test.txt"
CONST_FILE = "const.py"

REQUIREMENTS_FILE_DEV = "requirements_dev.txt"

path = "."
clone = "git clone --depth=1 https://github.com/home-assistant/core.git tmp_dir"
diff = "git diff --exit-code"

files = [
    "__init__.py",
    "common.py",
    "conftest.py",
    "ignore_uncaught_exceptions.py",
]

# remove rrquirements for development only, i.e not related to homeassistant tests
requirements_remove = [
    "codecov",
    "mypy",
    "pre-commit",
    "pylint",
    "astroid",
]

if os.path.isdir(TMP_DIR):
    shutil.rmtree(TMP_DIR)
if os.path.isdir(PACKAGE_DIR):
    shutil.rmtree(PACKAGE_DIR)
if os.path.isfile(REQUIREMENTS_FILE):
    os.remove(REQUIREMENTS_FILE)

os.system(clone)  # Cloning
os.mkdir(PACKAGE_DIR)
os.mkdir(os.path.join(PACKAGE_DIR, "test_util"))
shutil.copy2(os.path.join(TMP_DIR, REQUIREMENTS_FILE), REQUIREMENTS_FILE)
shutil.copy2(
    os.path.join(TMP_DIR, "homeassistant", CONST_FILE),
    os.path.join(PACKAGE_DIR, CONST_FILE),
)
shutil.copy2(
    os.path.join(TMP_DIR, "tests", "test_util", "aiohttp.py"),
    os.path.join(PACKAGE_DIR, "test_util", "aiohttp.py"),
)
shutil.copy2(
    os.path.join(TMP_DIR, "tests", "test_util", "__init__.py"),
    os.path.join(PACKAGE_DIR, "test_util", "__init__.py"),
)

for f in files:
    shutil.copy2(os.path.join(TMP_DIR, "tests", f), os.path.join(PACKAGE_DIR, f))

    filename = os.path.join(PACKAGE_DIR, f)

    with open(filename, "r") as file:
        filedata = file.read()

    filedata = filedata.replace("tests.", ".")

    with open(filename, "w") as file:
        file.write(filedata)

shutil.rmtree(TMP_DIR)
os.rename(
    os.path.join(PACKAGE_DIR, "conftest.py"), os.path.join(PACKAGE_DIR, "plugins.py")
)

with open(os.path.join(PACKAGE_DIR, CONST_FILE), "r") as original_file:
    data = original_file.readlines()
with open(os.path.join(PACKAGE_DIR, CONST_FILE), "w") as new_file:
    new_file.write("".join(data[0:6]))

added_text = "This file is originally from homeassistant/core and modified by pytest-homeassistant-custom-component.\n"
triple_quote = '"""\n'

for f in pathlib.Path(PACKAGE_DIR).rglob("*.py"):
    with open(f, "r") as original_file:
        data = original_file.readlines()
    old_docstring = data[0][3:][:-4]
    new_docstring = f"{triple_quote}{old_docstring}\n\n{added_text}{triple_quote}"
    body = "".join(data[1:])
    with open(f, "w") as new_file:
        new_file.write("".join([new_docstring, body]))

added_text = "# This file is from homeassistant/core.\n"

with open(REQUIREMENTS_FILE, "r") as original_file:
    data = original_file.readlines()

new_data = []
removed_data = []
for d in data:
    if "==" not in d:
        new_data.append(d)
    elif d.split("==")[0] not in requirements_remove:
        new_data.append(d)
    else:
        removed_data.append(d)

new_data.insert(0, added_text)

with open(REQUIREMENTS_FILE, "w") as new_file:
    new_file.writelines(new_data)

with open(REQUIREMENTS_FILE_DEV, "w") as new_file:
    new_file.writelines(removed_data)

diff_files = os.system(diff)

from pytest_homeassistant_custom_component.const import __version__

with open("README.md", "r") as original_file:
    data = original_file.readlines()

data[
    2
] = f"![HA core version](https://img.shields.io/static/v1?label=HA+core+version&message={__version__}&labelColor=blue)\n"

with open("README.md", "w") as new_file:
    new_file.write("".join(data))

print(f"Version: {__version__}")
