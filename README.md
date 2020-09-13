# pytest-homeassistant-custom-component

![HA core version](https://img.shields.io/static/v1?label=HA+core+version&message=0.116.0.dev0&labelColor=blue)

Experimental package to automatically extract testing plugins from Home Assistant for custom component testing. Automatic extraction of testing plugins and helpers. It is unknown whether this can be as full featured as the test modules inside of homeassistant/core.

* For now, this package will be updated randomly with no set schedule.
* Version of homeassistant is given in pytest_homeassistant_custom_component.const and in the README above

Checklist for making this nearly automatic:
- [x] Create PR automatically with changes
- [ ] Use simple integration to test basic functionality upon extraction
- [ ] When PR merged into master, automatically create release
  - [ ] bump version
  - [ ] commit version changes
  - [ ] tag
  - [ ] create release
  - [x] publish to pypi
