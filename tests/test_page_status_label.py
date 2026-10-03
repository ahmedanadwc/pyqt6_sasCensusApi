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
from pyqt6_sas_census.ui.pages.profile import ProfilePage
from pyqt6_sas_census.ui.pages.query import QueryPage


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


def test_profile_page_status_label_updates_on_success():
    page = ProfilePage(WizardState(), _service())
    on_screen_label = page._status_label

    page._on_worker_finished(OperationResult(success=True, log="ok"))

    assert page._status_label is on_screen_label
    assert on_screen_label.text() == "Success"
    assert "green" in on_screen_label.styleSheet()


def test_profile_page_status_label_updates_on_worker_failure():
    page = ProfilePage(WizardState(), _service())
    on_screen_label = page._status_label

    page._on_worker_failed("boom")

    assert page._status_label is on_screen_label
    assert on_screen_label.text() == "Worker error: boom"
    assert "red" in on_screen_label.styleSheet()


def test_query_page_status_label_updates_on_success_with_data():
    page = QueryPage(WizardState(), _service())
    on_screen_label = page._status_label
    df = pd.DataFrame({"NAME": ["A"]})

    page._on_worker_finished(OperationResult(success=True, log="ok", dataframe=df))

    assert page._status_label is on_screen_label
    assert on_screen_label.text() == "Success"
    assert "green" in on_screen_label.styleSheet()


def test_query_page_status_label_shows_no_data_message():
    page = QueryPage(WizardState(), _service())
    on_screen_label = page._status_label

    page._on_worker_finished(OperationResult(success=True, log="ok", dataframe=None))

    assert page._status_label is on_screen_label
    assert on_screen_label.text() == "Query completed but no data returned"
    assert "green" in on_screen_label.styleSheet()


def test_query_page_status_label_updates_on_macro_failure():
    page = QueryPage(WizardState(), _service())
    on_screen_label = page._status_label

    page._on_worker_finished(OperationResult(success=False, log="macro failed"))

    assert page._status_label is on_screen_label
    assert on_screen_label.text() == "Failed"
    assert "red" in on_screen_label.styleSheet()


def test_query_page_status_label_updates_on_worker_failure():
    page = QueryPage(WizardState(), _service())
    on_screen_label = page._status_label

    page._on_worker_failed("timeout")

    assert page._status_label is on_screen_label
    assert on_screen_label.text() == "Worker error: timeout"
    assert "red" in on_screen_label.styleSheet()
