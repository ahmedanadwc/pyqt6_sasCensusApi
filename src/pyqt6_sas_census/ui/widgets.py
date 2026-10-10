"""Reusable Qt widgets for the wizard."""

from pathlib import Path

import pandas as pd
from PyQt6.QtCore import (
    QRegularExpression,
    QSortFilterProxyModel,
    Qt,
    QTimer,
    pyqtSignal,
    pyqtSlot,
)
from PyQt6.QtGui import QColor, QFont, QSyntaxHighlighter, QTextCharFormat
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QComboBox,
    QFileDialog,
    QGridLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QPlainTextEdit,
    QPushButton,
    QSizePolicy,
    QTableView,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from pyqt6_sas_census.models.dataframe_model import DataFrameModel


class SasLogHighlighter(QSyntaxHighlighter):
    """Highlight SAS ERROR and WARNING lines in the log viewer."""

    _ERROR_RE = QRegularExpression(".*ERROR:.*")
    _WARNING_RE = QRegularExpression(".*WARNING:.*")

    def __init__(self, parent) -> None:
        super().__init__(parent)
        self.error_format = QTextCharFormat()
        self.error_format.setForeground(QColor("#d13c4e"))
        self.error_format.setFontWeight(QFont.Weight.Bold)

        self.warn_format = QTextCharFormat()
        self.warn_format.setForeground(QColor("#b45309"))
        self.warn_format.setFontWeight(QFont.Weight.Medium)

        self.norm_format = QTextCharFormat()
        self.norm_format.setForeground(QColor("#000000"))
        self.norm_format.setFontWeight(QFont.Weight.Normal)

    def highlightBlock(self, text: str) -> None:
        if self._ERROR_RE.match(text):
            self.setFormat(0, len(text), self.error_format)
        elif self._WARNING_RE.match(text):
            self.setFormat(0, len(text), self.warn_format)
        else:
            self.setFormat(0, len(text), self.norm_format)


class SasLogWidget(QWidget):
    """Collapsible/expandable read-only SAS log viewer with line count and header actions."""

    toggled = pyqtSignal(bool)

    def __init__(
        self,
        parent: QWidget | None = None,
        title: str = "SAS Log",
        expanded: bool = True,
    ) -> None:
        super().__init__(parent)
        self._title = title
        self._expanded = expanded
        self._line_count_val = 0

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)

        # Header with toggle button, title, copy action, and line count
        self._header = QWidget(self)
        self._header.setObjectName("sasLogHeader")
        header_layout = QHBoxLayout(self._header)
        header_layout.setContentsMargins(4, 2, 4, 2)
        header_layout.setSpacing(6)

        self._toggle_btn = QToolButton(self._header)
        self._toggle_btn.setCheckable(True)
        self._toggle_btn.setChecked(self._expanded)
        self._toggle_btn.setArrowType(
            Qt.ArrowType.DownArrow if self._expanded else Qt.ArrowType.RightArrow
        )
        self._toggle_btn.setToolTip("Collapse log" if self._expanded else "Expand log")
        self._toggle_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._toggle_btn.toggled.connect(self._on_toggle)

        self._title_btn = QPushButton(self._title, self._header)
        self._title_btn.setStyleSheet(
            "QPushButton {"
            "  border: none;"
            "  background: transparent;"
            "  font-weight: bold;"
            "  font-size: 12px;"
            "  text-align: left;"
            "  padding: 0px;"
            "}"
            "QPushButton:hover {"
            "  color: #0284c7;"
            "}"
        )
        self._title_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._title_btn.clicked.connect(self.toggle)

        self._line_count = QLabel("Lines: 0", self._header)
        self._line_count.setStyleSheet("color: gray; font-size: 11px;")

        self._copy_btn = QPushButton("Copy", self._header)
        self._copy_btn.setToolTip("Copy log to clipboard")
        self._copy_btn.setFixedHeight(20)
        self._copy_btn.setStyleSheet("font-size: 10px; padding: 1px 6px;")
        self._copy_btn.clicked.connect(self._copy_to_clipboard)

        self._clear_btn = QPushButton("Clear", self._header)
        self._clear_btn.setToolTip("Clear log text")
        self._clear_btn.setFixedHeight(20)
        self._clear_btn.setStyleSheet("font-size: 10px; padding: 1px 6px;")
        self._clear_btn.clicked.connect(self.clear)

        header_layout.addWidget(self._toggle_btn)
        header_layout.addWidget(self._title_btn)
        header_layout.addStretch()
        header_layout.addWidget(self._copy_btn)
        header_layout.addWidget(self._clear_btn)
        header_layout.addWidget(self._line_count)

        layout.addWidget(self._header)

        # Log content (collapsible)
        self._log = QPlainTextEdit(self)
        self._log.setReadOnly(True)
        self._log.setFont(QFont("Consolas", 9))
        self._log.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
        self._log.setMinimumHeight(100)
        self._log.setVisible(self._expanded)

        self._highlighter = SasLogHighlighter(self._log.document())

        layout.addWidget(self._log)
        self._update_size_policy()

    def _on_toggle(self, checked: bool) -> None:
        self._expanded = checked
        self._log.setVisible(checked)
        self._toggle_btn.setArrowType(
            Qt.ArrowType.DownArrow if checked else Qt.ArrowType.RightArrow
        )
        self._toggle_btn.setToolTip("Collapse log" if checked else "Expand log")
        if self._toggle_btn.isChecked() != checked:
            self._toggle_btn.setChecked(checked)
        self._update_size_policy()
        self.toggled.emit(checked)

    def _update_size_policy(self) -> None:
        if self._expanded:
            self.setSizePolicy(
                QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding
            )
        else:
            self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)

    def toggle(self) -> None:
        """Toggle collapsed/expanded state."""
        self.set_expanded(not self._expanded)

    def is_expanded(self) -> bool:
        """Return True if currently expanded."""
        return self._expanded

    def set_expanded(self, expanded: bool) -> None:
        """Programmatically expand or collapse the log viewer."""
        self._toggle_btn.setChecked(expanded)
        if self._expanded != expanded:
            self._on_toggle(expanded)

    def set_log(self, text: str) -> None:
        self._log.setPlainText(text)
        lines = text.count("\n") + (1 if text else 0)
        self._line_count_val = lines
        self._line_count.setText(f"Lines: {lines}")

    def append_log(self, text: str) -> None:
        self._log.appendPlainText(text)
        lines = self._log.toPlainText().count("\n") + 1
        self._line_count_val = lines
        self._line_count.setText(f"Lines: {lines}")

    def clear(self) -> None:
        self._log.clear()
        self._line_count_val = 0
        self._line_count.setText("Lines: 0")

    def toPlainText(self) -> str:
        return self._log.toPlainText()

    def _copy_to_clipboard(self) -> None:
        clipboard = QApplication.clipboard()
        if clipboard:
            clipboard.setText(self._log.toPlainText())


class CodePreviewWidget(QWidget):
    """Read-only SAS code editor with save action."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self._editor = QPlainTextEdit()
        self._editor.setReadOnly(True)
        self._editor.setFont(QFont("Consolas", 9))
        self._editor.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)

        #btn_layout = QHBoxLayout()
        #btn_layout.addStretch()
        #self._save_btn = QPushButton("Save .sas")
        #self._save_btn.clicked.connect(self._save_code)
        #btn_layout.addWidget(self._save_btn)

        layout.addWidget(self._editor)
        #layout.addLayout(btn_layout)

    def set_code(self, code: str) -> None:
        self._editor.setPlainText(code)

    def get_code(self) -> str:
        return self._editor.toPlainText()

    def _save_code(self) -> None:
        path, _ = QFileDialog.getSaveFileName(
            self, "Save SAS Code", "", "SAS Files (*.sas);;All Files (*)"
        )
        if path:
            Path(path).write_text(self._editor.toPlainText(), encoding="utf-8")


class CollapsibleCodeWidget(QWidget):
    """Collapsible/expandable read-only SAS code viewer with header actions."""

    toggled = pyqtSignal(bool)

    def __init__(
        self,
        parent: QWidget | None = None,
        title: str = "Generated SAS Code",
        expanded: bool = True,
    ) -> None:
        super().__init__(parent)
        self._title = title
        self._expanded = expanded

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)

        # Header with toggle button, title, and copy action
        self._header = QWidget(self)
        self._header.setObjectName("codePreviewHeader")
        header_layout = QHBoxLayout(self._header)
        header_layout.setContentsMargins(4, 2, 4, 2)
        header_layout.setSpacing(6)

        self._toggle_btn = QToolButton(self._header)
        self._toggle_btn.setCheckable(True)
        self._toggle_btn.setChecked(self._expanded)
        self._toggle_btn.setArrowType(
            Qt.ArrowType.DownArrow if self._expanded else Qt.ArrowType.RightArrow
        )
        self._toggle_btn.setToolTip(
            "Collapse code" if self._expanded else "Expand code"
        )
        self._toggle_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._toggle_btn.toggled.connect(self._on_toggle)

        self._title_btn = QPushButton(self._title, self._header)
        self._title_btn.setStyleSheet(
            "QPushButton {"
            "  border: none;"
            "  background: transparent;"
            "  font-weight: bold;"
            "  font-size: 12px;"
            "  text-align: left;"
            "  padding: 0px;"
            "}"
            "QPushButton:hover {"
            "  color: #0284c7;"
            "}"
        )
        self._title_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._title_btn.clicked.connect(self.toggle)

        self._copy_btn = QPushButton("Copy", self._header)
        self._copy_btn.setToolTip("Copy code to clipboard")
        self._copy_btn.setFixedHeight(20)
        self._copy_btn.setStyleSheet("font-size: 10px; padding: 1px 6px;")
        self._copy_btn.clicked.connect(self._copy_to_clipboard)

        self._save_btn = QPushButton("Save .sas", self._header)
        self._save_btn.setToolTip("Save code to file")
        self._save_btn.setFixedHeight(20)
        self._save_btn.setStyleSheet("font-size: 10px; padding: 1px 6px;")
        self._save_btn.clicked.connect(self._save_code)

        header_layout.addWidget(self._toggle_btn)
        header_layout.addWidget(self._title_btn)
        header_layout.addStretch()
        header_layout.addWidget(self._copy_btn)
        header_layout.addWidget(self._save_btn)

        layout.addWidget(self._header)

        # Code content (collapsible)
        self._code_preview = CodePreviewWidget()
        self._code_preview.setVisible(self._expanded)

        layout.addWidget(self._code_preview)
        self._update_size_policy()

    def _on_toggle(self, checked: bool) -> None:
        self._expanded = checked
        self._code_preview.setVisible(checked)
        self._toggle_btn.setArrowType(
            Qt.ArrowType.DownArrow if checked else Qt.ArrowType.RightArrow
        )
        self._toggle_btn.setToolTip("Collapse code" if checked else "Expand code")
        if self._toggle_btn.isChecked() != checked:
            self._toggle_btn.setChecked(checked)
        self._update_size_policy()
        self.toggled.emit(checked)

    def _update_size_policy(self) -> None:
        if self._expanded:
            self.setSizePolicy(
                QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding
            )
        else:
            self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)

    def toggle(self) -> None:
        """Toggle collapsed/expanded state."""
        self.set_expanded(not self._expanded)

    def is_expanded(self) -> bool:
        """Return True if currently expanded."""
        return self._expanded

    def set_expanded(self, expanded: bool) -> None:
        """Programmatically expand or collapse the code viewer."""
        self._toggle_btn.setChecked(expanded)
        if self._expanded != expanded:
            self._on_toggle(expanded)

    def set_code(self, code: str) -> None:
        self._code_preview.set_code(code)

    def get_code(self) -> str:
        return self._code_preview.get_code()

    def _copy_to_clipboard(self) -> None:
        clipboard = QApplication.clipboard()
        if clipboard:
            clipboard.setText(self._code_preview.get_code())

    def _save_code(self) -> None:
        self._code_preview._save_code()


class DataFrameWidget(QWidget):
    """Table view with pandas DataFrameModel and row selection."""

    row_selected = pyqtSignal(dict)
    rows_selected = pyqtSignal(list)

    def __init__(
        self,
        parent: QWidget | None = None,
        auto_resize_columns: bool = False,
        multi_select: bool = False,
    ) -> None:
        super().__init__(parent)
        self._auto_resize_columns = auto_resize_columns
        self._multi_select = multi_select
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Filter bar - filters across all columns (case-insensitive substring)
        filter_layout = QHBoxLayout()
        filter_layout.setContentsMargins(0, 0, 0, 0)
        filter_label = QLabel("Filter:")
        self._filter_edit = QLineEdit()
        self._filter_edit.setPlaceholderText("Type to filter rows...")
        self._filter_edit.setClearButtonEnabled(True)
        self._filter_edit.textChanged.connect(self._on_filter_changed)
        filter_layout.addWidget(filter_label)
        filter_layout.addWidget(self._filter_edit, 1)

        # Selection mode toggle (only shown if multi_select is True)
        if self._multi_select:
            self._select_mode_label = QLabel("Mode:")
            self._select_mode_combo = QComboBox()
            self._select_mode_combo.addItems(["Single Select", "Multi Select"])
            self._select_mode_combo.setCurrentText("Multi Select")
            self._select_mode_combo.currentTextChanged.connect(
                self._on_select_mode_changed
            )
            filter_layout.addWidget(self._select_mode_label)
            filter_layout.addWidget(self._select_mode_combo)

            # Clear selection button for multi-select
            self._clear_selection_btn = QPushButton("Clear Selection")
            self._clear_selection_btn.clicked.connect(self.clear_selection)
            filter_layout.addWidget(self._clear_selection_btn)

        layout.addLayout(filter_layout)

        self._view = QTableView()
        self._view.setAlternatingRowColors(True)
        self._view.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        # Default to multi-select if enabled, otherwise single
        if self._multi_select:
            self._view.setSelectionMode(QAbstractItemView.SelectionMode.MultiSelection)
        else:
            self._view.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self._view.setSortingEnabled(True)
        self._view.horizontalHeader().setStretchLastSection(True)
        self._view.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Interactive
        )
        self._view.horizontalHeader().setSortIndicatorShown(True)

        self._model = DataFrameModel()
        self._proxy = QSortFilterProxyModel(self)
        self._proxy.setSourceModel(self._model)
        self._proxy.setFilterCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self._proxy.setFilterKeyColumn(-1)
        self._view.setModel(self._proxy)

        layout.addWidget(self._view)

    def set_multi_select(self, enabled: bool) -> None:
        """Enable or disable multi-select mode."""
        self._multi_select = enabled
        if enabled:
            self._view.setSelectionMode(QAbstractItemView.SelectionMode.MultiSelection)
        else:
            self._view.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)

    def set_dataframe(self, df: pd.DataFrame) -> None:
        self._model.set_dataframe(df)
        if self._auto_resize_columns:
            self.resize_columns_to_contents()
        # Connect selection signal after dataframe is set to avoid issues with empty model
        try:
            self._view.selectionModel().selectionChanged.disconnect()
        except RuntimeError:
            pass  # Signal was not connected
        self._view.selectionModel().selectionChanged.connect(self._on_selection_changed)

    def resize_columns_to_contents(self) -> None:
        """Resize all columns to fit their content."""
        self._view.resizeColumnsToContents()
        # Ensure last section still stretches if needed
        self._view.horizontalHeader().setStretchLastSection(True)

    def is_empty(self) -> bool:
        """Return True when no source rows are loaded."""
        return self._model.rowCount() == 0

    def source_row_count(self) -> int:
        """Return the number of source (unfiltered) rows."""
        return self._model.rowCount()

    def source_row_dict(self, row: int) -> dict:
        """Return the source row at *row* as a dict."""
        return self._model.row_dict(row)

    def select_row(self, source_row: int) -> bool:
        """Select the view row for *source_row*; return False if hidden/invalid."""
        source_index = self._model.index(source_row, 0)
        if not source_index.isValid():
            return False
        proxy_index = self._proxy.mapFromSource(source_index)
        if not proxy_index.isValid():
            return False
        self._view.selectRow(proxy_index.row())
        return True

    def clear_filter(self) -> None:
        """Clear the filter text (reveals all rows)."""
        self._filter_edit.clear()

    def clear_selection(self) -> None:
        """Clear all row selections."""
        self._view.clearSelection()

    def selected_rows(self) -> list[dict]:
        """Return all selected rows as a list of dicts."""
        indexes = self._view.selectionModel().selectedRows()
        rows = []
        for idx in indexes:
            source = self._proxy.mapToSource(idx)
            if source.isValid():
                rows.append(self._model.row_dict(source.row()))
        return rows

    def _on_filter_changed(self, text: str) -> None:
        self._proxy.setFilterFixedString(text.strip())

    def _on_select_mode_changed(self, text: str) -> None:
        if text == "Multi Select":
            self._view.setSelectionMode(QAbstractItemView.SelectionMode.MultiSelection)
        else:
            self._view.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)

    @pyqtSlot()
    def _on_selection_changed(self) -> None:
        # Defer the actual work to avoid issues during selection change
        QTimer.singleShot(0, self._emit_selection_signals)

    def _emit_selection_signals(self) -> None:
        # Emit single row selection (for backwards compatibility)
        rows = self.selected_rows()
        if rows:
            self.row_selected.emit(rows[0])

        # Emit all selected rows (for multi-select)
        if self._multi_select:
            self.rows_selected.emit(rows)


def status_label(label: QLabel, success: bool, message: str) -> None:
    """Update an existing status label's text and success/failure color."""
    label.setText(message)
    if success:
        label.setStyleSheet("color: green; font-weight: bold;")
    else:
        label.setStyleSheet("color: red; font-weight: bold;")


def make_form_grid() -> QGridLayout:
    """Grid with two label/field column pairs (label, field, label, field)."""
    grid = QGridLayout()
    grid.setColumnStretch(1, 1)
    grid.setColumnStretch(3, 1)
    grid.setHorizontalSpacing(10)
    return grid


def add_form_field(
    grid: QGridLayout, row: int, col: int, label: str, field, span: int = 1
) -> None:
    """Place label + field in column pair `col` (0 or 1); span=2 uses the full row."""
    grid.addWidget(QLabel(label), row, col * 2, Qt.AlignmentFlag.AlignTop)
    cols = 3 if span == 2 else 1
    if isinstance(field, QWidget):
        grid.addWidget(field, row, col * 2 + 1, 1, cols)
    else:
        grid.addLayout(field, row, col * 2 + 1, 1, cols)
