"""Server settings for the PyQt6 SAS Census application.

Mirrors the defaults provided by ``py_sascensusapi.config`` in the
Standalone source package so the PyQt6 app can prefill UI fields
and supply sensible defaults to ``run_environment_setup`` without
hardcoding them.
"""

import os
from pathlib import Path


def _resolve_sas_project_root() -> Path:
    env_root = os.getenv("SAS_PROJECT_ROOT")
    if env_root and Path(env_root).exists():
        return Path(env_root)

    cwd = Path.cwd()
    candidates = [
        cwd,
        cwd.parent,
        cwd.parent / "sasCensusApi",
        Path.home() / "sasCensusApi",
    ]
    for candidate in candidates:
        if (candidate / "code" / "macros" / "censusapi").exists():
            return candidate.resolve()

    if env_root:
        return Path(env_root)
    return cwd if (cwd / "code").exists() else Path("/sasCensusApi")


def _resolve_sas_cfgfile() -> str:
    env_cfg = os.getenv("SAS_CFGFILE")
    if env_cfg and Path(env_cfg).exists():
        return env_cfg

    home = Path.home()
    for candidate in [
        home / "sascfg_personal.py",
        home / ".config" / "saspy" / "sascfg_personal.py",
        home / ".saspy" / "sascfg_personal.py",
    ]:
        if candidate.exists():
            return str(candidate)

    return ""


# Paths and defaults (mirrors py_sascensusapi.config)
SAS_PROJECT_ROOT = _resolve_sas_project_root()
SAS_CODE_ROOT = SAS_PROJECT_ROOT / "code"
SAS_MACRO_ROOT = SAS_CODE_ROOT / "macros"
SAS_PROGRAM_ROOT = SAS_CODE_ROOT / "programs"
SAS_OUTPUT_ROOT = SAS_PROJECT_ROOT / "output"
SAS_DATA_ROOT = SAS_PROJECT_ROOT / "data"

SAS_MACRO_DIRS = [
    SAS_MACRO_ROOT / "censusapi",
    SAS_MACRO_ROOT / "etl",
    SAS_MACRO_ROOT / "util",
]

DEFAULT_SAS_CFGFILE = _resolve_sas_cfgfile()

DEFAULT_DATA_JSON_URL = "https://api.census.gov/data.json"
DEFAULT_OUT_LIB = "APILIB"
DEFAULT_OUT_DS = "_API_ALL_DATA"
DEFAULT_MAX_VAR_COUNT = 50
