# pytest-homeassistant-custom-component

![HA core version](https://img.shields.io/static/v1?label=HA+core+version&message=2026.9.4&labelColor=blue)

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
* pytest-asyncio now requires `asyncio_mode = auto` config, see https://github.com/MatthewFlamm/pytest-homeassistant-custom-component/issues/129 and https://github.com/MatthewFlamm/pytest-homeassistant-custom-component/issues/247.
* If using `load_fixture`, the files need to be in a `fixtures` folder colocated with the tests. For example, a test in `test_sensor.py` can load data from `some_data.json` using `load_fixture` from this structure:

```
tests/
   fixtures/
      some_data.json
   test_sensor.py
```

* When using syrupy snapshots, add a `snapshot` fixture to conftest.py to make sure the snapshots are loaded from snapshot folder colocated with the tests.

```py
    from pytest_homeassistant_custom_component.syrupy import HomeAssistantSnapshotExtension
    from syrupy.assertion import SnapshotAssertion


    @pytest.fixture
    def snapshot(snapshot: SnapshotAssertion) -> SnapshotAssertion:
        """Return snapshot assertion fixture with the Home Assistant extension."""
        return snapshot.use_extension(HomeAssistantSnapshotExtension)
```

## Catching deprecated Home Assistant API usage

Home Assistant reports deprecated and incorrect API usage through
`homeassistant.helpers.frame.report_usage`. That report *raises* for a
homeassistant/core caller and for a call made straight from a test, but for a
custom integration it only *logs*. A custom integration's test suite therefore
stays green while its production code calls something Home Assistant has already
scheduled for removal, and the warning is only seen once a user pastes a log into
an issue.

Set `phacc_fail_on_deprecation_report` to turn those reports into test failures:

```ini
[pytest]
asyncio_mode = auto
phacc_fail_on_deprecation_report = true
```

The failure quotes Home Assistant's own report, which names the file, the line
and the source line that triggered it:

```
Detected that custom integration 'my_integration' calls
`device_registry.async_get_device`, which is deprecated [...] at
custom_components/my_integration/__init__.py, line 460: device = dev_reg.async_get_device(.
This will stop working in Home Assistant 2027.8.0
```

This is off by default, so adding it to an existing suite cannot change that
suite's result until you ask for it.

If your tests deliberately load somebody else's custom integration too, name the
domains you are responsible for so only your own reports fail the suite:

```ini
phacc_deprecation_report_domains =
    my_integration
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
