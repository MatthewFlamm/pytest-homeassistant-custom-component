"""List of tests that have uncaught exceptions today. Will be shrunk over time."""
IGNORE_UNCAUGHT_EXCEPTIONS = [
    ("test_homeassistant_bridge", "test_homeassistant_bridge_fan_setup",),
    (
        "pytest_homeassistant_custom_component.components.owntracks.test_device_tracker",
        "test_mobile_multiple_async_enter_exit",
    ),
    (
        "pytest_homeassistant_custom_component.components.smartthings.test_init",
        "test_event_handler_dispatches_updated_devices",
    ),
    (
        "pytest_homeassistant_custom_component.components.unifi.test_controller",
        "test_wireless_client_event_calls_update_wireless_devices",
    ),
]
