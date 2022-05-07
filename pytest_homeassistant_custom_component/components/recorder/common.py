"""
Common test utils for working with recorder.

This file is originally from homeassistant/core and modified by pytest-homeassistant-custom-component.
"""
from __future__ import annotations

from datetime import datetime, timedelta
from typing import cast

from sqlalchemy import create_engine
from sqlalchemy.orm.session import Session

from homeassistant import core as ha
from homeassistant.components import recorder
from homeassistant.components.recorder.models import RecorderRuns
from homeassistant.core import HomeAssistant
from homeassistant.util import dt as dt_util

from ...common import async_fire_time_changed, fire_time_changed
from ...components.recorder import models_schema_0

DEFAULT_PURGE_TASKS = 3


def wait_recording_done(hass: HomeAssistant) -> None:
    """Block till recording is done."""
    hass.block_till_done()
    trigger_db_commit(hass)
    hass.block_till_done()
    hass.data[recorder.DATA_INSTANCE].block_till_done()
    hass.block_till_done()


def trigger_db_commit(hass: HomeAssistant) -> None:
    """Force the recorder to commit."""
    for _ in range(recorder.DEFAULT_COMMIT_INTERVAL):
        # We only commit on time change
        fire_time_changed(hass, dt_util.utcnow() + timedelta(seconds=1))


async def async_wait_recording_done(hass: HomeAssistant) -> None:
    """Async wait until recording is done."""
    await hass.async_block_till_done()
    async_trigger_db_commit(hass)
    await hass.async_block_till_done()
    await async_recorder_block_till_done(hass)
    await hass.async_block_till_done()


async def async_wait_purge_done(hass: HomeAssistant, max: int = None) -> None:
    """Wait for max number of purge events.

    Because a purge may insert another PurgeTask into
    the queue after the WaitTask finishes, we need up to
    a maximum number of WaitTasks that we will put into the
    queue.
    """
    if not max:
        max = DEFAULT_PURGE_TASKS
    for _ in range(max + 1):
        await async_wait_recording_done(hass)


@ha.callback
def async_trigger_db_commit(hass: HomeAssistant) -> None:
    """Force the recorder to commit. Async friendly."""
    for _ in range(recorder.DEFAULT_COMMIT_INTERVAL):
        async_fire_time_changed(hass, dt_util.utcnow() + timedelta(seconds=1))


async def async_recorder_block_till_done(hass: HomeAssistant) -> None:
    """Non blocking version of recorder.block_till_done()."""
    instance: recorder.Recorder = hass.data[recorder.DATA_INSTANCE]
    await hass.async_add_executor_job(instance.block_till_done)


def corrupt_db_file(test_db_file):
    """Corrupt an sqlite3 database file."""
    with open(test_db_file, "w+") as fhandle:
        fhandle.seek(200)
        fhandle.write("I am a corrupt db" * 100)


def create_engine_test(*args, **kwargs):
    """Test version of create_engine that initializes with old schema.

    This simulates an existing db with the old schema.
    """
    engine = create_engine(*args, **kwargs)
    models_schema_0.Base.metadata.create_all(engine)
    return engine


def run_information_with_session(
    session: Session, point_in_time: datetime | None = None
) -> RecorderRuns | None:
    """Return information about current run from the database."""
    recorder_runs = RecorderRuns

    query = session.query(recorder_runs)
    if point_in_time:
        query = query.filter(
            (recorder_runs.start < point_in_time) & (recorder_runs.end > point_in_time)
        )

    if (res := query.first()) is not None:
        session.expunge(res)
        return cast(RecorderRuns, res)
    return res
