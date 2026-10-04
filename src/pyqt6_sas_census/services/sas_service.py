"""Service layer for SAS operations with typed results."""

from dataclasses import dataclass
from typing import Any, Optional
import pandas as pd

from pyqt6_sas_census.sas.programs import (
    build_collect_catalog_code,
    build_profile_code,
    build_query_code,
)


@dataclass
class OperationResult:
    """Result of a SAS operation."""

    success: bool
    log: str = ""
    lst: str = ""
    errors: list[str] | None = None
    warnings: list[str] | None = None
    dataframe: Optional[pd.DataFrame] = None
    metadata: dict | None = None

    def __post_init__(self):
        if self.errors is None:
            self.errors = []
        if self.warnings is None:
            self.warnings = []
        if self.metadata is None:
            self.metadata = {}


class SasService:
    """Service wrapping SAS backend operations."""

    def __init__(self, backend: Any) -> None:
        self.backend = backend

    def connect(self, cfgname: str, cfgfile: str) -> OperationResult:
        ok, msg = self.backend.connect(cfgname, cfgfile)
        return OperationResult(
            success=ok,
            log=msg,
            errors=[] if ok else [msg],
        )

    def disconnect(self) -> OperationResult:
        if not self.backend.is_connected:
            return OperationResult(success=True, log="No active SAS session.")
        msg = self.backend.disconnect()
        return OperationResult(success=True, log=msg)

    def initialize_environment(
        self, project_root: str, api_key: str
    ) -> OperationResult:
        if not self.backend.is_connected:
            return OperationResult(
                success=False,
                log="SAS is not connected.",
                errors=["Not connected"],
            )
        result = self.backend.run_environment_setup(project_root, api_key)
        return OperationResult(
            success=result.get("success", False),
            log=result.get("log", ""),
            lst=result.get("lst", ""),
            errors=result.get("errors", []),
            warnings=result.get("warnings", []),
        )

    def submit_code(self, code: str) -> OperationResult:
        if not self.backend.is_connected:
            return OperationResult(
                success=False,
                log="Cannot execute: No active SASPy session.",
                errors=["No active SAS session"],
            )
        result = self.backend.submit_code(code)
        return OperationResult(
            success=result.get("success", False),
            log=result.get("log", ""),
            lst=result.get("lst", ""),
            errors=result.get("errors", []),
            warnings=result.get("warnings", []),
        )

    def collect_catalog(
        self,
        out_lib: str,
        out_ds: str,
        data_json_url: str,
        report_path: str,
    ) -> OperationResult:
        if not self.backend.is_connected:
            return OperationResult(
                success=False,
                log="Cannot execute: No active SASPy session.",
                errors=["Not connected"],
            )

        code = build_collect_catalog_code(out_lib, out_ds, data_json_url, report_path)
        result = self.submit_code(code)

        if result.success:
            # Fetch the catalog data
            df = self.backend.fetch_dataframe(
                out_ds,
                out_lib,
                ds_opts={
                    "KEEP": "_rowid_ ds_unique_id baseurl c_vintage title description modified Spatial microdata_i"
                },
            )
            if df is not None:
                result.dataframe = df
                result.metadata = {"lib": out_lib, "dataset": out_ds}

        return result

    def profile_dataset(
        self,
        api_listing_lib: str,
        api_listing_ds: str,
        row_id: str,
        report_path: str,
    ) -> OperationResult:
        if not self.backend.is_connected:
            return OperationResult(
                success=False,
                log="Cannot execute: No active SASPy session.",
                errors=["Not connected"],
            )

        code = build_profile_code(api_listing_lib, api_listing_ds, row_id, report_path)
        return self.submit_code(code)

    def submit_query(
        self,
        api_base_url: str,
        get_clause: str,
        for_clause: str,
        in_clause: str,
        dataset_id: str,
        out_dataset: str,
        api_key_ref: str,
        max_var_count: int,
    ) -> OperationResult:
        if not self.backend.is_connected:
            return OperationResult(
                success=False,
                log="Cannot execute: No active SASPy session.",
                errors=["Not connected"],
            )

        code = build_query_code(
            api_base_url,
            get_clause,
            for_clause,
            in_clause,
            dataset_id,
            out_dataset,
            api_key_ref,
            max_var_count,
        )
        result = self.submit_code(code)

        if result.success:
            if "." in out_dataset:
                libref, table_name = out_dataset.split(".", 1)
            else:
                libref, table_name = "WORK", out_dataset
            df = self.backend.fetch_dataframe(table_name, libref)
            if df is not None:
                result.dataframe = df
                result.metadata = {"lib": libref, "dataset": table_name}

        return result

    def fetch_profile_tables(
        self, ds_unique_id: str
    ) -> dict[str, tuple[str, pd.DataFrame]]:
        """Find and fetch profile tables for a dataset unique ID.

        Returns dict mapping label -> (table_name, dataframe).
        """
        if not self.backend.is_connected:
            return {}

        table_names = self.backend.find_step3_tables(ds_unique_id)
        result = {}
        for label, table_name in table_names.items():
            df = self.backend.fetch_dataframe(table_name, "APILIB")
            if df is not None:
                result[label] = (table_name, df)
        return result
