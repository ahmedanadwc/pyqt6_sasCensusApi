"""Typed application state and page unlock rules for the wizard."""

from dataclasses import dataclass
from typing import Any


_DEFAULT_STATUS = "⚪ SAS Disconnected (Preview & Code Export mode)"


@dataclass
class WizardState:
    """Shared state for the three-step SAS Census wizard.

    Steps:
    1. SAS Session - Connect to SAS and initialize environment
    2. Collect All Datasets - Run %censusapi_getAllDataSets
    3. Dataset Profile & Query Builder - Run %censusapi_getDsFullInfo and %censusapi_submitDataApiQuery
    """

    sas_config_file: str = ""
    sas_config_name: str = ""
    sas_connected: bool = False
    sas_status_message: str = _DEFAULT_STATUS
    project_root: str = ""
    api_key: str = ""
    environment_ready: bool = False
    environment_result: object | None = None

    # Step 2: Collect Catalog
    step2_inputs: object | None = None
    step2_result: object | None = None
    step2_dataframe: Any | None = None
    step2_lib: str = "APILIB"
    step2_dataset: str = "_API_ALL_DATA"

    # Selected catalog row (shared between steps 2 and 3)
    selected_catalog_row: object | None = None
    selected_catalog_index: int | None = None
    selected_row_id: str | None = None
    dataset_unique_id: str | None = None

    # Step 3: Profile & Query
    step3_profile_inputs: object | None = None
    step3_profile_result: object | None = None
    step3_query_inputs: object | None = None
    step3_query_result: object | None = None
    step3_query_dataframe: Any | None = None
    step3_search_query: str = ""
    step3_search_year: int | None = None
    step3_search_results: Any | None = None
    step3_selected_endpoint: str = ""
    step3_endpoint_selected: bool = False
    # Per-dataset query fields keyed by ds_unique_id
    step3_query_fields: dict[str, dict[str, str]] = None

    def __post_init__(self):
        if self.step3_query_fields is None:
            self.step3_query_fields = {}

    def reset_after_disconnect(self) -> "WizardState":
        """Clear the active session and all state that depends on it."""
        self.sas_connected = False
        self.sas_status_message = _DEFAULT_STATUS
        self.environment_ready = False
        self.environment_result = None

        self.step2_inputs = None
        self.step2_result = None
        self.step2_dataframe = None
        self.step2_lib = "APILIB"
        self.step2_dataset = "_API_ALL_DATA"
        self.selected_catalog_row = None
        self.selected_catalog_index = None
        self.selected_row_id = None
        self.dataset_unique_id = None

        self.step3_profile_inputs = None
        self.step3_profile_result = None
        self.step3_query_inputs = None
        self.step3_query_result = None
        self.step3_query_dataframe = None
        self.step3_search_query = ""
        self.step3_search_year = None
        self.step3_search_results = None
        self.step3_selected_endpoint = ""
        self.step3_endpoint_selected = False
        self.step3_query_fields = {}
        return self


def result_succeeded(result: object) -> bool:
    """Return whether *result* is a mapping with a truthy ``success`` value."""
    return isinstance(result, dict) and bool(result.get("success"))


def highest_unlocked_step(state: WizardState) -> int:
    """Return the highest zero-based wizard step currently available (0, 1, or 2)."""
    if not state.sas_connected or not state.environment_ready:
        return 0
    # Step 2 is unlocked if the SAS run succeeded OR a cached
    # / pre-existing dataframe is available (no re-run required).
    if not (result_succeeded(state.step2_result) or state.step2_dataframe is not None):
        return 1
    # Step 3 is always unlocked once step 2 has data
    return 2
