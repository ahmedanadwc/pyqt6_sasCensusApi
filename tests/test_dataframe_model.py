import pandas as pd
import pytest
from PyQt6.QtCore import Qt

from pyqt6_sas_census.models.dataframe_model import DataFrameModel


def test_dataframe_model_exposes_shape_and_values(qtbot):
    model = DataFrameModel(pd.DataFrame({"id": [1], "title": ["Census"]}))
    assert model.rowCount() == 1
    assert model.columnCount() == 2
    assert model.headerData(0, Qt.Orientation.Horizontal) == "id"
    assert model.data(model.index(0, 1)) == "Census"


def test_dataframe_model_handles_nulls(qtbot):
    model = DataFrameModel(pd.DataFrame({"a": [1, None], "b": [None, "x"]}))
    assert model.rowCount() == 2
    # Float 1.0 displayed as integer "1" since it's a whole number
    assert model.data(model.index(0, 0)) == "1"
    assert model.data(model.index(1, 0)) == ""
    assert model.data(model.index(0, 1)) == ""
    assert model.data(model.index(1, 1)) == "x"


def test_dataframe_model_set_dataframe_emits_signals(qtbot):
    model = DataFrameModel(pd.DataFrame({"a": [1]}))
    assert model.rowCount() == 1

    with qtbot.waitSignal(model.modelReset):
        model.set_dataframe(pd.DataFrame({"b": [1, 2, 3]}))

    assert model.rowCount() == 3
    assert model.columnCount() == 1
    assert model.headerData(0, Qt.Orientation.Horizontal) == "b"


def test_dataframe_model_row_dict_returns_row_as_dict(qtbot):
    df = pd.DataFrame({"id": [1, 2], "title": ["Census", "ACS"]})
    model = DataFrameModel(df)
    row = model.row_dict(1)
    assert row == {"id": 2, "title": "ACS"}
