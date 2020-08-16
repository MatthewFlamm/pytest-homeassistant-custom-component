# pytest-homeassistant-custom-component
Experimental package to automatically extract testing plugins from Home Assistant for custom component testing. Automatic extraction of testing plugins and helpers. It is unknown whether this can be as full featured as the test modules inside of homeassistant/core.

TODO thoughts:
* For now, this package will be updated randomly with no set schedule.
* Versioning ideas:
  * Sync with homeassistant by using corresponding version numbers?
  * How often are the testing plugins and helpers updated?
  * Maybe asynchronous releases when changes are seen, with note of which version it represents?
* Testing:
  * How to test that automatic extraction is okay?
  * What about new needed modules?
