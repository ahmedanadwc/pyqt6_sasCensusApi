"""Tests for reusable UI widgets, specifically SasLogWidget."""

import sys
from PyQt6.QtWidgets import QApplication, QLabel
from PyQt6.QtCore import Qt

# Ensure a single QApplication instance exists for tests
app = QApplication.instance() or QApplication(sys.argv)

from pyqt6_sas_census.ui.widgets import SasLogWidget, status_label


def test_sas_log_widget_initial_state():
    widget = SasLogWidget(title="Test Log", expanded=True)
    assert widget.is_expanded() is True
    assert not widget._log.isHidden()
    assert "Lines: 0" in widget._line_count.text()
    assert widget.toPlainText() == ""


def test_sas_log_widget_collapse_and_expand():
    widget = SasLogWidget(expanded=True)
    assert widget.is_expanded() is True
    assert not widget._log.isHidden()

    # Collapse
    widget.set_expanded(False)
    assert widget.is_expanded() is False
    assert widget._log.isHidden()

    # Expand
    widget.set_expanded(True)
    assert widget.is_expanded() is True
    assert not widget._log.isHidden()


def test_sas_log_widget_toggle():
    widget = SasLogWidget(expanded=False)
    assert widget.is_expanded() is False
    assert widget._log.isHidden()

    widget.toggle()
    assert widget.is_expanded() is True
    assert not widget._log.isHidden()

    widget.toggle()
    assert widget.is_expanded() is False
    assert widget._log.isHidden()


def test_sas_log_widget_toggled_signal():
    widget = SasLogWidget(expanded=True)
    states = []
    widget.toggled.connect(states.append)

    widget.set_expanded(False)
    widget.set_expanded(True)

    assert states == [False, True]


def test_sas_log_widget_content_and_lines():
    widget = SasLogWidget()
    widget.set_log("Line 1\nLine 2\nLine 3")
    assert "Lines: 3" in widget._line_count.text()
    assert widget.toPlainText() == "Line 1\nLine 2\nLine 3"

    widget.append_log("Line 4")
    assert "Lines: 4" in widget._line_count.text()
    assert "Line 4" in widget.toPlainText()

    widget.clear()
    assert "Lines: 0" in widget._line_count.text()
    assert widget.toPlainText() == ""


def test_sas_log_widget_copy_to_clipboard():
    widget = SasLogWidget()
    widget.set_log("NOTE: Census API initialized successfully.")
    widget._copy_to_clipboard()

    clipboard = QApplication.clipboard()
    if clipboard:
        assert clipboard.text() == "NOTE: Census API initialized successfully."


def test_status_label_updates_existing_label_in_place():
    # Regression: status_label() used to *create and return* a new QLabel,
    # so callers doing `self._status_label = status_label(...)` replaced the
    # label that was actually on screen with an orphan never added to a
    # layout. It must now mutate the label it's given instead.
    label = QLabel("")

    status_label(label, True, "Success")
    assert label.text() == "Success"
    assert "green" in label.styleSheet()

    status_label(label, False, "Failed")
    assert label.text() == "Failed"
    assert "red" in label.styleSheet()
