#! /usr/bin/env python

import shutil
import os

TMP_DIR = "tmp_dir"
PACKAGE_DIR = "pytest_homeassistant_custom_component"
REQUIREMENTS_FILE = "requirements_test.txt"

path  = "." 
clone = "git clone --depth=1 https://github.com/home-assistant/core.git tmp_dir"

files = [
    "__init__.py",
    "async_mock.py",
    "common.py",
    "conftest.py",
    "ignore_uncaught_exceptions.py",
]

if os.path.isdir(TMP_DIR):
    shutil.rmtree(TMP_DIR)
if os.path.isdir(PACKAGE_DIR):
    shutil.rmtree(PACKAGE_DIR)
if os.path.isfile(REQUIREMENTS_FILE):
    os.remove(REQUIREMENTS_FILE)

os.system(clone) # Cloning
os.mkdir(PACKAGE_DIR)
os.mkdir(os.path.join(PACKAGE_DIR, "test_util"))
shutil.copy2(os.path.join(TMP_DIR, REQUIREMENTS_FILE), REQUIREMENTS_FILE)
shutil.copy2(os.path.join(TMP_DIR, "tests", "test_util", "aiohttp.py"), os.path.join(PACKAGE_DIR, "test_util", "aiohttp.py"))
shutil.copy2(os.path.join(TMP_DIR, "tests", "test_util", "__init__.py"), os.path.join(PACKAGE_DIR, "test_util", "__init__.py"))

for f in files:
    shutil.copy2(os.path.join(TMP_DIR, "tests", f), os.path.join(PACKAGE_DIR, f))

    filename = os.path.join(PACKAGE_DIR, f)
    
    with open(filename, 'r') as file:
        filedata = file.read()

    filedata = filedata.replace("tests.", '.')

    with open(filename, 'w') as file:
        file.write(filedata)

shutil.rmtree(TMP_DIR)
os.rename(os.path.join(PACKAGE_DIR, "conftest.py"), os.path.join(PACKAGE_DIR, "plugins.py"))
