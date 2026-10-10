"""Regression tests for ProfileQueryPage query-field handling."""

import sys

import pandas as pd
from PyQt6.QtWidgets import QApplication

app = QApplication.instance() or QApplication(sys.argv)

from pyqt6_sas_census.services.sas_service import SasService
from pyqt6_sas_census.state import WizardState
from pyqt6_sas_census.ui.pages.connection import ConnectionPage
from pyqt6_sas_census.ui.pages.profile_query import ProfileQueryPage


class _Backend:
    is_connected = False

    def fetch_dataframe(self, *args, **kwargs):
        return None


def _page(state=None):
    page = ProfileQueryPage(state or WizardState(), SasService(_Backend()))
    page._try_load_existing_profile = lambda: None
    return page


def test_switching_dataset_keeps_saved_for_and_in_clauses():
    state = WizardState()
    page = _page(state)
    state.dataset_unique_id = "A"
    page._get_clause_edit.setPlainText("get=A1")
    page._for_clause_edit.setText("for=county:*")
    page._in_clause_edit.setText("in=state:09")

    state.step3_query_fields["B"] = {"get": "get=B1", "for": "for=state:*", "in": "in="}
    state.dataset_unique_id = "B"
    page.initializePage()

    assert state.step3_query_fields["B"] == {
        "get": "get=B1",
        "for": "for=state:*",
        "in": "in=",
    }
    assert page._for_clause_edit.text() == "for=state:*"
    assert page._in_clause_edit.text() == "in="


def test_query_args_apply_defaults_used_by_preview_and_run():
    page = _page()
    page._for_clause_edit.setText("")
    page._out_dataset_edit.setText("")
    page._api_key_ref_edit.setText("")

    args = page._query_args()

    assert args["for_clause"] == "for=state:*"
    assert args["out_dataset"] == "work.sf1_response"
    assert args["api_key_ref"] == "&g_apiKey"


def test_profile_tabs_cleared_when_new_dataset_has_no_tables():
    page = _page()
    df = pd.DataFrame({"Name": ["X"]})
    page._populate_profile_tabs({"Variables": ("T_VARS", df)})
    assert not page._profile_tab_widgets["Variables"].is_empty()

    page._on_profile_tables_loaded({})

    assert page._profile_tab_widgets["Variables"].is_empty()


def test_blank_config_file_is_passed_through_to_clear_default():
    calls = []

    class Service:
        def try_begin_operation(self):
            return True

        def run_reserved_operation(self, op):
            return op()

        def connect(self, cfgname, cfgfile):
            calls.append((cfgname, cfgfile))

    page = ConnectionPage(WizardState(), Service())
    page._cfgfile_edit.setText("")
    page._cfgname_combo.setEditText("oda")
    page._run_worker = lambda func: func()

    page._on_connect()

    assert calls == [("oda", "")]
