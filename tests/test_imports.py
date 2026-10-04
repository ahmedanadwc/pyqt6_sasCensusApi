"""Smoke test to verify all application modules import correctly."""


def test_application_modules_import():
    from pyqt6_sas_census.main import main
    from pyqt6_sas_census.ui.wizard import WizardWindow
    from pyqt6_sas_census.state import WizardState, highest_unlocked_step
    from pyqt6_sas_census.sas.programs import (
        build_collect_catalog_code,
        build_profile_code,
        build_query_code,
    )
    from pyqt6_sas_census.sas.backend import SASBackend, sas_backend
    from pyqt6_sas_census.services.sas_service import SasService, OperationResult
    from pyqt6_sas_census.services.workers import SasWorker
    from pyqt6_sas_census.services.source_adapter import source_modules, source_root
    from pyqt6_sas_census.models.dataframe_model import DataFrameModel
    from pyqt6_sas_census.ui.widgets import (
        SasLogWidget,
        CodePreviewWidget,
        DataFrameWidget,
        status_label,
    )
    from pyqt6_sas_census.ui.pages import (
        ConnectionPage,
        CatalogPage,
        ProfileQueryPage,
    )

    assert callable(main)
    assert WizardWindow is not None
    assert WizardState is not None
    assert highest_unlocked_step is not None
    assert build_collect_catalog_code is not None
    assert build_profile_code is not None
    assert build_query_code is not None
    assert SASBackend is not None
    assert sas_backend is not None
    assert SasService is not None
    assert OperationResult is not None
    assert SasWorker is not None
    assert source_modules is not None
    assert source_root is not None
    assert DataFrameModel is not None
    assert SasLogWidget is not None
    assert CodePreviewWidget is not None
    assert DataFrameWidget is not None
    assert status_label is not None
    assert ConnectionPage is not None
    assert CatalogPage is not None
    assert ProfileQueryPage is not None
