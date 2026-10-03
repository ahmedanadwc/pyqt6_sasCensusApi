"""Tests for wizard unlock/navigation behavior."""

from pyqt6_sas_census.state import WizardState, highest_unlocked_step, result_succeeded


def test_failed_results_do_not_unlock_next_pages():
    state = WizardState(sas_connected=True, environment_ready=True)
    state.step2_result = {"success": False}
    assert highest_unlocked_step(state) == 1


def test_endpoint_selection_unlocks_query():
    state = WizardState(
        sas_connected=True,
        environment_ready=True,
        step2_result={"success": True},
        step3_result={"success": True},
        endpoint_selected=True,
    )
    assert highest_unlocked_step(state) == 4


def test_result_succeeded_edge_cases():
    assert result_succeeded(None) is False
    assert result_succeeded({}) is False
    assert result_succeeded({"success": False}) is False
    assert result_succeeded({"success": True}) is True
    assert result_succeeded({"success": True, "log": "ok"}) is True
