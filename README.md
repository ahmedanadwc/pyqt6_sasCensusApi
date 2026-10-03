# PyQt6 SAS Census Wizard

A native Windows desktop application for the US Census SAS API, built as a PyQt6 `QWizard` that replicates the five-step Streamlit workflow with local SASPy execution.

## Prerequisites

- **Python 3.10+**
- **SAS 9.4 or Viya** installed and configured on the workstation
- **SASPy** configured with a valid `sascfg_personal.py` (see [SASPy docs](https://sassoftware.github.io/saspy/install.html#configuration-file))
- **SAS Census API macros** available in a local repository

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `SAS_CENSUS_SOURCE_ROOT` | Path to the source SAS Census API repository (containing `src/py_sascensusapi`) | `D:\Projects\Python\py_sasCensusApi` |
| `SAS_PROJECT_ROOT` | Path to the SAS Census API project root (containing `code/macros/censusapi`) | Auto-detected |
| `SAS_CFGFILE` | Path to personal SASPy config file | Auto-detected (`~/sascfg_personal.py`) |

### SASPy Configuration

Ensure your `sascfg_personal.py` defines `SAS_config_names` as a list of configuration names, e.g.:

```python
SAS_config_names = ['oda', 'local']
```

## Installation

```bash
# Clone or navigate to the project
cd D:\Projects\Python\pyqt6_sasCensusApi

# Install in development mode
python -m pip install -e .[test]

# Or install without test dependencies
python -m pip install -e .
```

## Running the Application

```bash
# Using the launcher script
python app.py

# Or using the console script (after installation)
pyqt6-sas-census
```

## The Five Wizard Steps

1. **SAS Session** — Select SAS configuration, connect to SAS, and initialize the Census API environment (SASAUTOS, APILIB, global macro variables).

2. **Collect All Datasets** — Run `%censusapi_getAllDataSets` to fetch the full Census dataset catalog into a SAS dataset. Preview rows, select a dataset, and save generated SAS code.

3. **Dataset Profile** — Run `%censusapi_getDsFullInfo` for the selected catalog row to generate a complete dataset profile. View SAS logs and save code.

4. **Catalog Search** — Search the Census catalog by keyword and vintage. Display matching endpoints and apply the selected endpoint to the query page.

5. **Query Builder** — Build and run `%censusapi_submitDataApiQuery` with automatic variable chunking. View generated code, SAS logs, result data, and save the SAS script.

## Testing

```bash
# Run all tests
python -m pytest -q

# Run specific test modules
python -m pytest tests/test_state.py -q
python -m pytest tests/test_programs.py -q
python -m pytest tests/test_sas_service.py -q
python -m pytest tests/test_dataframe_model.py -q
python -m pytest tests/test_wizard_unlocks.py -q
python -m pytest tests/test_imports.py -q
```

## Building Windows Executable

```powershell
# Run the build script
.\build_windows.ps1
```

Or manually with PyInstaller:

```powershell
python -m PyInstaller --noconfirm --clean --windowed --name PyQt6SasCensus app.py
```

The executable will be in `dist/PyQt6SasCensus/`.

### Packaging Notes

- The application requires a local SAS installation and valid SASPy configuration on the target workstation
- PyInstaller will bundle PyQt6, pandas, and Python dependencies
- SAS macros and the source `py_sascensusapi` package must be available at runtime via `SAS_CENSUS_SOURCE_ROOT`
- The executable does **not** include SAS itself

## Project Structure

```
pyqt6_sasCensusApi/
├── app.py                          # Launcher script
├── build_windows.ps1               # PyInstaller build script
├── pyproject.toml                  # Package metadata
├── README.md                       # This file
├── src/
│   └── pyqt6_sas_census/
│       ├── __init__.py
│       ├── main.py                 # Application entry point
│       ├── state.py                # WizardState + unlock rules
│       ├── sas/
│       │   ├── __init__.py
│       │   └── programs.py         # SAS macro code builders
│       ├── services/
│       │   ├── __init__.py
│       │   ├── source_adapter.py   # Imports source repo modules
│       │   ├── sas_service.py      # Service layer + typed results
│       │   └── workers.py          # Qt worker for non-blocking SAS
│       ├── models/
│       │   ├── __init__.py
│       │   └── dataframe_model.py  # QAbstractTableModel for pandas
│       └── ui/
│           ├── __init__.py
│           ├── widgets.py          # Reusable Qt widgets
│           ├── wizard.py           # WizardWindow controller
│           └── pages/
│               ├── __init__.py
│               ├── connection.py   # Step 1: SAS Session
│               ├── catalog.py      # Step 2: Collect Catalog
│               ├── profile.py      # Step 3: Dataset Profile
│               ├── search.py       # Step 4: Catalog Search
│               └── query.py        # Step 5: Query Builder
└── tests/
    ├── test_state.py
    ├── test_programs.py
    ├── test_source_adapter.py
    ├── test_sas_service.py
    ├── test_dataframe_model.py
    ├── test_wizard_unlocks.py
    └── test_imports.py
```

## Architecture

```
PyQt6 QWizard pages
        |
        v
WizardWindow + typed WizardState
        |
        v
SasService (OperationResult) + SasWorker (QThread)
        |
        v
SASBackend (saspy) + census_catalog (httpx)
        |
        v
SAS Session + Census API Macros
```

## Source Repository

The application reuses the following modules from the source SAS Census API repository (`py_sasCensusApi`):

- `SASBackend` (`sas_backend.py`) — SASPy session management
- `search_datasets` (`census_catalog.py`) — Census catalog search with fallback
- `config.py` — Path resolution and defaults

## License

Internal tool - see source repository for licensing.