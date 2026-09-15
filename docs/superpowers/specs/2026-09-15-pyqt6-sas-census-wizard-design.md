# PyQt6 SAS Census API Wizard Design

## Goal

Create a native Windows PyQt6 wizard application under
`D:\Projects\Python\pyqt6_sasCensusApi` that logically replicates the current
five-step workflow in
`D:\Projects\Python\py_sasCensusApi\Streamlit_app.py`.

The first release targets local workstation execution. It owns one SASPy
session and assumes the user has SAS and a usable SASPy configuration available
on the workstation.

## User experience

The application uses the native PyQt6 `QWizard` shell rather than a browser
wrapper or a simulated page navigator. The five pages are:

1. **SAS Session** — discover/select `SAS_config_names`, connect to SAS, and
   initialize SASAUTOS, APILIB, and global macro variables.
2. **Collect All Datasets** — run
   `%censusapi_getAllDataSets`, load an existing catalog dataset when available,
   preview rows, select a dataset row, display row details, and save generated
   SAS code.
3. **Dataset Profile** — run `%censusapi_getDsFullInfo` for the selected catalog
   row, show generated code and SAS logs, and save the code.
4. **Catalog Search** — search the Census catalog by keyword and vintage, display
   matching endpoints, and apply the selected endpoint to the query page.
5. **Query Builder** — build and run `%censusapi_submitDataApiQuery`, display
   generated code, SAS logs, result data, empty-result status, and save the code.

The application title and descriptive text identify it as the US Census SAS API
Studio. Defaults and labels should remain logically consistent with the
Streamlit implementation.

## Architecture

The target project is separated into UI, application state, SAS integration,
and data-display concerns:

```text
PyQt6 QWizard pages
        |
        v
Wizard/controller + typed application state
        |
        v
SAS service layer / worker boundary
        |
        v
Existing SASBackend and census_catalog modules
        |
        v
SASPy session and Census API macros
```

Recommended structure:

```text
app/
├── main.py
├── ui/
│   ├── wizard.py
│   ├── pages/
│   │   ├── connection_page.py
│   │   ├── catalog_page.py
│   │   ├── profile_page.py
│   │   ├── search_page.py
│   │   └── query_page.py
│   └── widgets/
│       ├── dataframe_view.py
│       └── sas_log_view.py
├── sas/
│   ├── session_manager.py
│   ├── executor.py
│   └── programs.py
├── models/
│   └── table_model.py
└── config/
```

The exact package names may follow the target repository's final layout, but
responsibilities must remain separated:

- **Pages** own controls, page-local validation, code previews, and result
  presentation.
- **Wizard/controller** owns shared state, page transitions, reset behavior,
  and unlock rules.
- **SAS service** owns the session lifecycle and delegates to the existing
  `SASBackend`.
- **Program builders** generate the five macro invocation scripts.
- **Qt table model/view** displays pandas dataframes without coupling the SAS
  layer to widgets.

The existing source project is treated as the behavior reference. Existing
backend and catalog functionality should be reused through a small,
testable adapter rather than copied into the new application.

## State and navigation

The application state contains:

- SAS configuration file path and selected configuration name
- SAS connection status and status message
- SAS project root and Census API key
- environment setup result
- Step 2 inputs, execution result, dataframe, library, and dataset name
- selected catalog row, selected row index, row ID, and dataset unique ID
- Step 3 inputs and execution result
- Step 4 search text, vintage filter, search results, selected endpoint, and
  endpoint-selected flag
- Step 5 query inputs and execution result/dataframe

Unlock behavior mirrors `highest_unlocked_step()` from the Streamlit app:

- Before connection, only page 1 is available.
- Page 2 is available after a successful connection and environment setup.
- Page 3 is available after a successful page 2 result, including an existing
  catalog dataset loaded from SAS.
- Page 4 is available after a successful page 3 result.
- Page 5 is available after an endpoint has been applied.
- Disconnecting resets the wizard to page 1 and clears dependent unlock state.

The native Next button is enabled only when page-local requirements and
prerequisite results are satisfied. Back remains available for already reached
pages. Changes to earlier inputs that invalidate later results must clear or
invalidate those dependent results explicitly.

## SAS execution and threading

The GUI thread must not execute blocking SASPy calls. Connection, environment
initialization, macro submission, and dataframe retrieval run through a worker
boundary based on `QThread`/worker objects or an equivalent Qt-supported
executor.

Worker results have an explicit shape containing:

- success flag
- SAS log
- listing/output text when available
- error lines
- warning lines
- optional dataframe
- operation-specific metadata

Worker exceptions are surfaced as failed operations and displayed on the
originating page. The wizard must never advance after an unsuccessful required
operation.

The SAS service exposes narrow operations:

- `connect(cfgname, cfgfile)`
- `disconnect()`
- `initialize_environment(project_root, api_key)`
- `collect_catalog(inputs)`
- `profile_dataset(inputs)`
- `search_endpoints(query, year)`
- `submit_query(inputs)`

The service owns one local SASPy session for the application lifetime and
cleans it up on normal application exit and explicit disconnect.

## Forms and defaults

The PyQt6 controls preserve the Streamlit workflow's meaningful defaults,
including:

- discovered SAS configuration names and configured `DEFAULT_SAS_CFGFILE`
- `SAS_PROJECT_ROOT`
- `DEFAULT_OUT_LIB` (`APILIB`)
- `DEFAULT_OUT_DS` (`_API_ALL_DATA`)
- `DEFAULT_DATA_JSON_URL`
- `&g_outputRoot`
- default endpoint
  `https://api.census.gov/data/2000/dec/sf1?`
- default query clauses, dataset ID, output dataset, API key reference, and
  `DEFAULT_MAX_VAR_COUNT`

Controls are validated before execution. Required text fields, numeric ranges,
dataset row identifiers, endpoint selection, and query fields produce visible
inline errors. The application should retain the Streamlit fallback behavior
of `search_datasets()` when the remote catalog cannot be fetched.

## Presentation and exports

SAS code previews use read-only plain-text editors with a Save `.sas` action.
Logs use read-only text views and preserve SAS warning/error text. Dataframes
use a reusable Qt model/view implementation supporting readable headers,
selection, scrolling, and the selected catalog row needed by the profile page.

The first release does not require pixel-level reproduction of Streamlit CSS.
It prioritizes native Windows usability, clear validation, responsive
execution, and logical behavior parity.

## Error handling

Errors must be explicit and operation-specific:

- Invalid or missing SAS configuration files are reported before connection.
- SASPy import/configuration/connection errors remain visible to the user.
- Environment setup failures prevent later pages from unlocking.
- Macro failures show the number of SAS errors and the complete available log.
- Dataframe retrieval failures do not appear as successful macro execution.
- Network catalog errors fall back through the existing catalog module and are
  distinguishable from an empty search result.
- Disconnect always clears the active session and dependent wizard state.

No broad exception handling may silently convert a failed operation into a
successful result.

## Testing

Tests should cover the behavior most likely to regress during migration:

- initial state unlocks only the connection page
- successful prerequisites unlock pages in order
- failed page results do not unlock the next page
- disconnect relocks the wizard and clears dependent results
- endpoint application unlocks the query page
- generated macro code contains the expected parameters
- worker/service failures are returned as explicit failed results
- table model exposes dataframe columns, rows, and selected-row data

Service and state tests should use fakes/mocks and must not require a live SAS
installation. A small smoke test may instantiate the wizard if the environment
has PyQt6 available.

## Deployment

The application is designed for Windows packaging as a desktop executable,
with PyInstaller as the initial packaging target. Packaging must account for
PyQt6 platform plugins, pandas dependencies, and the user's local SAS/SASPy
configuration. The first implementation does not add a remote service or
multi-user authentication layer.

## Out of scope

- Replacing SASPy or changing the existing SAS macro implementation
- Centralized remote SAS execution
- Browser embedding or a Streamlit compatibility layer
- Pixel-perfect reproduction of Streamlit styling
- New Census API functionality not present in the current Streamlit flow
- Unrelated refactoring of the source Streamlit project
