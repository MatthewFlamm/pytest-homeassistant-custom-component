"""
Fail tests whose run makes Home Assistant report a custom integration.

Unlike everything under ``pytest_homeassistant_custom_component``, this module
is written here rather than extracted from homeassistant/core. It exists
because core cannot supply it: ``report_usage`` raises for core callers and for
callers with no integration frame, and only *custom* integrations get
``ReportBehavior.LOG``. A custom integration therefore has no way to learn
from its own test suite that it called a deprecated API -- the report goes to a
log nobody reads until a user pastes it into an issue, by which time the
removal version may already be close.

Off unless ``phacc_fail_on_deprecation_report`` is set, so adding it breaks
nobody's suite on an automatic version bump.
"""

from __future__ import annotations

from collections.abc import Generator
import logging

import pytest

# Every report Home Assistant makes about an integration is formatted by one of
# two ``_LOGGER.log`` calls in ``homeassistant.helpers.frame``, and both pass
# the integration kind first and the domain second. Reading those two arguments
# keeps this off the rendered wording, which is not a contract and has been
# reworded before.
_FRAME_LOGGER = "homeassistant.helpers.frame"
_KIND_ARG = 0
_DOMAIN_ARG = 1
_CUSTOM_KIND = "custom "

_INI_ENABLED = "phacc_fail_on_deprecation_report"
_INI_DOMAINS = "phacc_deprecation_report_domains"


def pytest_addoption(parser: pytest.Parser) -> None:
    """Register the ini options that enable and narrow the check."""
    parser.addini(
        _INI_ENABLED,
        "Fail a test if Home Assistant reports a custom integration for "
        "deprecated or incorrect API usage. Off by default.",
        type="bool",
        default=False,
    )
    parser.addini(
        _INI_DOMAINS,
        "Domains to fail on, one per line. Empty means every custom "
        "integration, which is what a repository holding one integration "
        "wants; name domains only if the tests deliberately load somebody "
        "else's custom integration too.",
        type="linelist",
        default=[],
    )


class _ReportCollector(logging.Handler):
    """Collect the reports that blame a custom integration under test."""

    def __init__(self, domains: frozenset[str]) -> None:
        """Watch ``domains``, or every custom integration when it is empty."""
        super().__init__()
        self._domains = domains
        self.reports: list[str] = []

    def emit(self, record: logging.LogRecord) -> None:
        """Keep ``record`` if it is a report about a watched integration."""
        args = record.args
        if not isinstance(args, tuple) or len(args) <= _DOMAIN_ARG:
            return
        if args[_KIND_ARG] != _CUSTOM_KIND:
            return
        if self._domains and args[_DOMAIN_ARG] not in self._domains:
            return
        self.reports.append(record.getMessage())


@pytest.fixture(autouse=True)
def fail_on_deprecation_report(request: pytest.FixtureRequest) -> Generator[None]:
    """
    Turn Home Assistant's reports about this integration into test failures.

    Reports name the file, the line and the source line that triggered them,
    so the failure says where to look without a traceback.

    Every test that reaches a reported call fails, not only the first: Home
    Assistant deduplicates reports by call site, but ``reset_globals`` clears
    that set after each test, so each test starts able to see its own.
    """
    if not request.config.getini(_INI_ENABLED):
        yield
        return

    collector = _ReportCollector(frozenset(request.config.getini(_INI_DOMAINS)))
    logger = logging.getLogger(_FRAME_LOGGER)
    # Reports are logged at WARNING. A suite that raised the threshold above it
    # would otherwise get a check that silently passes forever, which is worse
    # than not having one.
    restore_level = logger.level if not logger.isEnabledFor(logging.WARNING) else None
    if restore_level is not None:
        logger.setLevel(logging.WARNING)
    logger.addHandler(collector)
    try:
        yield
    finally:
        logger.removeHandler(collector)
        if restore_level is not None:
            logger.setLevel(restore_level)

    if collector.reports:
        pytest.fail(
            "Home Assistant reported this integration for deprecated or "
            "incorrect API usage:\n\n" + "\n\n".join(collector.reports),
            pytrace=False,
        )
