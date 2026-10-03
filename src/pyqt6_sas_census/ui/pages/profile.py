"""Profile page for the SAS Census wizard."""

from typing import Optional
from PyQt6.QtCore import pyqtSlot
from PyQt6.QtWidgets import (
    QWizardPage,
    QVBoxLayout,
    QHBoxLayout,
    QFormLayout,
    QLineEdit,
    QPushButton,
    QLabel,
    QMessageBox,
    QGroupBox,
    QProgressBar,
)

from pyqt6_sas_census.ui.widgets import SasLogWidget, CodePreviewWidget, status_label
from pyqt6_sas_census.services.workers import SasWorker
from pyqt6_sas_census.services.sas_service import SasService, OperationResult
from pyqt6_sas_census.sas.programs import build_profile_code
from pyqt6_sas_census.state import WizardState


class ProfilePage(QWizardPage):
    """Page 3: Dataset Profile - run getDsFullInfo for selected catalog row."""

    def __init__(self, state: WizardState, service: SasService, parent=None):
        super().__init__(parent)
        self.setTitle("Dataset Profile")
        self.setSubTitle(
            "Generate a complete profile for the selected dataset from the catalog."
        )
        self._state = state
        self._service = service
        self._worker: Optional[SasWorker] = None

        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)

        # Two-column layout
        two_col_layout = QHBoxLayout()
        two_col_layout.setSpacing(15)

        # --- Left Column: Profile Inputs ---
        input_group = QGroupBox("Profile Parameters")
        input_layout = QVBoxLayout(input_group)

        form = QFormLayout()
        form.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)

        self._api_lib_edit = QLineEdit("APILIB")
        form.addRow("Catalog Library:", self._api_lib_edit)

        self._api_ds_edit = QLineEdit("_API_ALL_DATA")
        form.addRow("Catalog Dataset:", self._api_ds_edit)

        self._row_id_edit = QLineEdit()
        self._row_id_edit.setPlaceholderText("Row ID from catalog (e.g., 3)")
        form.addRow("Row ID:", self._row_id_edit)

        self._report_path_edit = QLineEdit("&g_outputRoot")
        form.addRow("Report Path:", self._report_path_edit)

        input_layout.addLayout(form)

        # Run button
        btn_layout = QHBoxLayout()
        self._run_btn = QPushButton("Run Profile")
        self._run_btn.clicked.connect(self._on_run)
        btn_layout.addStretch()
        btn_layout.addWidget(self._run_btn)
        input_layout.addLayout(btn_layout)

        two_col_layout.addWidget(input_group, 1)

        # --- Right Column: Generated SAS Code ---
        code_group = QGroupBox("Generated SAS Code")
        code_layout = QVBoxLayout(code_group)

        self._code_preview = CodePreviewWidget()
        code_layout.addWidget(self._code_preview)

        two_col_layout.addWidget(code_group, 1)

        layout.addLayout(two_col_layout)

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
        layout.addWidget(self._log, 1)

    def initializePage(self) -> None:
        super().initializePage()
        # Pre-fill from state
        if self._state.step2_lib:
            self._api_lib_edit.setText(self._state.step2_lib)
        if self._state.step2_dataset:
            self._api_ds_edit.setText(self._state.step2_dataset)
        if self._state.selected_row_id:
            self._row_id_edit.setText(self._state.selected_row_id)
        self._refresh_code_preview()

    def _refresh_code_preview(self) -> None:
        row_id = self._row_id_edit.text().strip()
        if row_id:
            code = build_profile_code(
                self._api_lib_edit.text().strip() or "APILIB",
                self._api_ds_edit.text().strip() or "_API_ALL_DATA",
                row_id,
                self._report_path_edit.text().strip() or "&g_outputRoot",
            )
            self._code_preview.set_code(code)

    def _on_run(self) -> None:
        row_id = self._row_id_edit.text().strip()
        if not row_id:
            QMessageBox.warning(
                self, "Missing Row ID", "Please enter a row ID from the catalog."
            )
            return

        self._refresh_code_preview()
        self._run_btn.setEnabled(False)
        self._run_worker(
            lambda: self._service.profile_dataset(
                api_listing_lib=self._api_lib_edit.text().strip() or "APILIB",
                api_listing_ds=self._api_ds_edit.text().strip() or "_API_ALL_DATA",
                row_id=row_id,
                report_path=self._report_path_edit.text().strip() or "&g_outputRoot",
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
            row_id = self._row_id_edit.text().strip()
            self._state.step3_inputs = {
                "api_listing_lib": self._api_lib_edit.text().strip(),
                "api_listing_ds": self._api_ds_edit.text().strip(),
                "row_id": row_id,
                "report_path": self._report_path_edit.text().strip(),
            }
            self._state.step3_result = {"success": True, "log": result.log}
        else:
            self._state.step3_result = {"success": False, "log": result.log}

    @pyqtSlot(str)
    def _on_worker_failed(self, error: str) -> None:
        self._progress.setVisible(False)
        self._run_btn.setEnabled(True)
        self._log.append_log(f"Worker error: {error}")
        status_label(self._status_label, False, f"Worker error: {error}")
        self._state.step3_result = {"success": False, "log": error}

    def isComplete(self) -> bool:
        return bool(
            self._state.step3_result and self._state.step3_result.get("success")
        )
