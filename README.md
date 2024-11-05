# pytest-homeassistant-custom-component

![HA core version](https://img.shields.io/static/v1?label=HA+core+version&message=2024.11.0b5&labelColor=blue)

[![Open in Gitpod](https://gitpod.io/button/open-in-gitpod.svg)](https://gitpod.io/#https://github.com/MatthewFlamm/pytest-homeassistant-custom-component)

Package to automatically extract testing plugins from Home Assistant for custom component testing.
The goal is to provide the same functionality as the tests in home-assistant/core.
pytest-homeassistant-custom-component is updated daily according to the latest homeassistant release including beta.

## Usage:
* All pytest fixtures can be used as normal, like `hass`
* For helpers:
  * home-assistant/core native test: `from tests.common import MockConfigEntry`
  * custom component test: `from pytest_homeassistant_custom_component.common import MockConfigEntry`
* If your integration is inside a `custom_components` folder, a `custom_components/__init__.py` file or changes to `sys.path` may be required.
* `enable_custom_integrations` fixture is required (versions >=2021.6.0b0)
  * Some fixtures, e.g. `recorder_mock`, need to be initialized before `enable_custom_integrations`. See https://github.com/MatthewFlamm/pytest-homeassistant-custom-component/issues/132.
* pytest-asyncio might now require `asyncio_mode = auto` config, see #129.
* If using `load_fixture`, the files need to be in a `fixtures` folder colocated with the tests. For example, a test in `test_sensor.py` can load data from `some_data.json` using `load_fixture` from this structure:

```
tests/
   fixtures/
      some_data.json
   test_sensor.py
```

## Examples:
* See [list of custom components](https://github.com/MatthewFlamm/pytest-homeassistant-custom-component/network/dependents) as examples that use this package.
* Also see tests for `simple_integration` in this repository.
* Use [cookiecutter-homeassistant-custom-component](https://github.com/oncleben31/cookiecutter-homeassistant-custom-component) to create a custom component with tests by using [cookiecutter](https://github.com/cookiecutter/cookiecutter).
* The [github-custom-component-tutorial](https://github.com/boralyl/github-custom-component-tutorial) explaining in details how to create a custom componenent with a test suite using this package.

## More Info
This repository is set up to be nearly fully automatic.

* Version of home-assistant/core is given in `ha_version`, `pytest_homeassistant_custom_component.const`, and in the README above.
* This package is generated against published releases of homeassistant and updated daily.
* PRs should not include changes to the `pytest_homeassistant_custom_component` files.  CI testing will automatically generate the new files.

### Version Strategy
* When changes in extraction are required, there will be a change in the minor version.
* A change in the patch version indicates that it was an automatic update with a homeassistant version.
* This enables tracking back to which versions of pytest-homeassistant-custom-component can be used for
  extracting testing utilities from which version of homeassistant.

This package was inspired by [pytest-homeassistant](https://github.com/boralyl/pytest-homeassistant) by @boralyl, but is intended to more closely and automatically track the home-assistant/core library.
