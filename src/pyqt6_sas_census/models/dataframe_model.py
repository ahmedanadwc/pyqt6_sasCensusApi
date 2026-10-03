"""Pandas DataFrame model for Qt views."""

from typing import Any
import pandas as pd
from PyQt6.QtCore import QAbstractTableModel, QModelIndex, Qt


class DataFrameModel(QAbstractTableModel):
    """QAbstractTableModel backed by a pandas DataFrame."""

    def __init__(self, dataframe: pd.DataFrame | None = None, parent=None):
        super().__init__(parent)
        self._dataframe = dataframe if dataframe is not None else pd.DataFrame()

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return len(self._dataframe)

    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return len(self._dataframe.columns)

    def data(self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole) -> Any:
        if not index.isValid():
            return None
        if role == Qt.ItemDataRole.DisplayRole:
            value = self._dataframe.iloc[index.row(), index.column()]
            if pd.isna(value):
                return ""
            return str(value)
        return None

    def headerData(
        self,
        section: int,
        orientation: Qt.Orientation,
        role: int = Qt.ItemDataRole.DisplayRole,
    ) -> Any:
        if role == Qt.ItemDataRole.DisplayRole:
            if orientation == Qt.Orientation.Horizontal:
                return str(self._dataframe.columns[section])
            if orientation == Qt.Orientation.Vertical:
                return str(section)
        return None

    def set_dataframe(self, dataframe: pd.DataFrame) -> None:
        self.beginResetModel()
        self._dataframe = dataframe
        self.endResetModel()

    def row_dict(self, row: int) -> dict:
        if row < 0 or row >= len(self._dataframe):
            return {}
        return self._dataframe.iloc[row].to_dict()
