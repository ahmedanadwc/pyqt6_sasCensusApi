"""Cascading Region > Division > State selector dialog (mirrors the Streamlit version)."""

from typing import Callable, List, Optional, Tuple

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QVBoxLayout,
)

from pyqt6_sas_census.geo_lookup import (
    build_selection,
    division_label,
    division_options,
    in_clause,
    load_geo_rows,
    region_label,
    region_options,
    selection_from_in_clause,
    state_label,
    state_options,
)


class GeoSelectorDialog(QDialog):
    """Pick regions, then divisions, then states; OK applies the full paths."""

    def __init__(
        self,
        current_in: str = "",
        on_apply: Optional[Callable[[List[dict], str], None]] = None,
        parent=None,
    ):
        super().__init__(parent)
        self.setWindowTitle("Select Geography")
        self.resize(780, 520)
        self._on_apply = on_apply
        self._current_in = current_in
        self._rows = load_geo_rows()

        initial, unmatched = selection_from_in_clause(self._rows, current_in)
        self._regions: List[str] = list(dict.fromkeys(region_label(r) for r in initial))
        self._divisions: List[str] = list(
            dict.fromkeys(division_label(r) for r in initial)
        )
        self._states: List[str] = list(dict.fromkeys(state_label(r) for r in initial))
        self._unmatched = unmatched

        self._setup_ui()
        self._refresh_lists()

    # === UI ===

    def _make_column(self, title: str) -> Tuple[QGroupBox, QListWidget]:
        group = QGroupBox(title)
        box = QVBoxLayout(group)
        lst = QListWidget()
        lst.setSelectionMode(QListWidget.SelectionMode.NoSelection)
        lst.itemChanged.connect(self._on_item_changed)
        box.addWidget(lst)

        btns = QHBoxLayout()
        all_btn = QPushButton("Select All")
        all_btn.clicked.connect(lambda: self._set_all(lst, Qt.CheckState.Checked))
        clear_btn = QPushButton("Clear")
        clear_btn.clicked.connect(lambda: self._set_all(lst, Qt.CheckState.Unchecked))
        btns.addWidget(all_btn)
        btns.addWidget(clear_btn)
        box.addLayout(btns)
        return group, lst

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Select Census geography hierarchy:"))

        if self._unmatched:
            warn = QLabel(
                "These in= values are not in the lookup and will be dropped on "
                "Apply: " + ", ".join(self._unmatched)
            )
            warn.setWordWrap(True)
            warn.setStyleSheet("color: #b45309;")
            layout.addWidget(warn)

        columns = QHBoxLayout()
        region_group, self._region_list = self._make_column("Regions")
        division_group, self._division_list = self._make_column("Divisions")
        state_group, self._state_list = self._make_column("States")
        for group in (region_group, division_group, state_group):
            columns.addWidget(group, 1)
        layout.addLayout(columns, 1)

        self._count_label = QLabel()
        self._count_label.setStyleSheet("font-weight: bold;")
        layout.addWidget(self._count_label)

        self._in_clause_label = QLabel()
        self._in_clause_label.setWordWrap(True)
        self._in_clause_label.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
        )
        layout.addWidget(self._in_clause_label)

        self._button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        self._button_box.button(QDialogButtonBox.StandardButton.Ok).setText("Apply")
        self._button_box.accepted.connect(self._on_accept)
        self._button_box.rejected.connect(self.reject)
        layout.addWidget(self._button_box)

    # === State handling ===

    @staticmethod
    def _checked(lst: QListWidget) -> List[str]:
        return [
            lst.item(i).text()
            for i in range(lst.count())
            if lst.item(i).checkState() == Qt.CheckState.Checked
        ]

    @staticmethod
    def _fill(lst: QListWidget, options: List[str], selected: List[str]) -> None:
        lst.blockSignals(True)
        lst.clear()
        for opt in options:
            item = QListWidgetItem(opt)
            item.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsUserCheckable)
            item.setCheckState(
                Qt.CheckState.Checked if opt in selected else Qt.CheckState.Unchecked
            )
            lst.addItem(item)
        lst.blockSignals(False)

    def _refresh_lists(self) -> None:
        """Rebuild all three lists from the selection state, pruning orphans."""
        region_opts = region_options(self._rows)
        self._regions = [r for r in self._regions if r in region_opts]
        division_opts = division_options(self._rows, self._regions)
        self._divisions = [d for d in self._divisions if d in division_opts]
        state_opts = state_options(self._rows, self._divisions)
        self._states = [s for s in self._states if s in state_opts]

        self._fill(self._region_list, region_opts, self._regions)
        self._fill(self._division_list, division_opts, self._divisions)
        self._fill(self._state_list, state_opts, self._states)
        self._division_list.setEnabled(bool(self._regions))
        self._state_list.setEnabled(bool(self._divisions))
        self._update_summary()

    def _on_item_changed(self, _item: QListWidgetItem) -> None:
        self._regions = self._checked(self._region_list)
        self._divisions = self._checked(self._division_list)
        self._states = self._checked(self._state_list)
        self._refresh_lists()

    def _set_all(self, lst: QListWidget, state: Qt.CheckState) -> None:
        lst.blockSignals(True)
        for i in range(lst.count()):
            lst.item(i).setCheckState(state)
        lst.blockSignals(False)
        self._on_item_changed(None)  # type: ignore[arg-type]

    def _selection(self) -> List[dict]:
        return build_selection(self._rows, self._regions, self._divisions, self._states)

    def _update_summary(self) -> None:
        selection = self._selection()
        self._count_label.setText(f"{len(selection)} state(s) selected")
        self._in_clause_label.setText(f"IN clause: {in_clause(selection) or '(none)'}")
        self._button_box.button(QDialogButtonBox.StandardButton.Ok).setEnabled(
            bool(selection)
        )

    def _on_accept(self) -> None:
        selection = self._selection()
        if self._on_apply:
            self._on_apply(selection, self._current_in)
        self.accept()


def open_geo_dialog(
    current_in: str, on_apply: Callable[[List[dict], str], None], parent=None
) -> None:
    """Open the geography selector dialog."""
    GeoSelectorDialog(current_in, on_apply, parent).exec()
