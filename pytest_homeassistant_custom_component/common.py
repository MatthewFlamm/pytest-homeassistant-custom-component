"""
Test the helper method for writing .

This file is originally from homeassistant/core and modified by pytest-homeassistant-custom-component.
"""
from __future__ import annotations

import asyncio
from collections import OrderedDict
from collections.abc import Awaitable, Callable, Collection
from contextlib import contextmanager
from datetime import datetime, timedelta
import functools as ft
from io import StringIO
import json
import logging
import os
import pathlib
import threading
import time
from time import monotonic
import traceback
import types
from typing import Any
from unittest.mock import AsyncMock, Mock, patch

from aiohttp.test_utils import unused_port as get_test_instance_port  # noqa: F401
import voluptuous as vol

from homeassistant import auth, bootstrap, config_entries, core as ha, loader
from homeassistant.auth import (
    auth_store,
    models as auth_models,
    permissions as auth_permissions,
    providers as auth_providers,
)
from homeassistant.auth.permissions import system_policies
from homeassistant.components import device_automation, recorder
from homeassistant.components.device_automation import (  # noqa: F401
    _async_get_device_automation_capabilities as async_get_device_automation_capabilities,
)
from homeassistant.components.mqtt.models import ReceiveMessage
from homeassistant.config import async_process_component_config
from homeassistant.const import (
    DEVICE_DEFAULT_NAME,
    EVENT_HOMEASSISTANT_CLOSE,
    EVENT_STATE_CHANGED,
    STATE_OFF,
    STATE_ON,
)
from homeassistant.core import BLOCK_LOG_TIMEOUT, HomeAssistant, ServiceCall, State
from homeassistant.helpers import (
    area_registry,
    device_registry,
    entity,
    entity_platform,
    entity_registry,
    intent,
    issue_registry,
    recorder as recorder_helper,
    restore_state,
    storage,
)
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.json import JSONEncoder
from homeassistant.helpers.typing import ConfigType
from homeassistant.setup import setup_component
from homeassistant.util.async_ import run_callback_threadsafe
import homeassistant.util.dt as date_util
from homeassistant.util.unit_system import METRIC_SYSTEM
import homeassistant.util.uuid as uuid_util
import homeassistant.util.yaml.loader as yaml_loader

_LOGGER = logging.getLogger(__name__)
INSTANCES = []
CLIENT_ID = "https://example.com/app"
CLIENT_REDIRECT_URI = "https://example.com/app/callback"


async def async_get_device_automations(
    hass: HomeAssistant,
    automation_type: device_automation.DeviceAutomationType,
    device_id: str,
) -> Any:
    """Get a device automation for a single device id."""
    automations = await device_automation.async_get_device_automations(
        hass, automation_type, [device_id]
    )
    return automations.get(device_id)


def threadsafe_callback_factory(func):
    """Create threadsafe functions out of callbacks.

    Callback needs to have `hass` as first argument.
    """

    @ft.wraps(func)
    def threadsafe(*args, **kwargs):
        """Call func threadsafe."""
        hass = args[0]
        return run_callback_threadsafe(
            hass.loop, ft.partial(func, *args, **kwargs)
        ).result()

    return threadsafe


def threadsafe_coroutine_factory(func):
    """Create threadsafe functions out of coroutine.

    Callback needs to have `hass` as first argument.
    """

    @ft.wraps(func)
    def threadsafe(*args, **kwargs):
        """Call func threadsafe."""
        hass = args[0]
        return asyncio.run_coroutine_threadsafe(
            func(*args, **kwargs), hass.loop
        ).result()

    return threadsafe


def get_test_config_dir(*add_path):
    """Return a path to a test config dir."""
    return os.path.join(os.path.dirname(__file__), "testing_config", *add_path)


def get_test_home_assistant():
    """Return a Home Assistant object pointing at test config directory."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    hass = loop.run_until_complete(async_test_home_assistant(loop))

    loop_stop_event = threading.Event()

    def run_loop():
        """Run event loop."""
        # pylint: disable=protected-access
        loop._thread_ident = threading.get_ident()
        loop.run_forever()
        loop_stop_event.set()

    orig_stop = hass.stop
    hass._stopped = Mock(set=loop.stop)

    def start_hass(*mocks):
        """Start hass."""
        asyncio.run_coroutine_threadsafe(hass.async_start(), loop).result()

    def stop_hass():
        """Stop hass."""
        orig_stop()
        loop_stop_event.wait()
        loop.close()

    hass.start = start_hass
    hass.stop = stop_hass

    threading.Thread(name="LoopThread", target=run_loop, daemon=False).start()

    return hass


# pylint: disable=protected-access
async def async_test_home_assistant(event_loop, load_registries=True):
    """Return a Home Assistant object pointing at test config dir."""
    hass = ha.HomeAssistant()
    store = auth_store.AuthStore(hass)
    hass.auth = auth.AuthManager(hass, store, {}, {})
    ensure_auth_manager_loaded(hass.auth)
    INSTANCES.append(hass)

    orig_async_add_job = hass.async_add_job
    orig_async_add_executor_job = hass.async_add_executor_job
    orig_async_create_task = hass.async_create_task

    def async_add_job(target, *args):
        """Add job."""
        check_target = target
        while isinstance(check_target, ft.partial):
            check_target = check_target.func

        if isinstance(check_target, Mock) and not isinstance(target, AsyncMock):
            fut = asyncio.Future()
            fut.set_result(target(*args))
            return fut

        return orig_async_add_job(target, *args)

    def async_add_executor_job(target, *args):
        """Add executor job."""
        check_target = target
        while isinstance(check_target, ft.partial):
            check_target = check_target.func

        if isinstance(check_target, Mock):
            fut = asyncio.Future()
            fut.set_result(target(*args))
            return fut

        return orig_async_add_executor_job(target, *args)

    def async_create_task(coroutine):
        """Create task."""
        if isinstance(coroutine, Mock) and not isinstance(coroutine, AsyncMock):
            fut = asyncio.Future()
            fut.set_result(None)
            return fut

        return orig_async_create_task(coroutine)

    async def async_wait_for_task_count(self, max_remaining_tasks: int = 0) -> None:
        """Block until at most max_remaining_tasks remain.

        Based on HomeAssistant.async_block_till_done
        """
        # To flush out any call_soon_threadsafe
        await asyncio.sleep(0)
        start_time: float | None = None

        while len(self._pending_tasks) > max_remaining_tasks:
            pending: Collection[Awaitable[Any]] = [
                task for task in self._pending_tasks if not task.done()
            ]
            self._pending_tasks.clear()
            if len(pending) > max_remaining_tasks:
                remaining_pending = await self._await_count_and_log_pending(
                    pending, max_remaining_tasks=max_remaining_tasks
                )
                self._pending_tasks.extend(remaining_pending)

                if start_time is None:
                    # Avoid calling monotonic() until we know
                    # we may need to start logging blocked tasks.
                    start_time = 0
                elif start_time == 0:
                    # If we have waited twice then we set the start
                    # time
                    start_time = monotonic()
                elif monotonic() - start_time > BLOCK_LOG_TIMEOUT:
                    # We have waited at least three loops and new tasks
                    # continue to block. At this point we start
                    # logging all waiting tasks.
                    for task in pending:
                        _LOGGER.debug("Waiting for task: %s", task)
            else:
                self._pending_tasks.extend(pending)
                await asyncio.sleep(0)

    async def _await_count_and_log_pending(
        self, pending: Collection[Awaitable[Any]], max_remaining_tasks: int = 0
    ) -> Collection[Awaitable[Any]]:
        """Block at most max_remaining_tasks remain and log tasks that take a long time.

        Based on HomeAssistant._await_and_log_pending
        """
        wait_time = 0

        return_when = asyncio.ALL_COMPLETED
        if max_remaining_tasks:
            return_when = asyncio.FIRST_COMPLETED

        while len(pending) > max_remaining_tasks:
            _, pending = await asyncio.wait(
                pending, timeout=BLOCK_LOG_TIMEOUT, return_when=return_when
            )
            if not pending or max_remaining_tasks:
                return pending
            wait_time += BLOCK_LOG_TIMEOUT
            for task in pending:
                _LOGGER.debug("Waited %s seconds for task: %s", wait_time, task)

        return []

    hass.async_add_job = async_add_job
    hass.async_add_executor_job = async_add_executor_job
    hass.async_create_task = async_create_task
    hass.async_wait_for_task_count = types.MethodType(async_wait_for_task_count, hass)
    hass._await_count_and_log_pending = types.MethodType(
        _await_count_and_log_pending, hass
    )

    hass.data[loader.DATA_CUSTOM_COMPONENTS] = {}

    hass.config.location_name = "test home"
    hass.config.config_dir = get_test_config_dir()
    hass.config.latitude = 32.87336
    hass.config.longitude = -117.22743
    hass.config.elevation = 0
    hass.config.set_time_zone("US/Pacific")
    hass.config.units = METRIC_SYSTEM
    hass.config.media_dirs = {"local": get_test_config_dir("media")}
    hass.config.skip_pip = True
    hass.config.skip_pip_packages = []

    hass.config_entries = config_entries.ConfigEntries(
        hass,
        {
            "_": "Not empty or else some bad checks for hass config in discovery.py breaks"
        },
    )

    # Load the registries
    if load_registries:
        await asyncio.gather(
            area_registry.async_load(hass),
            device_registry.async_load(hass),
            entity_registry.async_load(hass),
            issue_registry.async_load(hass),
        )
        await hass.async_block_till_done()
        hass.data[bootstrap.DATA_REGISTRIES_LOADED] = None

    hass.state = ha.CoreState.running

    # Mock async_start
    orig_start = hass.async_start

    async def mock_async_start():
        """Start the mocking."""
        # We only mock time during tests and we want to track tasks
        with patch.object(hass, "async_stop_track_tasks"):
            await orig_start()

    hass.async_start = mock_async_start

    @ha.callback
    def clear_instance(event):
        """Clear global instance."""
        INSTANCES.remove(hass)

    hass.bus.async_listen_once(EVENT_HOMEASSISTANT_CLOSE, clear_instance)

    return hass


def async_mock_service(
    hass: HomeAssistant, domain: str, service: str, schema: vol.Schema | None = None
) -> list[ServiceCall]:
    """Set up a fake service & return a calls log list to this service."""
    calls = []

    @ha.callback
    def mock_service_log(call):  # pylint: disable=unnecessary-lambda
        """Mock service call."""
        calls.append(call)

    hass.services.async_register(domain, service, mock_service_log, schema=schema)

    return calls


mock_service = threadsafe_callback_factory(async_mock_service)


@ha.callback
def async_mock_intent(hass, intent_typ):
    """Set up a fake intent handler."""
    intents = []

    class MockIntentHandler(intent.IntentHandler):
        intent_type = intent_typ

        async def async_handle(self, intent):
            """Handle the intent."""
            intents.append(intent)
            return intent.create_response()

    intent.async_register(hass, MockIntentHandler())

    return intents


@ha.callback
def async_fire_mqtt_message(hass, topic, payload, qos=0, retain=False):
    """Fire the MQTT message."""
    if isinstance(payload, str):
        payload = payload.encode("utf-8")
    msg = ReceiveMessage(topic, payload, qos, retain)
    hass.data["mqtt"].client._mqtt_handle_message(msg)


fire_mqtt_message = threadsafe_callback_factory(async_fire_mqtt_message)


@ha.callback
def async_fire_time_changed_exact(
    hass: HomeAssistant, datetime_: datetime | None = None, fire_all: bool = False
) -> None:
    """Fire a time changed event at an exact microsecond.

    Consider that it is not possible to actually achieve an exact
    microsecond in production as the event loop is not precise enough.
    If your code relies on this level of precision, consider a different
    approach, as this is only for testing.
    """
    if datetime_ is None:
        utc_datetime = date_util.utcnow()
    else:
        utc_datetime = date_util.as_utc(datetime_)

    _async_fire_time_changed(hass, utc_datetime, fire_all)


@ha.callback
def async_fire_time_changed(
    hass: HomeAssistant, datetime_: datetime | None = None, fire_all: bool = False
) -> None:
    """Fire a time changed event.

    This function will add up to 0.5 seconds to the time to ensure that
    it accounts for the accidental synchronization avoidance code in repeating
    listeners.

    As asyncio is cooperative, we can't guarantee that the event loop will
    run an event at the exact time we want. If you need to fire time changed
    for an exact microsecond, use async_fire_time_changed_exact.
    """
    if datetime_ is None:
        utc_datetime = date_util.utcnow()
    else:
        utc_datetime = date_util.as_utc(datetime_)

    if utc_datetime.microsecond < 500000:
        # Allow up to 500000 microseconds to be added to the time
        # to handle update_coordinator's and
        # async_track_time_interval's
        # staggering to avoid thundering herd.
        utc_datetime = utc_datetime.replace(microsecond=500000)

    _async_fire_time_changed(hass, utc_datetime, fire_all)


@ha.callback
def _async_fire_time_changed(
    hass: HomeAssistant, utc_datetime: datetime | None, fire_all: bool
) -> None:
    timestamp = date_util.utc_to_timestamp(utc_datetime)
    for task in list(hass.loop._scheduled):
        if not isinstance(task, asyncio.TimerHandle):
            continue
        if task.cancelled():
            continue

        mock_seconds_into_future = timestamp - time.time()
        future_seconds = task.when() - hass.loop.time()

        if fire_all or mock_seconds_into_future >= future_seconds:
            with patch(
                "homeassistant.helpers.event.time_tracker_utcnow",
                return_value=utc_datetime,
            ), patch(
                "homeassistant.helpers.event.time_tracker_timestamp",
                return_value=timestamp,
            ):
                task._run()
                task.cancel()


fire_time_changed = threadsafe_callback_factory(async_fire_time_changed)


def get_fixture_path(filename: str, integration: str | None = None) -> pathlib.Path:
    """Get path of fixture."""
    start_path = traceback.extract_stack()[-3].filename
    if integration is None and "/" in filename and not filename.startswith("helpers/"):
        integration, filename = filename.split("/", 1)

    if integration is None:
        return pathlib.Path(start_path).parent.joinpath("fixtures", filename)

    return pathlib.Path(start_path).parent.joinpath(
        "components", integration, "fixtures", filename
    )


def load_fixture(filename: str, integration: str | None = None) -> str:
    """Load a fixture."""
    return get_fixture_path(filename, integration).read_text()


def mock_state_change_event(
    hass: HomeAssistant, new_state: State, old_state: State | None = None
) -> None:
    """Mock state change envent."""
    event_data = {"entity_id": new_state.entity_id, "new_state": new_state}

    if old_state:
        event_data["old_state"] = old_state

    hass.bus.fire(EVENT_STATE_CHANGED, event_data, context=new_state.context)


@ha.callback
def mock_component(hass: HomeAssistant, component: str) -> None:
    """Mock a component is setup."""
    if component in hass.config.components:
        AssertionError(f"Integration {component} is already setup")

    hass.config.components.add(component)


def mock_registry(
    hass: HomeAssistant,
    mock_entries: dict[str, entity_registry.RegistryEntry] | None = None,
) -> entity_registry.EntityRegistry:
    """Mock the Entity Registry."""
    registry = entity_registry.EntityRegistry(hass)
    if mock_entries is None:
        mock_entries = {}
    registry.entities = entity_registry.EntityRegistryItems()
    for key, entry in mock_entries.items():
        registry.entities[key] = entry

    hass.data[entity_registry.DATA_REGISTRY] = registry
    return registry


def mock_area_registry(
    hass: HomeAssistant, mock_entries: dict[str, area_registry.AreaEntry] | None = None
) -> area_registry.AreaRegistry:
    """Mock the Area Registry."""
    registry = area_registry.AreaRegistry(hass)
    registry.areas = mock_entries or OrderedDict()

    hass.data[area_registry.DATA_REGISTRY] = registry
    return registry


def mock_device_registry(
    hass: HomeAssistant,
    mock_entries: dict[str, device_registry.DeviceEntry] | None = None,
) -> device_registry.DeviceRegistry:
    """Mock the Device Registry."""
    registry = device_registry.DeviceRegistry(hass)
    registry.devices = device_registry.DeviceRegistryItems()
    if mock_entries is None:
        mock_entries = {}
    for key, entry in mock_entries.items():
        registry.devices[key] = entry
    registry.deleted_devices = device_registry.DeviceRegistryItems()

    hass.data[device_registry.DATA_REGISTRY] = registry
    return registry


class MockGroup(auth_models.Group):
    """Mock a group in Home Assistant."""

    def __init__(self, id=None, name="Mock Group", policy=system_policies.ADMIN_POLICY):
        """Mock a group."""
        kwargs = {"name": name, "policy": policy}
        if id is not None:
            kwargs["id"] = id

        super().__init__(**kwargs)

    def add_to_hass(self, hass):
        """Test helper to add entry to hass."""
        return self.add_to_auth_manager(hass.auth)

    def add_to_auth_manager(self, auth_mgr):
        """Test helper to add entry to hass."""
        ensure_auth_manager_loaded(auth_mgr)
        auth_mgr._store._groups[self.id] = self
        return self


class MockUser(auth_models.User):
    """Mock a user in Home Assistant."""

    def __init__(
        self,
        id=None,
        is_owner=False,
        is_active=True,
        name="Mock User",
        system_generated=False,
        groups=None,
    ):
        """Initialize mock user."""
        kwargs = {
            "is_owner": is_owner,
            "is_active": is_active,
            "name": name,
            "system_generated": system_generated,
            "groups": groups or [],
            "perm_lookup": None,
        }
        if id is not None:
            kwargs["id"] = id
        super().__init__(**kwargs)

    def add_to_hass(self, hass):
        """Test helper to add entry to hass."""
        return self.add_to_auth_manager(hass.auth)

    def add_to_auth_manager(self, auth_mgr):
        """Test helper to add entry to hass."""
        ensure_auth_manager_loaded(auth_mgr)
        auth_mgr._store._users[self.id] = self
        return self

    def mock_policy(self, policy):
        """Mock a policy for a user."""
        self._permissions = auth_permissions.PolicyPermissions(policy, self.perm_lookup)


async def register_auth_provider(
    hass: HomeAssistant, config: ConfigType
) -> auth_providers.AuthProvider:
    """Register an auth provider."""
    provider = await auth_providers.auth_provider_from_config(
        hass, hass.auth._store, config
    )
    assert provider is not None, "Invalid config specified"
    key = (provider.type, provider.id)
    providers = hass.auth._providers

    if key in providers:
        raise ValueError("Provider already registered")

    providers[key] = provider
    return provider


@ha.callback
def ensure_auth_manager_loaded(auth_mgr):
    """Ensure an auth manager is considered loaded."""
    store = auth_mgr._store
    if store._users is None:
        store._set_defaults()


class MockModule:
    """Representation of a fake module."""

    # pylint: disable=invalid-name
    def __init__(
        self,
        domain=None,
        dependencies=None,
        setup=None,
        requirements=None,
        config_schema=None,
        platform_schema=None,
        platform_schema_base=None,
        async_setup=None,
        async_setup_entry=None,
        async_unload_entry=None,
        async_migrate_entry=None,
        async_remove_entry=None,
        partial_manifest=None,
        async_remove_config_entry_device=None,
    ):
        """Initialize the mock module."""
        self.__name__ = f"homeassistant.components.{domain}"
        self.__file__ = f"homeassistant/components/{domain}"
        self.DOMAIN = domain
        self.DEPENDENCIES = dependencies or []
        self.REQUIREMENTS = requirements or []
        # Overlay to be used when generating manifest from this module
        self._partial_manifest = partial_manifest

        if config_schema is not None:
            self.CONFIG_SCHEMA = config_schema

        if platform_schema is not None:
            self.PLATFORM_SCHEMA = platform_schema

        if platform_schema_base is not None:
            self.PLATFORM_SCHEMA_BASE = platform_schema_base

        if setup:
            # We run this in executor, wrap it in function
            self.setup = lambda *args: setup(*args)

        if async_setup is not None:
            self.async_setup = async_setup

        if setup is None and async_setup is None:
            self.async_setup = AsyncMock(return_value=True)

        if async_setup_entry is not None:
            self.async_setup_entry = async_setup_entry

        if async_unload_entry is not None:
            self.async_unload_entry = async_unload_entry

        if async_migrate_entry is not None:
            self.async_migrate_entry = async_migrate_entry

        if async_remove_entry is not None:
            self.async_remove_entry = async_remove_entry

        if async_remove_config_entry_device is not None:
            self.async_remove_config_entry_device = async_remove_config_entry_device

    def mock_manifest(self):
        """Generate a mock manifest to represent this module."""
        return {
            **loader.manifest_from_legacy_module(self.DOMAIN, self),
            **(self._partial_manifest or {}),
        }


class MockPlatform:
    """Provide a fake platform."""

    __name__ = "homeassistant.components.light.bla"
    __file__ = "homeassistant/components/blah/light"

    # pylint: disable=invalid-name
    def __init__(
        self,
        setup_platform=None,
        dependencies=None,
        platform_schema=None,
        async_setup_platform=None,
        async_setup_entry=None,
        scan_interval=None,
    ):
        """Initialize the platform."""
        self.DEPENDENCIES = dependencies or []

        if platform_schema is not None:
            self.PLATFORM_SCHEMA = platform_schema

        if scan_interval is not None:
            self.SCAN_INTERVAL = scan_interval

        if setup_platform is not None:
            # We run this in executor, wrap it in function
            self.setup_platform = lambda *args: setup_platform(*args)

        if async_setup_platform is not None:
            self.async_setup_platform = async_setup_platform

        if async_setup_entry is not None:
            self.async_setup_entry = async_setup_entry

        if setup_platform is None and async_setup_platform is None:
            self.async_setup_platform = AsyncMock(return_value=None)


class MockEntityPlatform(entity_platform.EntityPlatform):
    """Mock class with some mock defaults."""

    def __init__(
        self,
        hass,
        logger=None,
        domain="test_domain",
        platform_name="test_platform",
        platform=None,
        scan_interval=timedelta(seconds=15),
        entity_namespace=None,
    ):
        """Initialize a mock entity platform."""
        if logger is None:
            logger = logging.getLogger("homeassistant.helpers.entity_platform")

        # Otherwise the constructor will blow up.
        if isinstance(platform, Mock) and isinstance(platform.PARALLEL_UPDATES, Mock):
            platform.PARALLEL_UPDATES = 0

        super().__init__(
            hass=hass,
            logger=logger,
            domain=domain,
            platform_name=platform_name,
            platform=platform,
            scan_interval=scan_interval,
            entity_namespace=entity_namespace,
        )


class MockToggleEntity(entity.ToggleEntity):
    """Provide a mock toggle device."""

    def __init__(self, name, state, unique_id=None):
        """Initialize the mock entity."""
        self._name = name or DEVICE_DEFAULT_NAME
        self._state = state
        self.calls = []

    @property
    def name(self):
        """Return the name of the entity if any."""
        self.calls.append(("name", {}))
        return self._name

    @property
    def state(self):
        """Return the state of the entity if any."""
        self.calls.append(("state", {}))
        return self._state

    @property
    def is_on(self):
        """Return true if entity is on."""
        self.calls.append(("is_on", {}))
        return self._state == STATE_ON

    def turn_on(self, **kwargs):
        """Turn the entity on."""
        self.calls.append(("turn_on", kwargs))
        self._state = STATE_ON

    def turn_off(self, **kwargs):
        """Turn the entity off."""
        self.calls.append(("turn_off", kwargs))
        self._state = STATE_OFF

    def last_call(self, method=None):
        """Return the last call."""
        if not self.calls:
            return None
        if method is None:
            return self.calls[-1]
        try:
            return next(call for call in reversed(self.calls) if call[0] == method)
        except StopIteration:
            return None


class MockConfigEntry(config_entries.ConfigEntry):
    """Helper for creating config entries that adds some defaults."""

    def __init__(
        self,
        *,
        domain="test",
        data=None,
        version=1,
        entry_id=None,
        source=config_entries.SOURCE_USER,
        title="Mock Title",
        state=None,
        options={},
        pref_disable_new_entities=None,
        pref_disable_polling=None,
        unique_id=None,
        disabled_by=None,
        reason=None,
    ):
        """Initialize a mock config entry."""
        kwargs = {
            "entry_id": entry_id or uuid_util.random_uuid_hex(),
            "domain": domain,
            "data": data or {},
            "pref_disable_new_entities": pref_disable_new_entities,
            "pref_disable_polling": pref_disable_polling,
            "options": options,
            "version": version,
            "title": title,
            "unique_id": unique_id,
            "disabled_by": disabled_by,
        }
        if source is not None:
            kwargs["source"] = source
        if state is not None:
            kwargs["state"] = state
        super().__init__(**kwargs)
        if reason is not None:
            self.reason = reason

    def add_to_hass(self, hass):
        """Test helper to add entry to hass."""
        hass.config_entries._entries[self.entry_id] = self
        hass.config_entries._domain_index.setdefault(self.domain, []).append(
            self.entry_id
        )

    def add_to_manager(self, manager):
        """Test helper to add entry to entry manager."""
        manager._entries[self.entry_id] = self
        manager._domain_index.setdefault(self.domain, []).append(self.entry_id)


def patch_yaml_files(files_dict, endswith=True):
    """Patch load_yaml with a dictionary of yaml files."""
    # match using endswith, start search with longest string
    matchlist = sorted(files_dict.keys(), key=len) if endswith else []

    def mock_open_f(fname, **_):
        """Mock open() in the yaml module, used by load_yaml."""
        # Return the mocked file on full match
        if isinstance(fname, pathlib.Path):
            fname = str(fname)

        if fname in files_dict:
            _LOGGER.debug("patch_yaml_files match %s", fname)
            res = StringIO(files_dict[fname])
            setattr(res, "name", fname)
            return res

        # Match using endswith
        for ends in matchlist:
            if fname.endswith(ends):
                _LOGGER.debug("patch_yaml_files end match %s: %s", ends, fname)
                res = StringIO(files_dict[ends])
                setattr(res, "name", fname)
                return res

        # Fallback for hass.components (i.e. services.yaml)
        if "homeassistant/components" in fname:
            _LOGGER.debug("patch_yaml_files using real file: %s", fname)
            return open(fname, encoding="utf-8")

        # Not found
        raise FileNotFoundError(f"File not found: {fname}")

    return patch.object(yaml_loader, "open", mock_open_f, create=True)


def mock_coro(return_value=None, exception=None):
    """Return a coro that returns a value or raise an exception."""
    fut = asyncio.Future()
    if exception is not None:
        fut.set_exception(exception)
    else:
        fut.set_result(return_value)
    return fut


@contextmanager
def assert_setup_component(count, domain=None):
    """Collect valid configuration from setup_component.

    - count: The amount of valid platforms that should be setup
    - domain: The domain to count is optional. It can be automatically
              determined most of the time

    Use as a context manager around setup.setup_component
        with assert_setup_component(0) as result_config:
            setup_component(hass, domain, start_config)
            # using result_config is optional
    """
    config = {}

    async def mock_psc(hass, config_input, integration):
        """Mock the prepare_setup_component to capture config."""
        domain_input = integration.domain
        res = await async_process_component_config(hass, config_input, integration)
        config[domain_input] = None if res is None else res.get(domain_input)
        _LOGGER.debug(
            "Configuration for %s, Validated: %s, Original %s",
            domain_input,
            config[domain_input],
            config_input.get(domain_input),
        )
        return res

    assert isinstance(config, dict)
    with patch("homeassistant.config.async_process_component_config", mock_psc):
        yield config

    if domain is None:
        assert len(config) == 1, "assert_setup_component requires DOMAIN: {}".format(
            list(config.keys())
        )
        domain = list(config.keys())[0]

    res = config.get(domain)
    res_len = 0 if res is None else len(res)
    assert (
        res_len == count
    ), f"setup_component failed, expected {count} got {res_len}: {res}"


SetupRecorderInstanceT = Callable[..., Awaitable[recorder.Recorder]]


def init_recorder_component(hass, add_config=None, db_url="sqlite://"):
    """Initialize the recorder."""
    config = dict(add_config) if add_config else {}
    if recorder.CONF_DB_URL not in config:
        config[recorder.CONF_DB_URL] = db_url
        if recorder.CONF_COMMIT_INTERVAL not in config:
            config[recorder.CONF_COMMIT_INTERVAL] = 0

    with patch("homeassistant.components.recorder.ALLOW_IN_MEMORY_DB", True):
        if recorder.DOMAIN not in hass.data:
            recorder_helper.async_initialize_recorder(hass)
        assert setup_component(hass, recorder.DOMAIN, {recorder.DOMAIN: config})
        assert recorder.DOMAIN in hass.config.components
    _LOGGER.info(
        "Test recorder successfully started, database location: %s",
        config[recorder.CONF_DB_URL],
    )


def mock_restore_cache(hass, states):
    """Mock the DATA_RESTORE_CACHE."""
    key = restore_state.DATA_RESTORE_STATE_TASK
    data = restore_state.RestoreStateData(hass)
    now = date_util.utcnow()

    last_states = {}
    for state in states:
        restored_state = state.as_dict()
        restored_state = {
            **restored_state,
            "attributes": json.loads(
                json.dumps(restored_state["attributes"], cls=JSONEncoder)
            ),
        }
        last_states[state.entity_id] = restore_state.StoredState.from_dict(
            {"state": restored_state, "last_seen": now}
        )
    data.last_states = last_states
    _LOGGER.debug("Restore cache: %s", data.last_states)
    assert len(data.last_states) == len(states), f"Duplicate entity_id? {states}"

    hass.data[key] = data


def mock_restore_cache_with_extra_data(hass, states):
    """Mock the DATA_RESTORE_CACHE."""
    key = restore_state.DATA_RESTORE_STATE_TASK
    data = restore_state.RestoreStateData(hass)
    now = date_util.utcnow()

    last_states = {}
    for state, extra_data in states:
        restored_state = state.as_dict()
        restored_state = {
            **restored_state,
            "attributes": json.loads(
                json.dumps(restored_state["attributes"], cls=JSONEncoder)
            ),
        }
        last_states[state.entity_id] = restore_state.StoredState.from_dict(
            {"state": restored_state, "extra_data": extra_data, "last_seen": now}
        )
    data.last_states = last_states
    _LOGGER.debug("Restore cache: %s", data.last_states)
    assert len(data.last_states) == len(states), f"Duplicate entity_id? {states}"

    hass.data[key] = data


class MockEntity(entity.Entity):
    """Mock Entity class."""

    def __init__(self, **values):
        """Initialize an entity."""
        self._values = values

        if "entity_id" in values:
            self.entity_id = values["entity_id"]

    @property
    def available(self):
        """Return True if entity is available."""
        return self._handle("available")

    @property
    def capability_attributes(self):
        """Info about capabilities."""
        return self._handle("capability_attributes")

    @property
    def device_class(self):
        """Info how device should be classified."""
        return self._handle("device_class")

    @property
    def device_info(self):
        """Info how it links to a device."""
        return self._handle("device_info")

    @property
    def entity_category(self):
        """Return the entity category."""
        return self._handle("entity_category")

    @property
    def has_entity_name(self):
        """Return the has_entity_name name flag."""
        return self._handle("has_entity_name")

    @property
    def entity_registry_enabled_default(self):
        """Return if the entity should be enabled when first added to the entity registry."""
        return self._handle("entity_registry_enabled_default")

    @property
    def entity_registry_visible_default(self):
        """Return if the entity should be visible when first added to the entity registry."""
        return self._handle("entity_registry_visible_default")

    @property
    def icon(self):
        """Return the suggested icon."""
        return self._handle("icon")

    @property
    def name(self):
        """Return the name of the entity."""
        return self._handle("name")

    @property
    def should_poll(self):
        """Return the ste of the polling."""
        return self._handle("should_poll")

    @property
    def state(self):
        """Return the state of the entity."""
        return self._handle("state")

    @property
    def supported_features(self):
        """Info about supported features."""
        return self._handle("supported_features")

    @property
    def unique_id(self):
        """Return the unique ID of the entity."""
        return self._handle("unique_id")

    @property
    def unit_of_measurement(self):
        """Info on the units the entity state is in."""
        return self._handle("unit_of_measurement")

    def _handle(self, attr):
        """Return attribute value."""
        if attr in self._values:
            return self._values[attr]
        return getattr(super(), attr)


@contextmanager
def mock_storage(data=None):
    """Mock storage.

    Data is a dict {'key': {'version': version, 'data': data}}

    Written data will be converted to JSON to ensure JSON parsing works.
    """
    if data is None:
        data = {}

    orig_load = storage.Store._async_load

    async def mock_async_load(store):
        """Mock version of load."""
        if store._data is None:
            # No data to load
            if store.key not in data:
                return None

            mock_data = data.get(store.key)

            if "data" not in mock_data or "version" not in mock_data:
                _LOGGER.error('Mock data needs "version" and "data"')
                raise ValueError('Mock data needs "version" and "data"')

            store._data = mock_data

        # Route through original load so that we trigger migration
        loaded = await orig_load(store)
        _LOGGER.info("Loading data for %s: %s", store.key, loaded)
        return loaded

    def mock_write_data(store, path, data_to_write):
        """Mock version of write data."""
        # To ensure that the data can be serialized
        _LOGGER.info("Writing data to %s: %s", store.key, data_to_write)
        raise_contains_mocks(data_to_write)
        data[store.key] = json.loads(json.dumps(data_to_write, cls=store._encoder))

    async def mock_remove(store):
        """Remove data."""
        data.pop(store.key, None)

    with patch(
        "homeassistant.helpers.storage.Store._async_load",
        side_effect=mock_async_load,
        autospec=True,
    ), patch(
        "homeassistant.helpers.storage.Store._write_data",
        side_effect=mock_write_data,
        autospec=True,
    ), patch(
        "homeassistant.helpers.storage.Store.async_remove",
        side_effect=mock_remove,
        autospec=True,
    ):
        yield data


async def flush_store(store):
    """Make sure all delayed writes of a store are written."""
    if store._data is None:
        return

    store._async_cleanup_final_write_listener()
    store._async_cleanup_delay_listener()
    await store._async_handle_write_data()


async def get_system_health_info(hass, domain):
    """Get system health info."""
    return await hass.data["system_health"][domain].info_callback(hass)


def mock_integration(hass, module, built_in=True):
    """Mock an integration."""
    integration = loader.Integration(
        hass,
        f"{loader.PACKAGE_BUILTIN}.{module.DOMAIN}"
        if built_in
        else f"{loader.PACKAGE_CUSTOM_COMPONENTS}.{module.DOMAIN}",
        None,
        module.mock_manifest(),
    )

    def mock_import_platform(platform_name):
        raise ImportError(
            f"Mocked unable to import platform '{platform_name}'",
            name=f"{integration.pkg_path}.{platform_name}",
        )

    integration._import_platform = mock_import_platform

    _LOGGER.info("Adding mock integration: %s", module.DOMAIN)
    hass.data.setdefault(loader.DATA_INTEGRATIONS, {})[module.DOMAIN] = integration
    hass.data.setdefault(loader.DATA_COMPONENTS, {})[module.DOMAIN] = module

    return integration


def mock_entity_platform(hass, platform_path, module):
    """Mock a entity platform.

    platform_path is in form light.hue. Will create platform
    hue.light.
    """
    domain, platform_name = platform_path.split(".")
    mock_platform(hass, f"{platform_name}.{domain}", module)


def mock_platform(hass, platform_path, module=None):
    """Mock a platform.

    platform_path is in form hue.config_flow.
    """
    domain, platform_name = platform_path.split(".")
    integration_cache = hass.data.setdefault(loader.DATA_INTEGRATIONS, {})
    module_cache = hass.data.setdefault(loader.DATA_COMPONENTS, {})

    if domain not in integration_cache:
        mock_integration(hass, MockModule(domain))

    _LOGGER.info("Adding mock integration platform: %s", platform_path)
    module_cache[platform_path] = module or Mock()


def async_capture_events(hass, event_name):
    """Create a helper that captures events."""
    events = []

    @ha.callback
    def capture_events(event):
        events.append(event)

    hass.bus.async_listen(event_name, capture_events)

    return events


@ha.callback
def async_mock_signal(hass, signal):
    """Catch all dispatches to a signal."""
    calls = []

    @ha.callback
    def mock_signal_handler(*args):
        """Mock service call."""
        calls.append(args)

    async_dispatcher_connect(hass, signal, mock_signal_handler)

    return calls


def assert_lists_same(a, b):
    """Compare two lists, ignoring order.

    Check both that all items in a are in b and that all items in b are in a,
    otherwise assert_lists_same(["1", "1"], ["1", "2"]) could be True.
    """
    assert len(a) == len(b)
    for i in a:
        assert i in b
    for i in b:
        assert i in a


def raise_contains_mocks(val):
    """Raise for mocks."""
    if isinstance(val, Mock):
        raise ValueError

    if isinstance(val, dict):
        for dict_value in val.values():
            raise_contains_mocks(dict_value)

    if isinstance(val, list):
        for dict_value in val:
            raise_contains_mocks(dict_value)
