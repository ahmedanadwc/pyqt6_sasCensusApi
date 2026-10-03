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
