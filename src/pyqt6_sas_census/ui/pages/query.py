"""Query page for the SAS Census wizard."""

from typing import Optional
from PyQt6.QtCore import pyqtSlot
from PyQt6.QtWidgets import (
    QWizardPage,
    QVBoxLayout,
    QHBoxLayout,
    QFormLayout,
    QLineEdit,
    QSpinBox,
    QPushButton,
    QLabel,
    QMessageBox,
)

from pyqt6_sas_census.ui.widgets import (
    SasLogWidget,
    CodePreviewWidget,
    DataFrameWidget,
    status_label,
)
from pyqt6_sas_census.services.workers import SasWorker
from pyqt6_sas_census.services.sas_service import SasService, OperationResult
from pyqt6_sas_census.sas.programs import build_query_code
from pyqt6_sas_census.state import WizardState
from PyQt6.QtWidgets import QProgressBar


class QueryPage(QWizardPage):
    """Page 5: Query Builder - build and run Census API query with variable chunking."""

    def __init__(self, state: WizardState, service: SasService, parent=None):
        super().__init__(parent)
        self.setTitle("Query Builder")
        self.setSubTitle(
            "Build and execute a Census Data API query with automatic variable chunking."
        )
        self._state = state
        self._service = service
        self._worker: Optional[SasWorker] = None

        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)

        # Inputs
        form = QFormLayout()
        self._endpoint_edit = QLineEdit()
        self._endpoint_edit.setPlaceholderText(
            "https://api.census.gov/data/2000/dec/sf1?"
        )
        form.addRow("Endpoint:", self._endpoint_edit)

        self._get_clause_edit = QLineEdit("get=NAME")
        form.addRow("GET Clause:", self._get_clause_edit)

        self._for_clause_edit = QLineEdit("for=state:*")
        form.addRow("FOR Clause:", self._for_clause_edit)

        self._in_clause_edit = QLineEdit("in=")
        form.addRow("IN Clause:", self._in_clause_edit)

        self._dataset_id_edit = QLineEdit("_114_dec_2000")
        form.addRow("Dataset Unique ID:", self._dataset_id_edit)

        self._out_dataset_edit = QLineEdit("work.sf1_response")
        form.addRow("Output Dataset:", self._out_dataset_edit)

        self._api_key_ref_edit = QLineEdit("&g_apiKey")
        form.addRow("API Key Reference:", self._api_key_ref_edit)

        self._max_var_count_spin = QSpinBox()
        self._max_var_count_spin.setRange(5, 50)
        self._max_var_count_spin.setValue(50)
        form.addRow("Max Variables per Chunk:", self._max_var_count_spin)

        layout.addLayout(form)

        # Code preview
        self._code_preview = CodePreviewWidget()
        layout.addWidget(QLabel("Generated SAS Code:"))
        layout.addWidget(self._code_preview)

        # Buttons
        btn_layout = QHBoxLayout()
        self._run_btn = QPushButton("Run Query")
        self._run_btn.clicked.connect(self._on_run)
        btn_layout.addWidget(self._run_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)

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

        # Result dataframe
        self._df_widget = DataFrameWidget()
        layout.addWidget(QLabel("Query Results:"))
        layout.addWidget(self._df_widget)

    def initializePage(self) -> None:
        super().initializePage()
        # Pre-fill from state
        if self._state.step4_selected_endpoint:
            self._endpoint_edit.setText(self._state.step4_selected_endpoint)
        if self._state.dataset_unique_id:
            self._dataset_id_edit.setText(self._state.dataset_unique_id)
        self._refresh_code_preview()

    def _refresh_code_preview(self) -> None:
        code = build_query_code(
            self._endpoint_edit.text().strip()
            or "https://api.census.gov/data/2000/dec/sf1?",
            self._get_clause_edit.text().strip() or "get=NAME",
            self._for_clause_edit.text().strip() or "for=state:*",
            self._in_clause_edit.text().strip() or "in=",
            self._dataset_id_edit.text().strip() or "_114_dec_2000",
            self._out_dataset_edit.text().strip() or "work.sf1_response",
            self._api_key_ref_edit.text().strip() or "&g_apiKey",
            self._max_var_count_spin.value(),
        )
        self._code_preview.set_code(code)

    def _on_run(self) -> None:
        endpoint = self._endpoint_edit.text().strip()
        dataset_id = self._dataset_id_edit.text().strip()
        if not endpoint:
            QMessageBox.warning(
                self, "Missing Endpoint", "Please enter the Census API endpoint."
            )
            return
        if not dataset_id:
            QMessageBox.warning(
                self, "Missing Dataset ID", "Please enter a dataset unique ID."
            )
            return

        self._refresh_code_preview()
        self._run_btn.setEnabled(False)

        self._run_worker(
            lambda: self._service.submit_query(
                api_base_url=endpoint,
                get_clause=self._get_clause_edit.text().strip(),
                for_clause=self._for_clause_edit.text().strip(),
                in_clause=self._in_clause_edit.text().strip(),
                dataset_id=dataset_id,
                out_dataset=self._out_dataset_edit.text().strip(),
                api_key_ref=self._api_key_ref_edit.text().strip(),
                max_var_count=self._max_var_count_spin.value(),
            )
        )

    def _run_worker(self, func) -> None:
        from PyQt6.QtCore import QThread

        self._progress.setVisible(True)
        self._run_btn.setEnabled(False)
        self._worker_thread = QThread()
        self._worker = SasWorker(func)
        self._worker.moveToThread(self._worker_thread)
        self._worker_thread.started.connect(self._worker.run)
        self._worker.finished.connect(self._on_worker_finished)
        self._worker.failed.connect(self._on_worker_failed)
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
            self._status_label, result.success, "Success" if result.success else "Failed"
        )

        if result.success:
            self._state.step5_inputs = {
                "api_base_url": self._endpoint_edit.text().strip(),
                "get_clause": self._get_clause_edit.text().strip(),
                "for_clause": self._for_clause_edit.text().strip(),
                "in_clause": self._in_clause_edit.text().strip(),
                "dataset_id": self._dataset_id_edit.text().strip(),
                "out_dataset": self._out_dataset_edit.text().strip(),
                "api_key_ref": self._api_key_ref_edit.text().strip(),
                "max_var_count": self._max_var_count_spin.value(),
            }
            self._state.step5_result = {"success": True, "log": result.log}
            if result.dataframe is not None:
                self._state.step5_dataframe = result.dataframe
                self._df_widget.set_dataframe(result.dataframe)
            else:
                status_label(
                    self._status_label, True, "Query completed but no data returned"
                )
        else:
            self._state.step5_result = {"success": False, "log": result.log}

    @pyqtSlot(str)
    def _on_worker_failed(self, error: str) -> None:
        self._progress.setVisible(False)
        self._run_btn.setEnabled(True)
        self._log.append_log(f"Worker error: {error}")
        status_label(self._status_label, False, f"Worker error: {error}")
        self._state.step5_result = {"success": False, "log": error}

    def isComplete(self) -> bool:
        return bool(
            self._state.step5_result and self._state.step5_result.get("success")
        )
