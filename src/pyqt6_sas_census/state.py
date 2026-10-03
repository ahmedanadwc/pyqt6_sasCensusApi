"""Typed application state and page unlock rules for the wizard."""

from dataclasses import dataclass
from typing import Any


_DEFAULT_STATUS = "⚪ SAS Disconnected (Preview & Code Export mode)"


@dataclass
class WizardState:
    """Shared state for the five-step SAS Census wizard."""

    sas_config_file: str = ""
    sas_config_name: str = ""
    sas_connected: bool = False
    sas_status_message: str = _DEFAULT_STATUS
    project_root: str = ""
    api_key: str = ""
    environment_ready: bool = False
    environment_result: object | None = None

    step2_inputs: object | None = None
    step2_result: object | None = None
    step2_dataframe: Any | None = None
    step2_lib: str = "APILIB"
    step2_dataset: str = "_API_ALL_DATA"

    selected_catalog_row: object | None = None
    selected_catalog_index: int | None = None
    selected_row_id: str | None = None
    dataset_unique_id: str | None = None

    step3_inputs: object | None = None
    step3_result: object | None = None

    step4_search_query: str = "sf1"
    step4_year: int | None = None
    step4_results: Any | None = None
    step4_selected_endpoint: str = ""
    endpoint_selected: bool = False

    step5_inputs: object | None = None
    step5_result: object | None = None
    step5_dataframe: Any | None = None

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

        self.step3_inputs = None
        self.step3_result = None

        self.step4_search_query = ""
        self.step4_year = None
        self.step4_results = None
        self.step4_selected_endpoint = ""
        self.endpoint_selected = False

        self.step5_inputs = None
        self.step5_result = None
        self.step5_dataframe = None
        return self


def result_succeeded(result: object) -> bool:
    """Return whether *result* is a mapping with a truthy ``success`` value."""
    return isinstance(result, dict) and bool(result.get("success"))


def highest_unlocked_step(state: WizardState) -> int:
    """Return the highest zero-based wizard step currently available."""
    if not state.sas_connected or not state.environment_ready:
        return 0
    # Step 2 is unlocked if the SAS run succeeded OR a cached
    # / pre-existing dataframe is available (no re-run required).
    if not (
        result_succeeded(state.step2_result)
        or state.step2_dataframe is not None
    ):
        return 1
    if not result_succeeded(state.step3_result):
        return 2
    if not state.endpoint_selected:
        return 3
    return 4
