"""Wizard pages package for PyQt6 SAS Census."""

from pyqt6_sas_census.ui.pages.catalog import CatalogPage
from pyqt6_sas_census.ui.pages.connection import ConnectionPage
from pyqt6_sas_census.ui.pages.profile_query import ProfileQueryPage

__all__ = [
    "CatalogPage",
    "ConnectionPage",
    "ProfileQueryPage",
]
