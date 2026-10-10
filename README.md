# pyqt6_sasCensusApi

**A PyQt 6 wizard for interacting with the SAS Census API**

---

## Overview

`pyqt6_sasCensusApi` provides a native Windows desktop application that guides the user through three logical steps:

1. **Connect & initialise** – Open a SAS session (via SASPy), load a configuration file and run any required environment‑setup code.
2. **Collect catalog** – Retrieve the full list of datasets available from the SAS Census API (`%censusapi_getAllDataSets`).
3. **Profile & query** – Inspect a selected dataset’s metadata (`%censusapi_getDsFullInfo`) and construct a custom query (`%censusapi_submitDataApiQuery`).

The wizard tracks shared state in the `WizardState` class and delegates all SAS‑related operations to `SasService`, which wraps the backend implementation in `src/pyqt6_sas_census/sas/backend.py`.

---

## Architecture snapshot (graft output)

| Directory | Hotspot symbols |
|-----------|-----------------|
| `src/` | `WizardState` (`state.py`), `OperationResult` (`services/sas_service.py`), `SasLogWidget` (`ui/widgets.py`) |
| `tests/` | `FakeBackend` (`test_sas_service.py`), `_service` (`test_page_status_label.py`) |

**Main entry point**: [`app.py`](file:///D:/Projects/Python/pyqt6_sasCensusApi/app.py) – creates the Qt `QApplication`, builds a `WizardWindow`, and starts the event loop.

**Core UI modules**:
- [`wizard.py`](file:///D:/Projects/Python/pyqt6_sasCensusApi/src/pyqt6_sas_census/ui/wizard.py) – top‑level window
- [`widgets.py`](file:///D:/Projects/Python/pyqt6_sasCensusApi/src/pyqt6_sas_census/ui/widgets.py) – log view, code preview, etc.
- Page modules under `src/pyqt6_sas_census/ui/pages/` – connection, catalog, profile/query pages.

**Backend / service**:
- [`backend.py`](file:///D:/Projects/Python/pyqt6_sasCensusApi/src/pyqt6_sas_census/sas/backend.py) – thin wrapper around SASPy.
- [`sas_service.py`](file:///D:/Projects/Python/pyqt6_sasCensusApi/src/pyqt6_sas_census/services/sas_service.py) – high‑level operations (`connect`, `collect_catalog`, `submit_code`, etc.).

---

## Installation

```bash
# Clone the repository
git clone https://github.com/yourorg/pyqt6_sasCensusApi.git
cd pyqt6_sasCensusApi

# Create a virtual environment
python -m venv .venv
.venv\Scripts\activate  # on Windows

# Install dependencies
pip install -r requirements.txt
```

> **Note**: The project depends on **PyQt6**, **SASPy**, and a valid SAS configuration file. Ensure you have a working SAS installation and the appropriate `sas.cfg` file.

---

## Running the application

```bash
python -m pyqt6_sas_census.main
```

The wizard window will appear. Follow the three steps to connect to SAS, pull the dataset catalog, and explore/query a dataset.

---

## Testing

The test suite lives under `tests/` and validates that all public modules are importable and that the service layer behaves as expected.

```bash
# Run the unit tests (requires a mock backend)
pytest
```

---

## License

This project is licensed under the MIT License – see the `LICENSE` file for details.

---

*Generated with assistance from the graft code‑graph tooling.*
