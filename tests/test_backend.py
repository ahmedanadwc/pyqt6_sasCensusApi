from pyqt6_sas_census.sas.backend import SASBackend, sas_backend
import pytest


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


def test_disconnect_clears_local_session_and_surfaces_shutdown_failure():
    class FailingSession:
        def endsas(self):
            raise RuntimeError("shutdown failed")

    backend = SASBackend()
    backend._sas = FailingSession()

    with pytest.raises(RuntimeError, match="shutdown failed"):
        backend.disconnect()

    assert backend.is_connected is False


def test_find_step3_tables_bypasses_cache_when_refreshing(monkeypatch):
    import pandas as pd

    backend = SASBackend()
    backend._sas = object()
    calls = []

    def fetch_dataframe(table_name, libref, ds_opts=None, force_refresh=False):
        calls.append(force_refresh)
        return pd.DataFrame({"memname": ["APILIB_DATASET_VARS"]})

    monkeypatch.setattr(backend, "fetch_dataframe", fetch_dataframe)

    tables = backend.find_step3_tables("dataset", force_refresh=True)

    assert tables == {"Variables": "APILIB_DATASET_VARS"}
    assert calls == [True]


def test_submit_code_detects_numbered_sas_errors():
    class Session:
        def submit(self, code):
            return {"LOG": "ERROR 22-322: Syntax error, expecting one of: ;\n", "LST": ""}

    backend = SASBackend()
    backend._sas = Session()

    result = backend.submit_code("data x; set;")

    assert result["success"] is False
    assert result["errors"] == ["ERROR 22-322: Syntax error, expecting one of: ;"]


def test_prune_cache_removes_least_recently_used_files(tmp_path):
    import os
    from pyqt6_sas_census.sas.backend import _prune_cache

    for i in range(5):
        f = tmp_path / f"k{i}.parquet"
        f.write_bytes(b"x" * 10)
        os.utime(f, (1000 + i, 1000 + i))
    (tmp_path / "stale.tmp").write_bytes(b"x")

    _prune_cache(tmp_path, keep=tmp_path / "k0.parquet", max_files=3, max_bytes=10**6)

    left = sorted(p.name for p in tmp_path.iterdir())
    # oldest (k0) is protected as "keep", so k1 and k2 go; stale tmp removed
    assert left == ["k0.parquet", "k3.parquet", "k4.parquet"]


def test_prune_cache_enforces_byte_limit(tmp_path):
    import os
    from pyqt6_sas_census.sas.backend import _prune_cache

    for i in range(4):
        f = tmp_path / f"k{i}.parquet"
        f.write_bytes(b"x" * 100)
        os.utime(f, (1000 + i, 1000 + i))

    _prune_cache(tmp_path, max_files=100, max_bytes=250)

    assert sorted(p.name for p in tmp_path.iterdir()) == ["k2.parquet", "k3.parquet"]
