# Changelog
This changelog only includes changes directly related to the structure of this project. Changes in testing behavior may still occur from changes in homeassistant/core.

Changes to minor version indicate a change structurally in this pacakge.  Changes in patch indicate changes solely from homeassistant/core. The latter does not imply no breaking changes are introduced.

## 0.2.0
* fix `load_fixture`

## 0.1.0
* remove Python 3.7 and add Python 3.9
* remove `async_test`
* move non-testing dependencies to separate `requirements_dev.txt`
