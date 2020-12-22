# pytest-homeassistant-custom-component

![HA core version](https://img.shields.io/static/v1?label=HA+core+version&message=2021.1.0.dev0&labelColor=blue)

Package to automatically extract testing plugins from Home Assistant for custom component testing.
Automatic extraction of testing plugins and helpers.
The goal is to provide the same functionality as the tests in home-assistant/core.

* For now, the package will be updated _approximately_ weekly.
* Version of home-assistant/core is given in `pytest_homeassistant_custom_component.const` and in the README above

Usage:
* All pytest fixtures can be used as normal, like `hass`
* For helpers:
  * home-assistant/core native test: `from tests.common import MockConfigEntry`
  * custom component test: `from pytest_homeassistant_custom_component.common import MockConfigEntry`
* If your integration is inside a `custom_components` folder, a `custom_components/__init__.py` file or changes to `sys.path` may be required.
* See [list of custom components](https://github.com/MatthewFlamm/pytest-homeassistant-custom-component/network/dependents) as examples that use this package.
* Also see tests for `simple_integration` in this repository.

This repository is set up to be nearly automatic with the goal of being fully automatic.
To keep the releases up to date, a PR is automatically generated with new changes once a week.
After manually merging the PR, a second action is manually run to bump the version, make a release, and upload to PyPI.

This package was inspired by [pytest-homeassistant](https://github.com/boralyl/pytest-homeassistant) by @boralyl, but is intended to more closely and automatically track the home-assistant/core library.
