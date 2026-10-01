"""Tests for the deprecation-report fixture."""

import pytest

# A module inside a `custom_components/` path, which is the only thing that
# makes Home Assistant call a frame a custom integration's
# (`frame.get_integration_frame` matches on the path, nothing else). Written to
# disk rather than imported so the test does not depend on a real integration
# staying deprecated.
PROBE = '''
from homeassistant.helpers.frame import ReportBehavior, report_usage


def call_deprecated_api():
    """Report from a frame inside custom_components, as a real one would."""
    report_usage(
        "calls something deprecated",
        core_behavior=ReportBehavior.IGNORE,
        core_integration_behavior=ReportBehavior.IGNORE,
        custom_integration_behavior=ReportBehavior.LOG,
        breaks_in_ha_version="2099.1.0",
    )
'''

# `hass` is what calls `frame.async_setup`, and `report_usage` raises without
# it, so the probe test takes it even though it never touches it.
TEST_USING_PROBE = '''
from custom_components.probe_integration.probe import call_deprecated_api


async def test_calls_deprecated_api(hass):
    call_deprecated_api()
'''


def ini(*lines: str) -> str:
    """Build a sub-run ini, with what every phacc consumer already sets."""
    return "\n".join(["[pytest]", "asyncio_mode = auto", *lines]) + "\n"


@pytest.fixture
def probe(pytester: pytest.Pytester) -> None:
    """Lay down the custom integration and the test that calls into it."""
    probe_dir = pytester.path / "custom_components" / "probe_integration"
    probe_dir.mkdir(parents=True)
    (probe_dir.parent / "__init__.py").write_text("")
    (probe_dir / "__init__.py").write_text("")
    (probe_dir / "probe.py").write_text(PROBE)
    pytester.makepyfile(test_probe=TEST_USING_PROBE)


def test_fails_by_default(pytester: pytest.Pytester, probe: None) -> None:
    """A report fails the suite without anything being configured."""
    pytester.makeini(ini())
    result = pytester.runpytest_subprocess()
    # The check runs after the test body, so the report arrives as a teardown
    # error rather than a failure -- the same shape `reset_globals` already uses
    # to fail a test that serialized a mock object.
    result.assert_outcomes(passed=1, errors=1)
    # The report names what to go and fix, which is the point of surfacing it.
    result.stdout.fnmatch_lines(
        ["*probe_integration*calls something deprecated*2099.1.0*"]
    )


def test_can_be_turned_off(pytester: pytest.Pytester, probe: None) -> None:
    """An escape hatch, for a suite with a backlog of reports to work through.

    Without this, adopting a version of this package that has the check would
    be a wall rather than a to-do list for anybody holding more than one
    report.
    """
    pytester.makeini(ini("phacc_fail_on_deprecation_report = false"))
    pytester.runpytest_subprocess().assert_outcomes(passed=1)


def test_ignores_reports_about_anything_but_a_custom_integration(
    pytester: pytest.Pytester,
) -> None:
    """A report with no custom integration behind it is not this suite's bug.

    Driven through `report_usage` from a test frame, which has no integration
    in it at all -- the one case Home Assistant reports without naming a
    custom integration, rather than a record built here to look like one.
    """
    pytester.makeini(ini())
    pytester.makepyfile(
        """
        from homeassistant.helpers.frame import ReportBehavior, report_usage


        async def test_report_without_an_integration_frame(hass):
            report_usage(
                "does something core cares about",
                core_behavior=ReportBehavior.LOG,
                breaks_in_ha_version="2099.1.0",
            )
        """
    )
    pytester.runpytest_subprocess().assert_outcomes(passed=1)


def test_domains_option_narrows_what_fails(
    pytester: pytest.Pytester, probe: None
) -> None:
    """Naming other domains leaves this one's reports alone."""
    pytester.makeini(
        ini(
            "phacc_deprecation_report_domains =",
            "    some_other_integration",
        )
    )
    pytester.runpytest_subprocess().assert_outcomes(passed=1)


def test_domains_option_matches_the_reported_domain(
    pytester: pytest.Pytester, probe: None
) -> None:
    """Naming this domain fails on it, so the filter is doing the deciding."""
    pytester.makeini(
        ini(
            "phacc_deprecation_report_domains =",
            "    probe_integration",
        )
    )
    pytester.runpytest_subprocess().assert_outcomes(passed=1, errors=1)
