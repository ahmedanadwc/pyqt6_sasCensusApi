"""Regression tests: the visible status label on each wizard page must
actually update in place after a worker finishes or fails.

Previously each page did `self._status_label = status_label(...)`, which
reassigned the Python attribute to a brand-new QLabel that was never added
to any layout - the label actually on screen (the one created in
_setup_ui and added via layout.addWidget) never changed. Each test below
captures a reference to that on-screen label *before* triggering the
worker callback and asserts both that it is still the same widget
instance afterwards (`is`) and that its text/color actually changed.
"""

import sys
import pandas as pd
from PyQt6.QtWidgets import QApplication

# Ensure a single QApplication instance exists for tests
app = QApplication.instance() or QApplication(sys.argv)

from pyqt6_sas_census.state import WizardState
from pyqt6_sas_census.services.sas_service import SasService, OperationResult
from pyqt6_sas_census.ui.pages.connection import ConnectionPage
from pyqt6_sas_census.ui.pages.catalog import CatalogPage
from pyqt6_sas_census.ui.pages.profile_query import ProfileQueryPage
from pyqt6_sas_census.ui.wizard import WizardWindow


class _FakeBackend:
    is_connected = False

    def fetch_dataframe(self, *args, **kwargs):
        return None


def _service() -> SasService:
    return SasService(_FakeBackend())


def test_connection_page_status_label_updates_on_success():
    page = ConnectionPage(WizardState(), _service())
    on_screen_label = page._status_label
    assert on_screen_label.text() == ""

    page._on_worker_finished(
        OperationResult(success=True, log="Successfully connected to SAS.")
    )

    assert page._status_label is on_screen_label
    assert on_screen_label.text() == "Success"
    assert "green" in on_screen_label.styleSheet()


def test_connection_page_status_label_updates_on_worker_failure():
    page = ConnectionPage(WizardState(), _service())
    on_screen_label = page._status_label

    page._on_worker_failed("boom")

    assert page._status_label is on_screen_label
    assert on_screen_label.text() == "Worker error: boom"
    assert "red" in on_screen_label.styleSheet()


def test_connection_page_resets_state_after_failed_disconnect_clears_session():
    state = WizardState()
    state.sas_connected = True
    state.environment_ready = True
    page = ConnectionPage(state, _service())

    page._on_worker_finished(
        OperationResult(
            success=False,
            log="Failed to disconnect SAS session: shutdown failed",
            errors=["shutdown failed"],
            metadata={"session_cleared": True},
        )
    )

    assert state.sas_connected is False
    assert state.environment_ready is False
    assert "Disconnected" in page._connection_badge.text()
    assert page._status_label.text() == "Failed"


def test_connection_page_rejects_worker_while_another_operation_is_reserved():
    page = ConnectionPage(WizardState(), _service())
    service = page._service
    assert service.try_begin_operation() is True
    calls = []

    page._run_worker(lambda: calls.append("ran"))

    assert calls == []
    assert page._status_label.text() == "Worker error: Another SAS operation is already in progress."
    service.end_operation()


def test_wizard_does_not_accept_while_sas_operation_is_reserved():
    wizard = WizardWindow(WizardState(), _service())
    accepted = []
    wizard.accepted.connect(lambda: accepted.append(True))
    assert wizard._service.try_begin_operation() is True

    wizard.accept()

    assert accepted == []
    assert "operation is still running" in wizard.windowTitle()
    wizard._service.end_operation()


def test_catalog_page_status_label_updates_on_success():
    page = CatalogPage(WizardState(), _service())
    on_screen_label = page._status_label
    df = pd.DataFrame({"title": ["A"]})

    page._on_worker_finished(OperationResult(success=True, log="ok", dataframe=df))

    assert page._status_label is on_screen_label
    assert on_screen_label.text() == "Success"
    assert "green" in on_screen_label.styleSheet()


def test_catalog_page_status_label_updates_on_macro_failure():
    page = CatalogPage(WizardState(), _service())
    on_screen_label = page._status_label

    page._on_worker_finished(OperationResult(success=False, log="macro failed"))

    assert page._status_label is on_screen_label
    assert on_screen_label.text() == "Failed"
    assert "red" in on_screen_label.styleSheet()


def test_catalog_page_status_label_updates_on_worker_failure():
    page = CatalogPage(WizardState(), _service())
    on_screen_label = page._status_label

    page._on_worker_failed("boom")

    assert page._status_label is on_screen_label
    assert on_screen_label.text() == "Worker error: boom"
    assert "red" in on_screen_label.styleSheet()


def test_catalog_existing_dataset_fetch_is_scheduled_as_worker():
    state = WizardState()
    state.sas_connected = True
    state.environment_ready = True
    page = CatalogPage(state, _service())
    scheduled = []
    calls = []
    page._service.backend.fetch_dataframe = lambda *args, **kwargs: calls.append(
        (args, kwargs)
    )
    page._run_worker = lambda func, **handlers: scheduled.append((func, handlers))

    page._try_fetch_existing()

    assert len(scheduled) == 1
    assert calls == []
    fetch, handlers = scheduled[0]
    fetch()
    assert len(calls) == 1
    assert handlers["finished_handler"] == page._on_existing_catalog_loaded
    handlers["finished_handler"](None)


def test_profile_table_fetch_is_scheduled_and_preserves_refresh_option():
    state = WizardState()
    state.dataset_unique_id = "dataset-id"
    page = ProfileQueryPage(state, _service())
    scheduled = []
    calls = []
    page._service.fetch_profile_tables = lambda uid, force_refresh=False: (
        calls.append((uid, force_refresh)) or {}
    )
    page._run_worker = lambda func, **handlers: scheduled.append((func, handlers))

    page._load_profile_tables(force_refresh=True)

    assert len(scheduled) == 1
    assert scheduled[0][1]["finished_handler"] == page._on_profile_tables_loaded
    assert calls == []
    tables = scheduled[0][0]()
    assert tables == {}
    assert calls == [("dataset-id", True)]


def test_profile_reuse_check_runs_in_background():
    state = WizardState()
    state.dataset_unique_id = "dataset-id"
    page = ProfileQueryPage(state, _service())
    page._row_id_edit.setText("3")
    scheduled = []
    calls = []
    tables = {
        label: (f"table_{index}", pd.DataFrame())
        for index, label in enumerate(
            ("Variables", "Groups", "Geographies", "Sample Queries")
        )
    }
    page._service.fetch_profile_tables = lambda uid, force_refresh=False: (
        calls.append((uid, force_refresh)) or tables
    )
    page._run_worker = lambda func, **handlers: scheduled.append(func)

    page._on_run_profile()

    assert calls == []
    result = scheduled[0]()
    assert calls == [("dataset-id", False)]
    assert result.metadata["reused"] is True


def test_profile_worker_failure_keeps_its_operation_identity():
    state = WizardState()
    page = ProfileQueryPage(state, _service())
    page._current_operation = "query"

    page._on_profile_worker_failed("profile request failed")

    assert state.step3_profile_result == {
        "success": False,
        "log": "profile request failed",
    }
    assert state.step3_query_result is None
