"""Connection page for the SAS Census wizard."""

import ast
from pathlib import Path
from typing import Optional
from PyQt6.QtCore import QThread, pyqtSlot
from PyQt6.QtWidgets import (
    QWizardPage,
    QVBoxLayout,
    QHBoxLayout,
    QFormLayout,
    QLineEdit,
    QComboBox,
    QPushButton,
    QLabel,
    QFileDialog,
    QMessageBox,
    QGroupBox,
    QProgressBar,
)

from pyqt6_sas_census.ui.widgets import SasLogWidget, status_label
from pyqt6_sas_census.services.workers import SasWorker
from pyqt6_sas_census.state import WizardState
from pyqt6_sas_census.services.sas_service import SasService, OperationResult
from pyqt6_sas_census import config as cfg


class ConnectionPage(QWizardPage):
    """Page 1: SAS Session - connect to SAS and initialize environment."""

    def __init__(self, state: WizardState, service: SasService, parent=None):
        super().__init__(parent)
        self.setTitle("SAS Session")
        self.setSubTitle(
            "Configure and connect to SAS, then initialize the Census API environment."
        )
        self._state = state
        self._service = service
        self._worker_thread: Optional[QThread] = None
        self._worker: Optional[SasWorker] = None

        self._setup_ui()
        self._load_config_names()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)

        # Two-column layout
        two_col_layout = QHBoxLayout()
        two_col_layout.setSpacing(15)

        # --- Left Column: SAS Connection ---
        conn_group = QGroupBox("SAS Connection")
        conn_group.setFixedSize(500, 150)  # Set a fixed size for the connection group
        conn_layout = QVBoxLayout(conn_group)

        conn_form = QFormLayout()
        conn_form.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)

        # Config file
        self._cfgfile_edit = QLineEdit(cfg.DEFAULT_SAS_CFGFILE)
        self._cfgfile_edit.setPlaceholderText("Path to sascfg_personal.py")
        self._cfgfile_btn = QPushButton("Browse...")
        self._cfgfile_btn.clicked.connect(self._browse_cfgfile)
        cfgfile_layout = QHBoxLayout()
        cfgfile_layout.addWidget(self._cfgfile_edit)
        cfgfile_layout.addWidget(self._cfgfile_btn)
        conn_form.addRow("Config File:", cfgfile_layout)

        # Config name
        self._cfgname_combo = QComboBox()
        self._cfgname_combo.setEditable(True)
        conn_form.addRow("Config Name:", self._cfgname_combo)

        # Add the form to the layout
        conn_layout.addLayout(conn_form)

        # Connect/Disconnect buttons
        conn_btn_layout = QHBoxLayout()
        self._connect_btn = QPushButton("Connect")
        self._connect_btn.clicked.connect(self._on_connect)
        self._disconnect_btn = QPushButton("Disconnect")
        self._disconnect_btn.clicked.connect(self._on_disconnect)
        self._disconnect_btn.setEnabled(False)
        conn_btn_layout.addWidget(self._connect_btn)
        conn_btn_layout.addWidget(self._disconnect_btn)
        conn_btn_layout.addStretch()
        conn_layout.addLayout(conn_btn_layout)

        two_col_layout.addWidget(conn_group, 1)

        # --- Right Column: Environment Initialization ---
        env_group = QGroupBox("Environment Initialization")
        env_group.setFixedSize(500, 150)  # Set a fixed size for the connection group
        env_layout = QVBoxLayout(env_group)

        env_form = QFormLayout()
        env_form.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)

        # Project root
        self._project_root_edit = QLineEdit(str(cfg.SAS_PROJECT_ROOT))
        self._project_root_edit.setPlaceholderText("SAS Census API project root")
        self._project_root_btn = QPushButton("Browse...")
        self._project_root_btn.clicked.connect(self._browse_project_root)
        proj_layout = QHBoxLayout()
        proj_layout.addWidget(self._project_root_edit)
        proj_layout.addWidget(self._project_root_btn)
        env_form.addRow("Project Root:", proj_layout)

        # API Key
        self._api_key_edit = QLineEdit()
        self._api_key_edit.setPlaceholderText("Census API key (optional)")
        self._api_key_edit.setEchoMode(QLineEdit.EchoMode.Password)
        env_form.addRow("API Key:", self._api_key_edit)

        env_layout.addLayout(env_form)

        # Initialize button
        self._init_env_btn = QPushButton("Initialize Environment")
        self._init_env_btn.clicked.connect(self._on_init_env)
        self._init_env_btn.setEnabled(False)
        env_btn_layout = QHBoxLayout()
        env_btn_layout.addStretch()
        env_btn_layout.addWidget(self._init_env_btn)
        env_layout.addLayout(env_btn_layout)

        two_col_layout.addWidget(env_group, 1)

        layout.addLayout(two_col_layout)

        # Progress bar (indeterminate)
        self._progress = QProgressBar()
        self._progress.setRange(0, 0)
        self._progress.setVisible(False)
        self._progress.setTextVisible(False)
        self._progress.setFixedHeight(4)
        layout.addWidget(self._progress)

        # Status
        self._status_label = QLabel("")
        layout.addWidget(self._status_label)

        # Log
        self._log = SasLogWidget()
        layout.addWidget(self._log, 1)  # Stretch to fill remaining space

    def _browse_cfgfile(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "Select SAS Config File", "", "Python Files (*.py);;All Files (*)"
        )
        if path:
            self._cfgfile_edit.setText(path)
            self._load_config_names()

    def _browse_project_root(self) -> None:
        path = QFileDialog.getExistingDirectory(self, "Select Project Root")
        if path:
            self._project_root_edit.setText(path)

    def _load_config_names(self) -> None:
        cfgfile = self._cfgfile_edit.text().strip()
        if not cfgfile or not Path(cfgfile).exists():
            return

        try:
            with open(cfgfile, "r", encoding="utf-8") as f:
                tree = ast.parse(f.read())

            config_names = []
            for node in ast.walk(tree):
                if isinstance(node, ast.Assign):
                    for target in node.targets:
                        if (
                            isinstance(target, ast.Name)
                            and target.id == "SAS_config_names"
                        ):
                            if isinstance(node.value, (ast.List, ast.Tuple)):
                                for elt in node.value.elts:
                                    if isinstance(elt, ast.Constant) and isinstance(
                                        elt.value, str
                                    ):
                                        config_names.append(elt.value)

            self._cfgname_combo.clear()
            self._cfgname_combo.addItems(config_names)
            if config_names:
                self._cfgname_combo.setCurrentIndex(0)
        except Exception:
            pass  # Silently ignore parse errors

    def _on_connect(self) -> None:
        cfgfile = self._cfgfile_edit.text().strip()
        cfgname = self._cfgname_combo.currentText().strip()
        if not cfgname:
            QMessageBox.warning(
                self, "Missing Config", "Please select or enter a SAS config name."
            )
            return

        self._run_worker(
            lambda: self._service.connect(cfgname, cfgfile if cfgfile else None)
        )
        self._connect_btn.setEnabled(False)
        self._disconnect_btn.setEnabled(True)
        self._init_env_btn.setEnabled(True)

    def _on_disconnect(self) -> None:
        self._run_worker(self._service.disconnect)
        self._connect_btn.setEnabled(True)
        self._disconnect_btn.setEnabled(False)
        self._init_env_btn.setEnabled(False)
        # Navigate back to page 1 per spec: disconnect resets the wizard
        wizard = self.wizard()
        if wizard is not None and hasattr(wizard, "_on_disconnect_requested"):
            wizard._on_disconnect_requested()

    def _on_init_env(self) -> None:
        project_root = self._project_root_edit.text().strip()
        api_key = self._api_key_edit.text().strip()
        if not project_root:
            QMessageBox.warning(
                self,
                "Missing Project Root",
                "Please enter the SAS Census API project root.",
            )
            return

        self._run_worker(
            lambda: self._service.initialize_environment(project_root, api_key)
        )

    def _run_worker(self, func) -> None:
        self._progress.setVisible(True)
        self._connect_btn.setEnabled(False)
        self._disconnect_btn.setEnabled(False)
        self._init_env_btn.setEnabled(False)
        self._worker_thread = QThread()
        self._worker = SasWorker(func)
        self._worker.moveToThread(self._worker_thread)
        self._worker_thread.started.connect(self._worker.run)
        self._worker.finished.connect(self._on_worker_finished)
        self._worker.failed.connect(self._on_worker_failed)
        self._worker.finished.connect(self._worker_thread.quit)
        self._worker.failed.connect(self._worker_thread.quit)
        self._worker.finished.connect(self._worker.deleteLater)
        self._worker.failed.connect(self._worker.deleteLater)
        self._worker_thread.finished.connect(self._worker_thread.deleteLater)
        self._worker_thread.start()

    @pyqtSlot(object)
    def _on_worker_finished(self, result: OperationResult) -> None:
        self._progress.setVisible(False)
        self._connect_btn.setEnabled(True)
        self._log.set_log(result.log)
        status_label(
            self._status_label, result.success, "Success" if result.success else "Failed"
        )
        self._update_state_from_result(result)
        # Update buttons AFTER state is updated
        self._disconnect_btn.setEnabled(self._state.sas_connected)
        self._init_env_btn.setEnabled(self._state.sas_connected)

    @pyqtSlot(str)
    def _on_worker_failed(self, error: str) -> None:
        self._progress.setVisible(False)
        self._connect_btn.setEnabled(True)
        self._log.append_log(f"Worker error: {error}")
        status_label(self._status_label, False, f"Worker error: {error}")
        # Update buttons based on current state
        self._disconnect_btn.setEnabled(self._state.sas_connected)
        self._init_env_btn.setEnabled(self._state.sas_connected)

    def _update_state_from_result(self, result: OperationResult) -> None:
        if "Successfully connected" in result.log:
            self._state.sas_connected = True
            self._state.sas_config_file = self._cfgfile_edit.text().strip()
            self._state.sas_config_name = self._cfgname_combo.currentText().strip()
            self._state.sas_status_message = result.log
            self.completeChanged.emit()
        elif "SAS session ended" in result.log:
            self._state.reset_after_disconnect()
            self.completeChanged.emit()
        elif "setup" in result.log.lower() or "initialization" in result.log.lower():
            if result.success:
                self._state.environment_ready = True
                self._state.environment_result = {"success": True, "log": result.log}
                self._state.project_root = self._project_root_edit.text().strip()
                self._state.api_key = self._api_key_edit.text().strip()
                self._state.sas_status_message = "Environment initialized"
                self.completeChanged.emit()

    def isComplete(self) -> bool:
        return self._state.sas_connected and self._state.environment_ready
