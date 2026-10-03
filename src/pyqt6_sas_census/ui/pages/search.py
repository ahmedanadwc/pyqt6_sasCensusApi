"""Search page for the SAS Census wizard."""

from typing import Optional
from PyQt6.QtCore import pyqtSlot
from PyQt6.QtWidgets import (
    QWizardPage,
    QVBoxLayout,
    QHBoxLayout,
    QFormLayout,
    QLineEdit,
    QComboBox,
    QPushButton,
    QLabel,
    QListWidget,
    QMessageBox,
)

from pyqt6_sas_census.ui.widgets import SasLogWidget
from pyqt6_sas_census.services.workers import SasWorker
from pyqt6_sas_census.services.sas_service import SasService, OperationResult
from pyqt6_sas_census.state import WizardState
from PyQt6.QtWidgets import QProgressBar


class SearchPage(QWizardPage):
    """Page 4: Catalog Search - search Census catalog by keyword and vintage."""

    def __init__(self, state: WizardState, service: SasService, parent=None):
        super().__init__(parent)
        self.setTitle("Catalog Search")
        self.setSubTitle("Search the Census Data API catalog by keyword and vintage.")
        self._state = state
        self._service = service
        self._worker: Optional[SasWorker] = None
        self._search_results: list[dict] = []

        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)

        # Search inputs
        form = QFormLayout()
        self._query_edit = QLineEdit()
        self._query_edit.setPlaceholderText("e.g., population, housing, income")
        form.addRow("Keyword:", self._query_edit)

        self._year_combo = QComboBox()
        self._year_combo.addItems(
            ["All", "2022", "2021", "2020", "2019", "2010", "2000"]
        )
        self._year_combo.setCurrentText("All")
        form.addRow("Vintage:", self._year_combo)

        layout.addLayout(form)

        # Buttons
        btn_layout = QHBoxLayout()
        self._search_btn = QPushButton("Search")
        self._search_btn.clicked.connect(self._on_search)
        btn_layout.addWidget(self._search_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        # Progress bar (indeterminate)
        self._progress = QProgressBar()
        self._progress.setRange(0, 0)
        self._progress.setVisible(False)
        self._progress.setTextVisible(False)
        self._progress.setFixedHeight(4)
        layout.addWidget(self._progress)

        # Results
        layout.addWidget(QLabel("Search Results:"))
        self._results_list = QListWidget()
        self._results_list.itemClicked.connect(self._on_result_selected)
        layout.addWidget(self._results_list)

        # Selected endpoint
        self._selected_endpoint_label = QLabel("No endpoint selected")
        self._selected_endpoint_label.setStyleSheet("color: blue;")
        layout.addWidget(self._selected_endpoint_label)

        # Apply button
        apply_layout = QHBoxLayout()
        self._apply_btn = QPushButton("Apply to Query Page")
        self._apply_btn.clicked.connect(self._on_apply)
        self._apply_btn.setEnabled(False)
        apply_layout.addStretch()
        apply_layout.addWidget(self._apply_btn)
        layout.addLayout(apply_layout)

        # Log
        self._log = SasLogWidget()
        layout.addWidget(self._log)

    def _on_search(self) -> None:
        query = self._query_edit.text().strip()
        year = self._year_combo.currentText()
        year_param = None if year == "All" else year

        self._search_btn.setEnabled(False)
        self._results_list.clear()
        self._apply_btn.setEnabled(False)
        self._selected_endpoint_label.setText("No endpoint selected")

        self._run_worker(lambda: self._service.search_endpoints(query, year_param))

    def _run_worker(self, func) -> None:
        from PyQt6.QtCore import QThread

        self._progress.setVisible(True)
        self._search_btn.setEnabled(False)
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
    def _on_worker_finished(self, result: tuple) -> None:
        results, used_fallback = result if isinstance(result, tuple) else (result, False)
        self._progress.setVisible(False)
        self._search_btn.setEnabled(True)
        self._search_results = results

        if not results:
            if used_fallback:
                self._results_list.addItem(
                    "Could not reach catalog — showing local fallback"
                )
                self._log.set_log(
                    "Search fell back to local catalog (remote unavailable)."
                )
            else:
                self._results_list.addItem("No results found")
                self._log.set_log("Search returned no results")
        else:
            for ds in results:
                title = ds.get("title", "Unknown")
                vintage = ds.get("vintage", "")
                endpoint = ds.get("endpoint", "")
                self._results_list.addItem(f"{title} ({vintage}) - {endpoint}")
            self._log.set_log(f"Found {len(results)} dataset(s)")

    @pyqtSlot(str)
    def _on_worker_failed(self, error: str) -> None:
        self._progress.setVisible(False)
        self._search_btn.setEnabled(True)
        self._log.append_log(f"Worker error: {error}")

    def _on_result_selected(self, item) -> None:
        index = self._results_list.row(item)
        if 0 <= index < len(self._search_results):
            ds = self._search_results[index]
            endpoint = ds.get("endpoint", "")
            self._selected_endpoint_label.setText(f"Selected: {endpoint}")
            self._state.step4_selected_endpoint = endpoint
            self._apply_btn.setEnabled(True)

    def _on_apply(self) -> None:
        self._state.endpoint_selected = True
        self._state.step4_results = self._search_results
        self._state.step4_search_query = self._query_edit.text().strip()
        self._state.step4_year = (
            self._year_combo.currentText()
            if self._year_combo.currentText() != "All"
            else None
        )
        QMessageBox.information(self, "Applied", "Endpoint applied to Query page.")

    def isComplete(self) -> bool:
        return self._state.endpoint_selected
