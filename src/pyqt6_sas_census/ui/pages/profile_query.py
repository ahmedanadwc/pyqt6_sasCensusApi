"""Combined Profile & Query page for the SAS Census wizard (Step 3)."""

from typing import Any, Optional
from PyQt6.QtCore import Qt, QThread, pyqtSlot
from PyQt6.QtWidgets import (
    QFrame,
    QWizardPage,
    QVBoxLayout,
    QHBoxLayout,
    QLineEdit,
    QPushButton,
    QLabel,
    QMessageBox,
    QGroupBox,
    QProgressBar,
    QTabWidget,
    QWidget,
    QTextEdit,
    QSpinBox,
    QSplitter,
    QScrollArea,
    QCheckBox,
)

from pyqt6_sas_census.ui.widgets import (
    SasLogWidget,
    CodePreviewWidget,
    CollapsibleCodeWidget,
    DataFrameWidget,
    add_form_field,
    make_form_grid,
    status_label,
)
from pyqt6_sas_census.ui.geo_selector_dialog import open_geo_dialog
from pyqt6_sas_census.services.workers import SasWorker
from pyqt6_sas_census.services.sas_service import SasService, OperationResult
from pyqt6_sas_census.sas.programs import build_profile_code, build_query_code
from pyqt6_sas_census.state import WizardState
from pyqt6_sas_census import config as cfg


PROFILE_TABLE_SUFFIXES = [
    ("Variables", "_VARS"),
    ("Groups", "_GRPS"),
    ("Geographies", "_GEOS"),
    ("Sample Queries", "_EXMPLS"),
]


class ProfileQueryPage(QWizardPage):
    """Page 3: Dataset Profile & Query Builder - combined profile, search, and query."""

    def __init__(self, state: WizardState, service: SasService, parent=None):
        super().__init__(parent)
        self.setTitle("Dataset Profile & Query Builder")
        self.setSubTitle(
            "Generate dataset profile (%censusapi_getDsFullInfo), search catalog, "
            "and submit Census API queries (%censusapi_submitDataApiQuery)."
        )
        self._state = state
        self._service = service
        self._worker: Optional[SasWorker] = None
        self._worker_thread: Optional[QThread] = None
        self._profile_tables: dict[
            str, tuple[str, Any]
        ] = {}  # label -> (table_name, dataframe)
        self._current_operation: str = ""

        self._setup_ui()

    def _setup_ui(self) -> None:
        # Scroll area keeps the page's minimum size small so the wizard never
        # grows taller than the display; content scrolls instead.
        page_layout = QVBoxLayout(self)
        page_layout.setContentsMargins(0, 0, 0, 0)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        content = QWidget()
        content.setMinimumHeight(1400)
        layout = QVBoxLayout(content)
        layout.setContentsMargins(0, 0, 0, 0)
        scroll.setWidget(content)
        page_layout.addWidget(scroll)

        # Main splitter for resizable sections
        main_splitter = QSplitter()
        main_splitter.setOrientation(Qt.Orientation.Vertical)
        layout.addWidget(main_splitter, 1)

        # === TOP SECTION: Profile Inputs & Results ===
        top_widget = QWidget()
        top_layout = QVBoxLayout(top_widget)
        top_layout.setContentsMargins(0, 0, 0, 0)

        # Profile parameters: full-width form, fields in two columns
        profile_input_group = QGroupBox("Profile Parameters (%censusapi_getDsFullInfo)")
        profile_input_layout = QVBoxLayout(profile_input_group)
        profile_grid = make_form_grid()

        self._api_lib_edit = QLineEdit("APILIB")
        add_form_field(profile_grid, 0, 0, "Catalog Library:", self._api_lib_edit)

        self._api_ds_edit = QLineEdit("_API_ALL_DATA")
        add_form_field(profile_grid, 1, 0, "Catalog Dataset:", self._api_ds_edit)

        self._row_id_edit = QLineEdit()
        self._row_id_edit.setPlaceholderText("Row ID from catalog (e.g., 3)")
        add_form_field(profile_grid, 0, 1, "Row ID:", self._row_id_edit)

        self._profile_report_path_edit = QLineEdit("&g_outputRoot")
        add_form_field(
            profile_grid, 1, 1, "Report Path:", self._profile_report_path_edit
        )

        self._reuse_profile_check = QCheckBox("Reuse Existing Profile Tables")
        self._reuse_profile_check.setChecked(True)
        profile_grid.addWidget(self._reuse_profile_check, 2, 0, 1, 4)

        profile_input_layout.addLayout(profile_grid)

        # Profile buttons (Submit on left, Refresh on right - matching Streamlit)
        profile_btn_layout = QHBoxLayout()
        self._run_profile_btn = QPushButton("Run Profile")
        self._run_profile_btn.clicked.connect(self._on_run_profile)
        self._refresh_profile_btn = QPushButton("Refresh from SAS")
        self._refresh_profile_btn.clicked.connect(self._on_refresh_profile)
        self._refresh_profile_btn.setEnabled(False)
        profile_btn_layout.addWidget(self._run_profile_btn)
        profile_btn_layout.addStretch()
        profile_btn_layout.addWidget(self._refresh_profile_btn)
        profile_input_layout.addLayout(profile_btn_layout)

        # Profile progress and status
        self._profile_progress = QProgressBar()
        self._profile_progress.setRange(0, 0)
        self._profile_progress.setVisible(False)
        self._profile_progress.setTextVisible(False)
        self._profile_progress.setFixedHeight(4)
        profile_input_layout.addWidget(self._profile_progress)

        self._profile_status = QLabel("")
        profile_input_layout.addWidget(self._profile_status)

        # SAS log sits below the form, above the generated code
        self._profile_log = SasLogWidget()
        self._profile_log.setMaximumHeight(150)

        # Generated SAS Code (Profile) - collapsible
        self._profile_code_preview = CollapsibleCodeWidget(
            title="Generated SAS Code (Profile)", expanded=False
        )

        top_layout.addWidget(profile_input_group)
        top_layout.addWidget(self._profile_log)
        top_layout.addWidget(self._profile_code_preview)

        # Profile results tabs (spans full width below)
        self._profile_tabs = QTabWidget()
        self._profile_tabs.setMinimumHeight(260)  # tab bar + header + ~5 grid rows
        self._profile_tab_widgets: dict[str, DataFrameWidget] = {}
        for label, _ in PROFILE_TABLE_SUFFIXES:
            tab_widget = QWidget()
            tab_layout = QVBoxLayout(tab_widget)
            # Use multi-select for Variables tab
            multi_select = label == "Variables"
            df_widget = DataFrameWidget(
                auto_resize_columns=True, multi_select=multi_select
            )
            self._profile_tab_widgets[label] = df_widget
            tab_layout.addWidget(df_widget)
            self._profile_tabs.addTab(tab_widget, label)

        # Connect Variables tab selection (both single and multi)
        self._profile_tab_widgets["Variables"].row_selected.connect(
            self._on_variable_selected
        )
        self._profile_tab_widgets["Variables"].rows_selected.connect(
            self._on_variables_multi_selected
        )
        # Connect Sample Queries tab selection
        self._profile_tab_widgets["Sample Queries"].row_selected.connect(
            self._on_sample_query_selected
        )

        top_layout.addWidget(self._profile_tabs, 1)

        # Add top widget to splitter
        main_splitter.addWidget(top_widget)

        # === BOTTOM SECTION: Query Builder ===
        query_widget = QWidget()
        query_layout = QVBoxLayout(query_widget)
        query_layout.setContentsMargins(0, 0, 0, 0)

        # Query builder: full-width form, fields in two columns
        query_input_group = QGroupBox("Query Builder (%censusapi_submitDataApiQuery)")
        query_input_layout = QVBoxLayout(query_input_group)
        query_grid = make_form_grid()

        self._endpoint_edit = QLineEdit()
        self._endpoint_edit.setPlaceholderText(
            "https://api.census.gov/data/2000/dec/sf1?"
        )
        add_form_field(query_grid, 0, 0, "Endpoint:", self._endpoint_edit, span=2)

        self._get_clause_edit = QTextEdit()
        self._get_clause_edit.setPlainText("get=NAME")
        self._get_clause_edit.setMaximumHeight(80)
        self._get_clause_edit.setPlaceholderText(
            "Enter variable names, one per line or comma-separated"
        )
        self._get_clause_edit.textChanged.connect(self._on_query_field_changed)
        add_form_field(query_grid, 1, 0, "GET Clause:", self._get_clause_edit, span=2)

        self._for_clause_edit = QLineEdit("for=state:*")
        self._for_clause_edit.textChanged.connect(self._on_query_field_changed)
        add_form_field(query_grid, 2, 0, "FOR Clause:", self._for_clause_edit)

        self._in_clause_edit = QLineEdit("in=")
        self._in_clause_edit.textChanged.connect(self._on_query_field_changed)
        # IN Clause with geography selector button
        in_clause_layout = QHBoxLayout()
        in_clause_layout.addWidget(self._in_clause_edit)
        self._geo_btn = QPushButton("🌎 Select Geography")
        self._geo_btn.clicked.connect(self._on_select_geography)
        in_clause_layout.addWidget(self._geo_btn)
        add_form_field(query_grid, 3, 0, "IN Clause:", in_clause_layout)

        self._dataset_id_edit = QLineEdit()
        add_form_field(query_grid, 2, 1, "Dataset Unique ID:", self._dataset_id_edit)

        self._out_dataset_edit = QLineEdit("work.sf1_response")
        add_form_field(query_grid, 3, 1, "Output Dataset:", self._out_dataset_edit)

        self._api_key_ref_edit = QLineEdit("&g_apiKey")
        add_form_field(query_grid, 4, 0, "API Key Reference:", self._api_key_ref_edit)

        self._max_var_count_spin = QSpinBox()
        self._max_var_count_spin.setRange(5, 50)
        self._max_var_count_spin.setValue(50)
        add_form_field(
            query_grid, 4, 1, "Max Variables per Chunk:", self._max_var_count_spin
        )

        query_input_layout.addLayout(query_grid)

        # Query buttons
        query_btn_layout = QHBoxLayout()
        self._run_query_btn = QPushButton("Run Query")
        self._run_query_btn.clicked.connect(self._on_run_query)
        query_btn_layout.addWidget(self._run_query_btn)
        query_btn_layout.addStretch()
        query_input_layout.addLayout(query_btn_layout)

        # Query progress and status
        self._query_progress = QProgressBar()
        self._query_progress.setRange(0, 0)
        self._query_progress.setVisible(False)
        self._query_progress.setTextVisible(False)
        self._query_progress.setFixedHeight(4)
        query_input_layout.addWidget(self._query_progress)

        self._query_status = QLabel("")
        query_input_layout.addWidget(self._query_status)

        # SAS log sits below the form, above the generated code
        self._query_log = SasLogWidget()
        self._query_log.setMaximumHeight(150)

        # Create query results widget first
        self._query_df_widget = DataFrameWidget()

        # Generated SAS Code (Query) - collapsible
        self._query_code_preview = CollapsibleCodeWidget(
            title="Generated SAS Code (Query)", expanded=True
        )

        query_layout.addWidget(query_input_group)
        query_layout.addWidget(self._query_log)
        query_layout.addWidget(self._query_code_preview)
        query_layout.addWidget(QLabel("Query Results:"))
        query_layout.addWidget(self._query_df_widget, 1)

        main_splitter.addWidget(query_widget)

        # Set initial splitter sizes (top: profile, bottom: query)
        main_splitter.setSizes([700, 700])

    def initializePage(self) -> None:
        super().initializePage()
        # Pre-fill from state - check widget exists first
        if not hasattr(self, "_api_lib_edit") or self._api_lib_edit is None:
            return
        try:
            if self._state.step2_lib:
                self._api_lib_edit.setText(self._state.step2_lib)
        except RuntimeError:
            # Widget was deleted, re-setup UI
            self._setup_ui()
            if self._state.step2_lib:
                self._api_lib_edit.setText(self._state.step2_lib)
            return

        if self._state.step2_dataset:
            self._api_ds_edit.setText(self._state.step2_dataset)
        if self._state.selected_row_id:
            self._row_id_edit.setText(self._state.selected_row_id)
        if self._state.dataset_unique_id:
            self._dataset_id_edit.setText(self._state.dataset_unique_id)
        if self._state.step3_selected_endpoint:
            endpoint = self._state.step3_selected_endpoint
            if endpoint and not endpoint.endswith("?"):
                endpoint += "?"
            self._endpoint_edit.setText(endpoint)

        # Load per-dataset query fields if available
        uid = self._state.dataset_unique_id or ""
        if uid and uid in self._state.step3_query_fields:
            fields = self._state.step3_query_fields[uid]
            if "get" in fields:
                self._get_clause_edit.setPlainText(fields["get"])
            if "for" in fields:
                self._for_clause_edit.setText(fields["for"])
            if "in" in fields:
                self._in_clause_edit.setText(fields["in"])

        self._refresh_profile_code_preview()
        self._refresh_query_code_preview()

        # Try to load existing profile tables
        self._try_load_existing_profile()

    def _refresh_profile_code_preview(self) -> None:
        row_id = self._row_id_edit.text().strip()
        if row_id:
            code = build_profile_code(
                self._api_lib_edit.text().strip() or "APILIB",
                self._api_ds_edit.text().strip() or "_API_ALL_DATA",
                row_id,
                self._profile_report_path_edit.text().strip() or "&g_outputRoot",
            )
            self._profile_code_preview.set_code(code)

    def _refresh_query_code_preview(self) -> None:
        code = build_query_code(
            self._endpoint_edit.text().strip()
            or "https://api.census.gov/data/2000/dec/sf1?",
            self._get_clause_edit.toPlainText().strip() or "get=NAME",
            self._for_clause_edit.text().strip() or "for=state:*",
            self._in_clause_edit.text().strip() or "in=",
            self._dataset_id_edit.text().strip() or "_114_dec_2000",
            self._out_dataset_edit.text().strip() or "work.sf1_response",
            self._api_key_ref_edit.text().strip() or "&g_apiKey",
            self._max_var_count_spin.value(),
        )
        self._query_code_preview.set_code(code)

    # === Profile Operations ===

    def _on_run_profile(self) -> None:
        row_id = self._row_id_edit.text().strip()
        if not row_id:
            QMessageBox.warning(
                self, "Missing Row ID", "Please enter a row ID from the catalog."
            )
            return

        # Check if "Reuse Existing Profile Tables" is checked and tables exist
        reuse = self._reuse_profile_check.isChecked()
        if reuse and self._state.dataset_unique_id:
            existing_tables = self._service.fetch_profile_tables(
                self._state.dataset_unique_id
            )
            if len(existing_tables) == 4:  # All 4 tables exist
                self._populate_profile_tabs(existing_tables)
                self._profile_log.set_log(
                    "Reused existing APILIB profile tables; %censusapi_getDsFullInfo was not re-run."
                )
                status_label(
                    self._profile_status, True, "Success (reused existing tables)"
                )
                self._state.step3_profile_result = {
                    "success": True,
                    "log": "Reused existing tables",
                }
                self._run_profile_btn.setEnabled(True)
                self._refresh_profile_btn.setEnabled(True)
                return

        self._current_operation = "profile"
        self._refresh_profile_code_preview()
        self._run_profile_btn.setEnabled(False)
        self._refresh_profile_btn.setEnabled(False)
        self._profile_progress.setVisible(True)

        self._run_worker(
            lambda: self._service.profile_dataset(
                api_listing_lib=self._api_lib_edit.text().strip() or "APILIB",
                api_listing_ds=self._api_ds_edit.text().strip() or "_API_ALL_DATA",
                row_id=row_id,
                report_path=self._profile_report_path_edit.text().strip()
                or "&g_outputRoot",
            )
        )

    def _on_refresh_profile(self) -> None:
        """Refresh profile tables from SAS (bypass cache)."""
        if not self._state.dataset_unique_id:
            return
        self._load_profile_tables(force_refresh=True)

    def _try_load_existing_profile(self) -> None:
        """Try to load existing profile tables for the selected dataset."""
        uid = self._state.dataset_unique_id
        if not uid:
            return
        self._load_profile_tables(force_refresh=False)

    def _load_profile_tables(self, force_refresh: bool = False) -> None:
        """Load profile tables from SASHELP.VTABLE and fetch data."""
        if not self._state.dataset_unique_id:
            return

        tables = self._service.fetch_profile_tables(self._state.dataset_unique_id)
        if tables:
            self._populate_profile_tabs(tables)

    def _populate_profile_tabs(self, tables: dict) -> None:
        """Populate the profile tabs with fetched table data."""
        for label, (table_name, df) in tables.items():
            if label in self._profile_tab_widgets:
                self._profile_tab_widgets[label].set_dataframe(df)
                # Store table name for reference
                self._profile_tab_widgets[label].setProperty("table_name", table_name)

    @pyqtSlot(object)
    def _on_worker_finished(self, result: OperationResult) -> None:
        self._profile_progress.setVisible(False)
        self._run_profile_btn.setEnabled(True)
        self._refresh_profile_btn.setEnabled(True)
        self._profile_log.set_log(result.log)
        status_label(
            self._profile_status,
            result.success,
            "Success" if result.success else "Failed",
        )

        if result.success:
            self._state.step3_profile_inputs = {
                "api_listing_lib": self._api_lib_edit.text().strip(),
                "api_listing_ds": self._api_ds_edit.text().strip(),
                "row_id": self._row_id_edit.text().strip(),
                "report_path": self._profile_report_path_edit.text().strip(),
            }
            self._state.step3_profile_result = {"success": True, "log": result.log}

            # After profile runs, try to load the generated tables
            self._load_profile_tables(force_refresh=True)
        else:
            self._state.step3_profile_result = {"success": False, "log": result.log}

    # === Query Operations ===

    def _on_run_query(self) -> None:
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

        self._current_operation = "query"
        self._refresh_query_code_preview()
        self._run_query_btn.setEnabled(False)
        self._query_progress.setVisible(True)

        self._run_worker(
            lambda: self._service.submit_query(
                api_base_url=endpoint,
                get_clause=self._get_clause_edit.toPlainText().strip(),
                for_clause=self._for_clause_edit.text().strip(),
                in_clause=self._in_clause_edit.text().strip(),
                dataset_id=dataset_id,
                out_dataset=self._out_dataset_edit.text().strip(),
                api_key_ref=self._api_key_ref_edit.text().strip(),
                max_var_count=self._max_var_count_spin.value(),
            )
        )

    @pyqtSlot(object)
    def _on_query_finished(self, result: OperationResult) -> None:
        self._query_progress.setVisible(False)
        self._run_query_btn.setEnabled(True)
        self._query_log.set_log(result.log)
        status_label(
            self._query_status,
            result.success,
            "Success" if result.success else "Failed",
        )

        if result.success:
            self._state.step3_query_inputs = {
                "api_base_url": self._endpoint_edit.text().strip(),
                "get_clause": self._get_clause_edit.toPlainText().strip(),
                "for_clause": self._for_clause_edit.text().strip(),
                "in_clause": self._in_clause_edit.text().strip(),
                "dataset_id": self._dataset_id_edit.text().strip(),
                "out_dataset": self._out_dataset_edit.text().strip(),
                "api_key_ref": self._api_key_ref_edit.text().strip(),
                "max_var_count": self._max_var_count_spin.value(),
            }
            self._state.step3_query_result = {"success": True, "log": result.log}
            if result.dataframe is not None:
                self._state.step3_query_dataframe = result.dataframe
                self._query_df_widget.set_dataframe(result.dataframe)
            else:
                status_label(
                    self._query_status, True, "Query completed but no data returned"
                )
        else:
            self._state.step3_query_result = {"success": False, "log": result.log}

    # === Selection Handlers ===

    def _on_variable_selected(self, row: dict) -> None:
        """Handle single variable selection from Variables tab - populate GET clause."""
        self._add_variable_to_get_clause(row)

    def _on_variables_multi_selected(self, rows: list[dict]) -> None:
        """Handle multi-variable selection from Variables tab - populate GET clause with all selected."""
        if not rows:
            return
        uid = self._state.dataset_unique_id or ""
        if uid not in self._state.step3_query_fields:
            self._state.step3_query_fields[uid] = {}

        # Collect all variable names from selected rows
        var_names = []
        for row in rows:
            name = row.get("Name") or row.get("name") or row.get("NAME")
            if name and name not in var_names:
                var_names.append(name)

        if var_names:
            new_get = "get=" + ",".join(var_names)
            self._state.step3_query_fields[uid]["get"] = new_get
            self._get_clause_edit.setPlainText(new_get)
            self._refresh_query_code_preview()

    def _add_variable_to_get_clause(self, row: dict) -> None:
        """Add a single variable to the GET clause (for single-select mode)."""
        name = row.get("Name") or row.get("name") or row.get("NAME")
        if name:
            uid = self._state.dataset_unique_id or ""
            if uid not in self._state.step3_query_fields:
                self._state.step3_query_fields[uid] = {}
            current_get = self._state.step3_query_fields[uid].get("get", "get=")
            if current_get == "get=":
                new_get = f"get={name}"
            else:
                vars_list = current_get.replace("get=", "").split(",")
                if name not in vars_list:
                    vars_list.append(name)
                new_get = "get=" + ",".join(vars_list)
            self._state.step3_query_fields[uid]["get"] = new_get
            self._get_clause_edit.setPlainText(new_get)
            self._refresh_query_code_preview()

    def _on_sample_query_selected(self, row: dict) -> None:
        """Handle sample query selection - populate all query fields."""
        url = (
            row.get("in_exampleURL")
            or row.get("IN_EXAMPLEURL")
            or row.get("ExampleURL")
        )
        if url:
            parsed = self._parse_example_url(url)
            uid = self._state.dataset_unique_id or ""
            if uid not in self._state.step3_query_fields:
                self._state.step3_query_fields[uid] = {}
            for k, v in parsed.items():
                if v:
                    self._state.step3_query_fields[uid][k] = v
            if "get" in parsed:
                self._get_clause_edit.setPlainText(parsed["get"])
            if "for" in parsed:
                self._for_clause_edit.setText(parsed["for"])
            if "in" in parsed:
                self._in_clause_edit.setText(parsed["in"])
            if "base_url" in parsed:
                self._endpoint_edit.setText(parsed["base_url"])
            self._refresh_query_code_preview()

    def _on_query_field_changed(self) -> None:
        """Auto-save GET, FOR and IN clauses to per-dataset query fields."""
        uid = self._state.dataset_unique_id or ""
        if not uid:
            return
        if uid not in self._state.step3_query_fields:
            self._state.step3_query_fields[uid] = {}
        self._state.step3_query_fields[uid]["get"] = (
            self._get_clause_edit.toPlainText().strip()
        )
        self._state.step3_query_fields[uid]["for"] = (
            self._for_clause_edit.text().strip()
        )
        self._state.step3_query_fields[uid]["in"] = self._in_clause_edit.text().strip()

    def _parse_example_url(self, url: str) -> dict[str, str]:
        """Parse an example URL into base_url, get, for, in clauses."""
        from urllib.parse import unquote

        base, _, query = str(url).strip().partition("?")
        parsed = {
            "base_url": f"{base}?" if base else "",
            "get": "",
            "for": "",
            "in": "",
        }
        in_clauses = []
        for part in query.split("&"):
            name, _, value = part.partition("=")
            name, value = name.strip().lower(), unquote(value.strip())
            if name == "get":
                parsed["get"] = f"get={value}"
            elif name == "for":
                parsed["for"] = f"for={value}"
            elif name == "in":
                in_clauses.append(f"in={value}")
        parsed["in"] = "&".join(in_clauses)
        return parsed

    def _on_select_geography(self) -> None:
        """Open the geography selector dialog and update the IN clause."""
        current_in = self._in_clause_edit.text().strip()

        def on_geo_selected(selection: list[dict], cur_in: str) -> None:
            from pyqt6_sas_census.geo_lookup import merge_in_clause

            new_in = merge_in_clause(cur_in, selection)
            self._in_clause_edit.setText(new_in)
            self._refresh_query_code_preview()

            # Update per-dataset query fields
            uid = self._state.dataset_unique_id or ""
            if uid:
                if uid not in self._state.step3_query_fields:
                    self._state.step3_query_fields[uid] = {}
                self._state.step3_query_fields[uid]["in"] = new_in

        open_geo_dialog(current_in, on_geo_selected, self)

    # === Worker Management ===

    def _run_worker(self, func) -> None:
        self._worker_thread = QThread()
        self._worker = SasWorker(func)
        self._worker.moveToThread(self._worker_thread)

        if self._current_operation == "profile":
            self._worker.finished.connect(self._on_worker_finished)
        elif self._current_operation == "query":
            self._worker.finished.connect(self._on_query_finished)

        self._worker.failed.connect(self._on_worker_failed)
        self._worker.finished.connect(self._worker_thread.quit)
        self._worker.failed.connect(self._worker_thread.quit)
        self._worker.finished.connect(self._worker.deleteLater)
        self._worker.failed.connect(self._worker.deleteLater)
        self._worker_thread.finished.connect(self._worker_thread.deleteLater)
        self._worker_thread.started.connect(self._worker.run)
        self._worker_thread.start()

    @pyqtSlot(str)
    def _on_worker_failed(self, error: str) -> None:
        if self._current_operation == "profile":
            self._profile_progress.setVisible(False)
            self._run_profile_btn.setEnabled(True)
            self._refresh_profile_btn.setEnabled(True)
            self._profile_log.append_log(f"Worker error: {error}")
            status_label(self._profile_status, False, f"Worker error: {error}")
            self._state.step3_profile_result = {"success": False, "log": error}
        elif self._current_operation == "query":
            self._query_progress.setVisible(False)
            self._run_query_btn.setEnabled(True)
            self._query_log.append_log(f"Worker error: {error}")
            status_label(self._query_status, False, f"Worker error: {error}")
            self._state.step3_query_result = {"success": False, "log": error}

    def isComplete(self) -> bool:
        # Complete if either profile or query has succeeded
        profile_ok = bool(
            self._state.step3_profile_result
            and self._state.step3_profile_result.get("success")
        )
        query_ok = bool(
            self._state.step3_query_result
            and self._state.step3_query_result.get("success")
        )
        return profile_ok or query_ok


# Need to add Qt import
from PyQt6.QtCore import Qt
