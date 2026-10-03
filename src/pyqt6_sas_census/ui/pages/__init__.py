"""Wizard pages package for PyQt6 SAS Census."""

from pyqt6_sas_census.ui.pages.connection import ConnectionPage
from pyqt6_sas_census.ui.pages.catalog import CatalogPage
from pyqt6_sas_census.ui.pages.profile import ProfilePage
from pyqt6_sas_census.ui.pages.search import SearchPage
from pyqt6_sas_census.ui.pages.query import QueryPage

__all__ = [
    "ConnectionPage",
    "CatalogPage",
    "ProfilePage",
    "SearchPage",
    "QueryPage",
]
