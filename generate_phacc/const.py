"""Constants for phacc."""
TMP_DIR = "tmp_dir"
PACKAGE_DIR = "pytest_homeassistant_custom_component"
REQUIREMENTS_FILE = "requirements_test.txt"
CONST_FILE = "const.py"

REQUIREMENTS_FILE_DEV = "requirements_dev.txt"

path = "."
clone = "git clone https://github.com/home-assistant/core.git tmp_dir"
diff = "git diff --exit-code"

files = [
    "__init__.py",
    "common.py",
    "conftest.py",
    "ignore_uncaught_exceptions.py",
    "components/recorder/common.py",
]

# remove requirements for development only, i.e not related to homeassistant tests
requirements_remove = [
    "codecov",
    "mypy",
    "pre-commit",
    "pylint",
    "astroid",
]

LICENSE_FILE_HA = "LICENSE.md"
LICENSE_FILE_NEW = "LICENSE_HA_CORE.md"

HA_VERSION_FILE = "ha_version"
