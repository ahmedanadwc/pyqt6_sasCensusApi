"""Catalog page for the SAS Census wizard."""

from numbers import Integral, Real

from PyQt6.QtCore import pyqtSlot
from PyQt6.QtWidgets import (
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QTextEdit,
    QVBoxLayout,
    QWidget,
    QWizardPage,
)

from pyqt6_sas_census import config as cfg
from pyqt6_sas_census.sas.programs import build_collect_catalog_code
from pyqt6_sas_census.services.sas_service import OperationResult, SasService
from pyqt6_sas_census.services.workers import SasWorker
from pyqt6_sas_census.state import WizardState
from pyqt6_sas_census.ui.widgets import (
    CollapsibleCodeWidget,
    DataFrameWidget,
    SasLogWidget,
    add_form_field,
    make_form_grid,
    status_label,
)

# Preview columns from the source implementation (matches KEEP option in ds_opts)
CATALOG_PREVIEW_COLUMNS = [
    "_rowid_",
    "ds_unique_id",
    "baseurl",
    "c_vintage",
    "title",
    "description",
    "modified",
    "Spatial",
    "microdata_i",
]


class CatalogPage(QWizardPage):
    """Page 2: Collect All Datasets - run getAllDataSets and preview catalog."""

    def __init__(self, state: WizardState, service: SasService, parent=None):
        super().__init__(parent)
        self.setTitle("Collect All Datasets")
        self.setSubTitle("Retrieve the full Census dataset catalog into a SAS dataset.")
        self._state = state
        self._service = service
        self._worker: SasWorker | None = None

        self._setup_ui()
        self._refresh_code_preview()

    def _setup_ui(self) -> None:
        # Scroll area keeps the page's minimum size small so the wizard never
        # grows taller than the display; content scrolls instead.
        page_layout = QVBoxLayout(self)
        page_layout.setContentsMargins(0, 0, 0, 0)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        content = QWidget()
        content.setMinimumHeight(1100)
        layout = QVBoxLayout(content)
        scroll.setWidget(content)
        page_layout.addWidget(scroll)

        # --- Catalog inputs: full-width form, fields in two columns ---
        input_group = QGroupBox("Catalog Parameters")
        input_layout = QVBoxLayout(input_group)
        grid = make_form_grid()

        self._out_lib_edit = QLineEdit(cfg.DEFAULT_OUT_LIB)
        add_form_field(grid, 0, 0, "Output Library:", self._out_lib_edit)

        self._out_ds_edit = QLineEdit(cfg.DEFAULT_OUT_DS)
        add_form_field(grid, 0, 1, "Output Dataset:", self._out_ds_edit)

        self._data_json_url_edit = QLineEdit(cfg.DEFAULT_DATA_JSON_URL)
        add_form_field(grid, 1, 0, "Catalog URL:", self._data_json_url_edit)

        self._report_path_edit = QLineEdit("&g_outputRoot")
        add_form_field(grid, 1, 1, "Report Path:", self._report_path_edit)

        input_layout.addLayout(grid)

        # Run button
        btn_layout = QHBoxLayout()
        self._run_btn = QPushButton("Run Catalog Collection")
        self._run_btn.clicked.connect(self._on_run)
        btn_layout.addStretch()
        btn_layout.addWidget(self._run_btn)
        input_layout.addLayout(btn_layout)

        layout.addWidget(input_group)

        # Progress bar (indeterminate)
        self._progress = QProgressBar()
        self._progress.setRange(0, 0)
        self._progress.setVisible(False)
        self._progress.setTextVisible(False)
        self._progress.setFixedHeight(4)
        layout.addWidget(self._progress)

        # Status
        self._status_label = QLabel("")
        layout.addWidget(self._status_label)

        # Log
        self._log = SasLogWidget()
        layout.addWidget(self._log)

        # Generated SAS code - collapsible, below the log
        self._code_preview = CollapsibleCodeWidget(
            title="Generated SAS Code", expanded=False
        )
        layout.addWidget(self._code_preview)

        # Dataframe preview
        self._df_widget = DataFrameWidget(auto_resize_columns=True)
        self._df_widget.setMinimumHeight(250)
        self._df_widget.row_selected.connect(self._on_row_selected)
        layout.addWidget(QLabel("Catalog Preview:"))
        layout.addWidget(self._df_widget, 1)

        # Selected row details - two-column readonly layout
        details_group = QGroupBox("Selected Row Details")
        details_layout = QVBoxLayout(details_group)
        details_grid = make_form_grid()

        self._detail_title = QLineEdit()
        self._detail_title.setPlaceholderText("Select a row in the table above")
        self._detail_vintage = QLineEdit()
        self._detail_ds_id = QLineEdit()
        self._detail_row_id = QLineEdit()
        self._detail_baseurl = QLineEdit()
        self._detail_modified = QLineEdit()
        self._detail_spatial = QLineEdit()
        for edit in (
            self._detail_title,
            self._detail_vintage,
            self._detail_ds_id,
            self._detail_row_id,
            self._detail_baseurl,
            self._detail_modified,
            self._detail_spatial,
        ):
            edit.setReadOnly(True)

        # Left column: identity fields
        add_form_field(details_grid, 0, 0, "Title:", self._detail_title)
        add_form_field(details_grid, 1, 0, "Vintage:", self._detail_vintage)
        add_form_field(details_grid, 2, 0, "Dataset Unique ID:", self._detail_ds_id)
        add_form_field(details_grid, 3, 0, "Row ID:", self._detail_row_id)
        # Right column: location/meta fields
        add_form_field(details_grid, 0, 1, "Base URL:", self._detail_baseurl)
        add_form_field(details_grid, 1, 1, "Modified:", self._detail_modified)
        add_form_field(details_grid, 2, 1, "Spatial:", self._detail_spatial)

        # Description spans the full width and gets extra height
        self._detail_description = QTextEdit()
        self._detail_description.setReadOnly(True)
        self._detail_description.setPlaceholderText(
            "Description of the selected dataset"
        )
        self._detail_description.setLineWrapMode(QTextEdit.LineWrapMode.WidgetWidth)
        self._detail_description.setMinimumHeight(160)
        add_form_field(
            details_grid, 4, 0, "Description:", self._detail_description, span=2
        )

        details_layout.addLayout(details_grid)
        layout.addWidget(details_group)

    def _refresh_code_preview(self) -> None:
        code = build_collect_catalog_code(
            self._out_lib_edit.text().strip() or "APILIB",
            self._out_ds_edit.text().strip() or "_API_ALL_DATA",
            self._data_json_url_edit.text().strip()
            or "https://api.census.gov/data.json",
            self._report_path_edit.text().strip() or "&g_outputRoot",
        )
        self._code_preview.set_code(code)

    def _on_run(self) -> None:
        self._refresh_code_preview()
        self._run_btn.setEnabled(False)
        out_lib = self._out_lib_edit.text().strip() or "APILIB"
        out_ds = self._out_ds_edit.text().strip() or "_API_ALL_DATA"
        data_json_url = (
            self._data_json_url_edit.text().strip()
            or "https://api.census.gov/data.json"
        )
        report_path = self._report_path_edit.text().strip() or "&g_outputRoot"
        self._run_worker(
            lambda: self._service.collect_catalog(
                out_lib=out_lib,
                out_ds=out_ds,
                data_json_url=data_json_url,
                report_path=report_path,
            )
        )

    def _run_worker(self, func, finished_handler=None, failed_handler=None) -> None:
        if not self._service.try_begin_operation():
            (failed_handler or self._on_worker_failed)(
                "Another SAS operation is already in progress."
            )
            return

        from PyQt6.QtCore import QThread

        self._progress.setVisible(True)
        self._run_btn.setEnabled(False)
        self._worker_thread = QThread()
        self._worker = SasWorker(self._service.run_reserved_operation, func)
        self._worker.moveToThread(self._worker_thread)
        self._worker_thread.started.connect(self._worker.run)
        self._worker.finished.connect(finished_handler or self._on_worker_finished)
        self._worker.failed.connect(failed_handler or self._on_worker_failed)
        self._worker.finished.connect(self._worker_thread.quit)
        self._worker.failed.connect(self._worker_thread.quit)
        self._worker.finished.connect(self._worker.deleteLater)
        self._worker.failed.connect(self._worker.deleteLater)
        self._worker_thread.finished.connect(self._worker_thread.deleteLater)
        self._worker_thread.start()

    @pyqtSlot(object)
    def _on_worker_finished(self, result: OperationResult) -> None:
        self._progress.setVisible(False)
        self._run_btn.setEnabled(True)
        self._log.set_log(result.log)
        status_label(
            self._status_label,
            result.success,
            "Success" if result.success else "Failed",
        )

        if result.success:
            self._state.step2_inputs = {
                "out_lib": self._out_lib_edit.text().strip(),
                "out_ds": self._out_ds_edit.text().strip(),
                "data_json_url": self._data_json_url_edit.text().strip(),
                "report_path": self._report_path_edit.text().strip(),
            }
            self._state.step2_result = {"success": True, "log": result.log}
            self._state.step2_lib = self._out_lib_edit.text().strip() or "APILIB"
            self._state.step2_dataset = (
                self._out_ds_edit.text().strip() or "_API_ALL_DATA"
            )

            if result.dataframe is not None:
                self._state.step2_dataframe = result.dataframe
                self._df_widget.set_dataframe(result.dataframe)
                # Fresh run invalidates any previous selection - user must reselect
                self._state.selected_catalog_row = None
                self._state.selected_catalog_index = None
                self._state.selected_row_id = None
                self._state.dataset_unique_id = None
                self._clear_details()
                self.completeChanged.emit()
            else:
                # Try to fetch existing dataset
                self._try_fetch_existing()
                self._reselect_previous_row()
                # Macro succeeded — allow progression even without data
                self.completeChanged.emit()

    @pyqtSlot(str)
    def _on_worker_failed(self, error: str) -> None:
        self._progress.setVisible(False)
        self._run_btn.setEnabled(True)
        self._log.append_log(f"Worker error: {error}")
        status_label(self._status_label, False, f"Worker error: {error}")
        self._state.step2_result = {"success": False, "log": error}
        self.completeChanged.emit()

    def _try_fetch_existing(self) -> None:
        lib = self._state.step2_lib
        ds = self._state.step2_dataset
        df = self._state.step2_dataframe
        if df is not None:
            self._df_widget.set_dataframe(df)
            self._clear_details()
            return

        self._run_btn.setEnabled(False)
        self._progress.setVisible(True)

        self._run_worker(
            lambda: self._service.backend.fetch_dataframe(
                ds,
                lib,
                ds_opts={
                    "KEEP": "_rowid_ ds_unique_id baseurl c_vintage title description modified Spatial microdata_i"
                },
            ),
            finished_handler=self._on_existing_catalog_loaded,
            failed_handler=self._on_existing_catalog_failed,
        )

    @pyqtSlot(object)
    def _on_existing_catalog_loaded(self, dataframe) -> None:
        self._progress.setVisible(False)
        self._run_btn.setEnabled(True)
        if dataframe is not None:
            self._state.step2_dataframe = dataframe
            self._df_widget.set_dataframe(dataframe)
            self._clear_details()
            self._reselect_previous_row()
            self.completeChanged.emit()

    @pyqtSlot(str)
    def _on_existing_catalog_failed(self, error: str) -> None:
        self._progress.setVisible(False)
        self._run_btn.setEnabled(True)
        self._log.append_log(f"Worker error: {error}")
        status_label(self._status_label, False, f"Worker error: {error}")

    @staticmethod
    def _format_value(value) -> str:
        """Stringify a value; whole-number floats (3.0) are shown as integers (3)."""
        if (
            isinstance(value, Real)
            and not isinstance(value, (Integral, bool))
            and value == value  # not NaN
            and value not in (float("inf"), float("-inf"))
            and float(value).is_integer()
        ):
            return str(int(value))
        return str(value)

    @staticmethod
    def _row_value(row: dict, *candidates: str) -> str:
        """Return the first matching value, case-insensitively, as a string."""
        lowered = {str(k).lower(): v for k, v in row.items()}
        for key in candidates:
            value = lowered.get(key.lower())
            if value is not None and str(value) != "nan":
                return CatalogPage._format_value(value)
        return ""

    def _populate_details(self, row: dict) -> None:
        self._detail_title.setText(
            self._row_value(row, "title", "c_title", "TITLE", "C_TITLE")
        )
        self._detail_vintage.setText(
            self._row_value(row, "c_vintage", "C_VINTAGE", "vintage", "VINTAGE")
        )
        self._detail_ds_id.setText(self._row_value(row, "ds_unique_id", "DS_UNIQUE_ID"))
        self._detail_row_id.setText(
            self._row_value(row, "_ROWID_", "_rowid_", "row_id", "ROW_ID")
        )
        self._detail_baseurl.setText(
            self._row_value(row, "baseurl", "BASEURL", "accessURL", "endpoint")
        )
        self._detail_modified.setText(self._row_value(row, "modified", "MODIFIED"))
        self._detail_spatial.setText(
            self._row_value(
                row, "Spatial", "SPATIAL", "spatial", "microdata_is", "microdata_i"
            )
        )
        self._detail_description.setPlainText(
            self._row_value(row, "description", "DESCRIPTION", "c_description")
        )

    def _clear_details(self) -> None:
        self._detail_title.clear()
        self._detail_vintage.clear()
        self._detail_ds_id.clear()
        self._detail_row_id.clear()
        self._detail_baseurl.clear()
        self._detail_modified.clear()
        self._detail_spatial.clear()
        self._detail_description.clear()

    def _on_row_selected(self, row: dict) -> None:
        self._state.selected_catalog_row = row
        self._state.selected_catalog_index = row.get("_ROWID_", row.get("_rowid_"))
        self._state.selected_row_id = self._format_value(
            row.get("_ROWID_", row.get("_rowid_", row.get("row_id", "")))
        )
        self._state.dataset_unique_id = row.get("ds_unique_id", row.get("DS_UNIQUE_ID"))
        # Also save BaseURL for auto-populating query builder
        self._state.step3_selected_endpoint = row.get(
            "baseurl", row.get("BASEURL", row.get("BaseURL", row.get("baseurl", "")))
        )
        self._populate_details(row)
        self.completeChanged.emit()

    def _reselect_previous_row(self) -> None:
        """Re-highlight the previously selected row after returning to the page."""
        prev = self._state.selected_catalog_row
        if not isinstance(prev, dict) or self._df_widget.is_empty():
            return
        prev_id = self._row_value(prev, "_ROWID_", "_rowid_", "row_id", "ROW_ID")
        prev_ds = self._row_value(prev, "ds_unique_id", "DS_UNIQUE_ID")
        if not prev_id and not prev_ds:
            return
        for i in range(self._df_widget.source_row_count()):
            cur = self._df_widget.source_row_dict(i)
            cur_id = self._row_value(cur, "_ROWID_", "_rowid_", "row_id", "ROW_ID")
            cur_ds = self._row_value(cur, "ds_unique_id", "DS_UNIQUE_ID")
            if prev_id and cur_id and prev_id == cur_id:
                if self._df_widget.select_row(i):
                    self._populate_details(cur)
                return
            if prev_ds and cur_ds and prev_ds == cur_ds and not prev_id:
                if self._df_widget.select_row(i):
                    self._populate_details(cur)
                return

    def initializePage(self) -> None:
        super().initializePage()
        # Try to fetch existing dataset on page entry
        if (
            self._state.sas_connected
            and self._state.environment_ready
            and self._state.step2_result is None
        ):
            self._try_fetch_existing()
            if self._state.step2_dataframe is not None:
                self._df_widget.set_dataframe(self._state.step2_dataframe)
        elif self._state.step2_dataframe is not None and self._df_widget.is_empty():
            self._df_widget.set_dataframe(self._state.step2_dataframe)
        self._reselect_previous_row()

    def isComplete(self) -> bool:
        # Complete if a SAS run succeeded, OR if a pre-existing
        # / cached dataframe is already available. The user should
        # not need to re-run SAS every time they open this page.
        sas_succeeded = (
            self._state.step2_result is not None
            and self._state.step2_result.get("success")
        )
        has_cached_data = self._state.step2_dataframe is not None
        has_selection = self._state.selected_catalog_row is not None
        return bool((sas_succeeded or has_cached_data) and has_selection)
