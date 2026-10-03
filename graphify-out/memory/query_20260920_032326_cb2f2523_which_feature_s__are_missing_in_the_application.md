---
type: "query"
date: "2026-09-20T03:23:26.095525+00:00"
question: "Which feature(s) are missing in the application"
contributor: "graphify"
source_nodes: ["status_label", "QueryPage", "ConnectionPage", "CatalogPage", "ProfilePage", "SearchPage", "pyqt6_sas_census.__init__.main() stub"]
---

# Q: Which feature(s) are missing in the application

## Answer

Graph traversal + design-doc/code cross-check turned up two real gaps rather than a labeled 'missing feature' node (the graph doesn't track absence directly):

1. Status feedback indicator is broken across the app. widgets.py:status_label() (L342) returns a NEW QLabel; it is never attached to a layout except the one created in each page's _setup_ui(). But ConnectionPage (L254/267), CatalogPage (L242/281), ProfilePage (L170/191), and QueryPage (L178/198/209) all do 'self._status_label = status_label(...)' in _on_worker_finished/_on_worker_failed - this reassigns the Python attribute to a throwaway QLabel that is never added to any layout, so the green/red success-failure message the design doc calls for is silently dropped on every one of those 4 pages. SearchPage imports status_label but never calls it at all - no status feedback exists there.
2. QueryPage (query.py) imports QMessageBox but never calls it, unlike Connection/Profile/Search which use QMessageBox.warning/information for validation feedback. The design doc requires 'visible inline errors' for required fields, numeric ranges, and query fields (design doc L179-182) but QueryPage has no such validation path - bad inputs just fail silently through to a failed macro run.

Also flagged: pyqt6_sas_census/__init__.py has a stub main() that raises NotImplementedError, distinct from the real entry point in main.py - AMBIGUOUS edge (confidence 0.2), likely dead/leftover code.

Everything else in the 5-step wizard (Connection, Catalog, Profile, Search, Query) matches the design doc's feature list - the 'Out of scope' items (remote execution, multi-user auth, browser embedding, Streamlit styling parity) are intentionally excluded, not missing.

## Source Nodes

- status_label
- QueryPage
- ConnectionPage
- CatalogPage
- ProfilePage
- SearchPage
- pyqt6_sas_census.__init__.main() stub