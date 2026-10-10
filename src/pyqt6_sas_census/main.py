"""Main entry point for the PyQt6 SAS Census Wizard."""

import sys

from PyQt6.QtWidgets import QApplication

from pyqt6_sas_census import config
from pyqt6_sas_census.sas.backend import SASBackend
from pyqt6_sas_census.services.sas_service import SasService
from pyqt6_sas_census.state import WizardState
from pyqt6_sas_census.ui.wizard import WizardWindow


def main() -> int:
    """Run the PyQt6 SAS Census wizard."""
    app = QApplication(sys.argv)
    app.setOrganizationName("CensusSAS")
    app.setApplicationName("PyQt6SasCensus")

    # Initialize state and service
    state = WizardState()

    # Initialize state defaults from this app's own config module.
    state.project_root = str(config.SAS_PROJECT_ROOT)
    state.sas_config_file = config.DEFAULT_SAS_CFGFILE

    backend = SASBackend()
    service = SasService(backend)

    # Create and show wizard
    wizard = WizardWindow(state, service)
    wizard.show()

    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
