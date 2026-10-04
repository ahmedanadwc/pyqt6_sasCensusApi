"""Main wizard window for the PyQt6 SAS Census application."""

from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import QWizard, QMessageBox

from pyqt6_sas_census.state import WizardState, highest_unlocked_step
from pyqt6_sas_census.services.sas_service import SasService
from pyqt6_sas_census.ui.pages import (
    ConnectionPage,
    CatalogPage,
    ProfileQueryPage,
)


class WizardWindow(QWizard):
    """Main wizard window with three pages and unlock logic."""

    def __init__(self, state: WizardState, service: SasService, parent=None):
        super().__init__(parent)
        self.setWindowTitle("US Census SAS API Studio")
        self.resize(1200, 800)
        self.setWizardStyle(QWizard.WizardStyle.ModernStyle)

        self._state = state
        self._service = service

        # Create pages
        self._connection_page = ConnectionPage(state, service)
        self._catalog_page = CatalogPage(state, service)
        self._profile_query_page = ProfileQueryPage(state, service)

        # Add pages in order
        self.addPage(self._connection_page)
        self.addPage(self._catalog_page)
        self.addPage(self._profile_query_page)

        # Connect signals
        self.currentIdChanged.connect(self._on_page_changed)
        self.finished.connect(self._on_finished)
        # Also update navigation when any page completes
        self._connection_page.completeChanged.connect(self._update_navigation)
        self._catalog_page.completeChanged.connect(self._update_navigation)
        self._profile_query_page.completeChanged.connect(self._update_navigation)

        # Initial navigation update
        self._update_navigation()

    def _on_page_changed(self, page_id: int) -> None:
        self._update_navigation()
        step_names = [
            "SAS Session",
            "Collect All Datasets",
            "Dataset Profile & Query Builder",
        ]
        if 0 <= page_id < len(step_names):
            self.setWindowTitle(f"US Census SAS API Studio - {step_names[page_id]}")

    def _update_navigation(self) -> None:
        max_unlocked = highest_unlocked_step(self._state)
        page_ids = self.pageIds()
        for i, page_id in enumerate(page_ids):
            page = self.page(page_id)
            if page:
                page.setEnabled(i <= max_unlocked)

    def _on_finished(self, result: int) -> None:
        if result == QWizard.DialogCode.Accepted:
            # Clean up SAS session on normal exit
            self._service.disconnect()

    def _on_disconnect_requested(self) -> None:
        """Reset state and navigate back to page 1."""
        self._state.reset_after_disconnect()
        self.setCurrentId(0)
        self._update_navigation()

    def closeEvent(self, event) -> None:
        # Ensure disconnect on close
        self._service.disconnect()
        super().closeEvent(event)
