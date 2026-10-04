from dataclasses import fields

from pyqt6_sas_census.state import WizardState, highest_unlocked_step, result_succeeded


def test_initial_state_has_configuration_defaults_and_only_connection_unlocked():
    state = WizardState()

    assert state.sas_config_file == ""
    assert state.sas_config_name == ""
    assert state.sas_connected is False
    assert state.environment_ready is False
    assert state.step2_result is None
    assert state.step3_selected_endpoint == ""
    assert state.step3_endpoint_selected is False
    assert highest_unlocked_step(state) == 0
    assert {field.name for field in fields(state)} >= {
        "sas_config_file",
        "sas_config_name",
        "sas_connected",
        "sas_status_message",
        "project_root",
        "api_key",
        "environment_ready",
        "environment_result",
        "step2_inputs",
        "step2_result",
        "step2_dataframe",
        "step2_lib",
        "step2_dataset",
        "selected_catalog_row",
        "selected_catalog_index",
        "selected_row_id",
        "dataset_unique_id",
        "step3_profile_inputs",
        "step3_profile_result",
        "step3_query_inputs",
        "step3_query_result",
        "step3_query_dataframe",
        "step3_search_query",
        "step3_search_year",
        "step3_search_results",
        "step3_selected_endpoint",
        "step3_endpoint_selected",
        "step3_query_fields",
    }


def test_sequential_unlock_requires_connection_environment_and_successful_results():
    state = WizardState(sas_connected=True)
    assert highest_unlocked_step(state) == 0

    state.environment_ready = True
    assert highest_unlocked_step(state) == 1

    state.step2_result = {"success": True}
    assert highest_unlocked_step(state) == 2

    state.step2_dataframe = "cached_frame"
    # Cached dataframe also unlocks step 2 even without step2_result
    state.step2_result = None
    assert highest_unlocked_step(state) == 2

    state.step2_result = {"success": True}
    # Step 3 is always unlocked once step 2 has data
    assert highest_unlocked_step(state) == 2


def test_failed_or_malformed_results_do_not_unlock_next_step():
    state = WizardState(
        sas_connected=True, environment_ready=True, step2_result={"success": False}
    )
    assert highest_unlocked_step(state) == 1

    state.step2_result = None
    assert highest_unlocked_step(state) == 1
    assert result_succeeded(None) is False
    assert result_succeeded([]) is False
    assert result_succeeded({"success": False}) is False
    assert result_succeeded({"success": True}) is True

    # Cached dataframe unlocks step 2 even without step2_result
    state.step2_dataframe = "cached_frame"
    assert highest_unlocked_step(state) == 2

    state.step2_result = {"success": True}
    state.step3_profile_result = {"success": False}
    state.step3_endpoint_selected = True
    assert highest_unlocked_step(state) == 2


def test_disconnect_reset_clears_active_connection_and_dependent_state():
    state = WizardState(
        sas_config_file="C:/sasv9.cfg",
        sas_config_name="SASApp",
        sas_connected=True,
        sas_status_message="Connected",
        project_root="C:/project",
        api_key="secret",
        environment_ready=True,
        environment_result={"success": True},
        step2_inputs={"out": "catalog"},
        step2_result={"success": True},
        step2_dataframe="frame",
        step2_lib="CUSTOM_LIB",
        step2_dataset="CUSTOM_DATASET",
        selected_catalog_row={"id": "row"},
        selected_catalog_index=3,
        selected_row_id="row",
        dataset_unique_id="dataset",
        step3_profile_inputs={"id": "dataset"},
        step3_profile_result={"success": True},
        step3_search_query="population",
        step3_search_year=2020,
        step3_search_results=["endpoint"],
        step3_selected_endpoint="https://example.test",
        step3_endpoint_selected=True,
        step3_query_inputs={"query": "NAME"},
        step3_query_result={"success": True},
        step3_query_dataframe="query-frame",
    )

    returned = state.reset_after_disconnect()

    assert returned is state
    assert state.sas_connected is False
    assert state.sas_status_message
    assert state.environment_ready is False
    assert state.environment_result is None
    assert state.step2_inputs is None
    assert state.step2_result is None
    assert state.step2_dataframe is None
    assert state.step2_lib == "APILIB"
    assert state.step2_dataset == "_API_ALL_DATA"
    assert state.selected_catalog_row is None
    assert state.selected_catalog_index is None
    assert state.selected_row_id is None
    assert state.dataset_unique_id is None
    assert state.step3_profile_inputs is None
    assert state.step3_profile_result is None
    assert state.step3_query_inputs is None
    assert state.step3_query_result is None
    assert state.step3_query_dataframe is None
    assert state.step3_search_query == ""
    assert state.step3_search_year is None
    assert state.step3_search_results is None
    assert state.step3_selected_endpoint == ""
    assert state.step3_endpoint_selected is False
    assert state.step3_query_fields == {}
    assert state.project_root == "C:/project"
    assert state.api_key == "secret"
    assert state.sas_config_file == "C:/sasv9.cfg"
    assert state.sas_config_name == "SASApp"
    assert highest_unlocked_step(state) == 0
