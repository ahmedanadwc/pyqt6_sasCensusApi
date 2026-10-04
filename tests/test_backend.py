from pyqt6_sas_census.sas.backend import SASBackend, sas_backend


def test_backend_is_bundled_in_app():
    """SASBackend should come from this app, not the standalone package."""
    from pyqt6_sas_census.sas.backend import SASBackend as AppBackend

    assert SASBackend is AppBackend


def test_sas_backend_singleton_exists():
    assert sas_backend is not None
    assert hasattr(sas_backend, "connect")
    assert hasattr(sas_backend, "submit_code")
    assert hasattr(sas_backend, "run_environment_setup")
    assert hasattr(sas_backend, "fetch_dataframe")
