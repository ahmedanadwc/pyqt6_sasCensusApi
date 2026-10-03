"""Adapter for reusing the standalone SAS Census API source package.

The SAS backend (``SASBackend`` / ``sas_backend``) is provided by this
application's own ``pyqt6_sas_census.sas.backend`` module so the PyQt6
app does not depend on the standalone ``py_sascensusapi`` package for
SAS session management.  Only the catalog search helper and config
object are still sourced from the standalone package when available.
"""

from dataclasses import dataclass
from pathlib import Path
import os
import sys


@dataclass(frozen=True)
class SourceModules:
    SASBackend: type
    sas_backend: object
    config: object
    config_module: object
    search_datasets: object


def source_root() -> Path:
    """Return the configured source repository root."""
    configured_root = os.getenv("SAS_CENSUS_SOURCE_ROOT")
    if configured_root:
        return Path(configured_root).expanduser()

    adapter_path = Path(__file__).resolve()
    for ancestor in adapter_path.parents:
        candidates = [ancestor]
        try:
            candidates.extend(
                child for child in ancestor.iterdir() if child.is_dir()
            )
        except OSError:
            continue
        for candidate in candidates:
            if (candidate / "src" / "py_sascensusapi").is_dir():
                return candidate

    raise ImportError(
        "Unable to locate the SAS Census source checkout. Set "
        "SAS_CENSUS_SOURCE_ROOT to the source repository root containing "
        "a src\\py_sascensusapi package."
    )


def source_modules() -> SourceModules:
    """Load and return source components for the wizard."""
    root = source_root()
    source_src = root / "src"
    if not (source_src / "py_sascensusapi").is_dir():
        raise ImportError(
            "Unable to locate the SAS Census source package at "
            f"{source_src}. Set SAS_CENSUS_SOURCE_ROOT to the source "
            "repository root containing a src\\py_sascensusapi package."
        )
    source_src_string = str(source_src)
    if source_src_string not in sys.path:
        sys.path.insert(0, source_src_string)

    # SAS backend is provided by this app's own module.
    from pyqt6_sas_census.sas.backend import SASBackend, sas_backend

    # Config and catalog search are still sourced from the standalone
    # package when available.
    try:
        from py_sascensusapi import config
        from py_sascensusapi.census_catalog import search_datasets
    except ImportError:
        config = None
        search_datasets = None  # type: ignore[assignment]

    return SourceModules(
        SASBackend=SASBackend,
        sas_backend=sas_backend,
        config=config,
        search_datasets=search_datasets,
        config_module=config,
    )


def get_config():
    """Return the app config module (standalone or bundled fallback)."""
    try:
        return source_modules().config_module
    except ImportError:
        pass
    try:
        from pyqt6_sas_census import config as bundled
        return bundled
    except ImportError:
        return None


def search_with_fallback(query: str, year: str | None) -> tuple[list[dict], bool]:
    """Search the catalog, falling back to an empty result on network failure.

    Returns (results, was_fallback).  was_fallback is True when the remote
    catalog could not be reached and an empty list is returned instead of
    raising, matching the Streamlit app's search_datasets() fallback path.
    """
    try:
        modules = source_modules()
        if modules.search_datasets is None:
            return [], True
        return modules.search_datasets(query=query, year=year), False
    except Exception:
        # Network or import failure — return empty so the UI can distinguish
        # "no results" from "could not reach catalog".
        return [], True
