import pytest

from pyqt6_sas_census.sas.backend import SASBackend, sas_backend
from pyqt6_sas_census.services.source_adapter import source_modules
from pyqt6_sas_census.services.source_adapter import source_root


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


def test_source_modules_exposes_source_components():
    try:
        root = source_root()
    except ImportError:
        pytest.skip("SAS Census source checkout is not available")
    assert (root / "src" / "py_sascensusapi").is_dir()

    modules = source_modules()

    # SAS backend is now provided by this app
    from pyqt6_sas_census.sas.backend import SASBackend as AppB

    assert modules.SASBackend is AppB
    assert modules.sas_backend is sas_backend
    assert modules.search_datasets
    assert modules.config
    assert modules.config_module


def test_source_modules_reports_missing_source(monkeypatch, tmp_path):
    monkeypatch.setenv("SAS_CENSUS_SOURCE_ROOT", str(tmp_path / "missing"))

    with pytest.raises(ImportError, match="SAS_CENSUS_SOURCE_ROOT"):
        source_modules()
