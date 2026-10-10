from pyqt6_sas_census.services.sas_service import SasService, OperationResult


class FakeBackend:
    is_connected = False

    def connect(self, cfgname=None, cfgfile=None):
        self.is_connected = True
        return True, "connected"

    def disconnect(self):
        self.is_connected = False
        return "ended"

    def run_environment_setup(self, project_root, api_key):
        return {"success": True, "log": "setup"}

    def submit_code(self, code):
        return {"success": True, "log": code, "errors": [], "warnings": []}

    def fetch_dataframe(self, table_name, libref="WORK", ds_opts=None):
        return None


def test_service_profile_table_refresh_bypasses_backend_cache():
    backend = FakeBackend()
    backend.is_connected = True
    find_calls = []

    def find_tables(ds_unique_id, force_refresh=False):
        find_calls.append(force_refresh)
        return {"variables": "vars"}

    backend.find_step3_tables = find_tables
    calls = []

    def fetch_dataframe(table_name, libref="WORK", ds_opts=None, force_refresh=False):
        calls.append(force_refresh)
        return None

    backend.fetch_dataframe = fetch_dataframe
    service = SasService(backend)

    service.fetch_profile_tables("dataset-id", force_refresh=True)

    assert find_calls == [True]
    assert calls == [True]


def test_service_disconnect_reports_backend_failure():
    backend = FakeBackend()
    backend.is_connected = True

    def disconnect():
        backend.is_connected = False
        raise RuntimeError("SAS session could not be closed")

    backend.disconnect = disconnect
    result = SasService(backend).disconnect()

    assert result.success is False
    assert result.errors == ["SAS session could not be closed"]
    assert result.metadata["session_cleared"] is True


def test_service_allows_only_one_in_flight_backend_operation():
    service = SasService(FakeBackend())

    assert service.try_begin_operation() is True
    assert service.try_begin_operation() is False

    assert service.run_reserved_operation(lambda: "completed") == "completed"

    assert service.try_begin_operation() is True
    service.end_operation()


def test_service_releases_operation_reservation_when_operation_fails():
    service = SasService(FakeBackend())
    assert service.try_begin_operation() is True

    def fail():
        raise RuntimeError("operation failed")

    try:
        service.run_reserved_operation(fail)
    except RuntimeError as exc:
        assert str(exc) == "operation failed"
    else:
        raise AssertionError("the operation failure should be propagated")

    assert service.try_begin_operation() is True
    service.end_operation()


def test_service_connects_and_initializes():
    service = SasService(FakeBackend())
    result = service.connect("oda", "cfg.py")
    assert result.success is True
    assert service.backend.is_connected is True
    result = service.initialize_environment("C:\\project", "")
    assert result.success is True


def test_service_rejects_sas_operations_when_disconnected():
    service = SasService(FakeBackend())
    result = service.submit_code("proc datasets; run;")
    assert result.success is False
    assert "no active sas session" in result.errors[0].lower()


def test_service_collect_catalog_generates_correct_code():
    from pyqt6_sas_census.sas.programs import build_collect_catalog_code

    backend = FakeBackend()
    backend.submit_code = lambda code: {
        "success": True,
        "log": code,
        "errors": [],
        "warnings": [],
    }
    backend.fetch_dataframe = lambda *args, **kwargs: None

    service = SasService(backend)
    service.connect("oda", "cfg.py")
    service.initialize_environment("C:\\project", "")

    result = service.collect_catalog(
        out_lib="APILIB",
        out_ds="_API_ALL_DATA",
        data_json_url="https://api.census.gov/data.json",
        report_path="&g_outputRoot",
    )
    assert result.success is True
    assert "%censusapi_getAllDataSets" in result.log


def test_service_profile_dataset_generates_correct_code():
    from pyqt6_sas_census.sas.programs import build_profile_code

    backend = FakeBackend()
    backend.submit_code = lambda code: {
        "success": True,
        "log": code,
        "errors": [],
        "warnings": [],
    }
    backend.fetch_dataframe = lambda *args, **kwargs: None

    service = SasService(backend)
    service.connect("oda", "cfg.py")
    service.initialize_environment("C:\\project", "")

    result = service.profile_dataset(
        api_listing_lib="APILIB",
        api_listing_ds="_API_ALL_DATA",
        row_id="3",
        report_path="&g_outputRoot",
    )
    assert result.success is True
    assert "%censusapi_getDsFullInfo" in result.log


def test_service_submit_query_generates_correct_code():
    from pyqt6_sas_census.sas.programs import build_query_code

    backend = FakeBackend()
    backend.submit_code = lambda code: {
        "success": True,
        "log": code,
        "errors": [],
        "warnings": [],
    }
    backend.fetch_dataframe = lambda *args, **kwargs: None

    service = SasService(backend)
    service.connect("oda", "cfg.py")
    service.initialize_environment("C:\\project", "")

    result = service.submit_query(
        api_base_url="https://api.census.gov/data/2000/dec/sf1?",
        get_clause="get=NAME",
        for_clause="for=state:*",
        in_clause="in=",
        dataset_id="_114_dec_2000",
        out_dataset="work.sf1_response",
        api_key_ref="&g_apiKey",
        max_var_count=50,
    )
    assert result.success is True
    assert "%censusapi_submitDataApiQuery" in result.log


def _query_args():
    return dict(
        api_base_url="https://api.census.gov/data/2000/dec/sf1?",
        get_clause="get=NAME",
        for_clause="for=state:*",
        in_clause="in=",
        dataset_id="_114_dec_2000",
        out_dataset="work.sf1_response",
        api_key_ref="&g_apiKey",
        max_var_count=50,
    )


def test_service_submit_query_caps_rows_and_flags_truncation():
    import pandas as pd

    calls = []
    backend = FakeBackend()

    def fetch(table_name, libref="WORK", ds_opts=None):
        calls.append(ds_opts)
        return pd.DataFrame({"a": range(1001)})

    backend.fetch_dataframe = fetch
    service = SasService(backend)
    service.connect("oda", "cfg.py")

    result = service.submit_query(**_query_args(), max_rows=1000)

    assert calls == [{"obs": 1001}]
    assert len(result.dataframe) == 1000
    assert result.metadata["truncated"] is True


def test_service_submit_query_under_cap_is_not_truncated():
    import pandas as pd

    backend = FakeBackend()
    backend.fetch_dataframe = lambda *a, **k: pd.DataFrame({"a": range(10)})
    service = SasService(backend)
    service.connect("oda", "cfg.py")

    result = service.submit_query(**_query_args(), max_rows=1000)

    assert len(result.dataframe) == 10
    assert result.metadata["truncated"] is False
