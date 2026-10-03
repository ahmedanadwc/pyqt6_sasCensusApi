# Graph Report - pyqt6-sas-census-wizard  (2026-09-29)

## Corpus Check
- Corpus is ~15,692 words - fits in a single context window. You may not need a graph.

## Summary
- 423 nodes · 874 edges · 23 communities (18 shown, 5 thin omitted)
- Extraction: 88% EXTRACTED · 12% INFERRED · 0% AMBIGUOUS · INFERRED: 107 edges (avg confidence: 0.94)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- App Launcher & Imports
- Source Adapter & Tests
- Query Page & Qt Widgets
- Wizard State Machine
- SAS Service
- Graft Hooks
- SAS Log Widget
- Profile Page & UI
- DataFrame Model
- Catalog Page
- Worker Threading
- Resume Evaluator & Scripts
- Connection Page
- Wizard Window & Docs
- Graft Instructions
- Missing Features Query
- Graft MCP Config
- Resume Deps
- Services Package
- SAS Service Ops
- Project Package

## God Nodes (most connected - your core abstractions)
1. `WizardState` - 42 edges
2. `SasService` - 39 edges
3. `SasLogWidget` - 37 edges
4. `OperationResult` - 32 edges
5. `CatalogPage` - 31 edges
6. `ConnectionPage` - 26 edges
7. `QueryPage` - 26 edges
8. `SasWorker` - 23 edges
9. `ProfilePage` - 23 edges
10. `DataFrameWidget` - 23 edges

## Surprising Connections (you probably didn't know these)
- `Source Adapter Reuse Pattern (wrap existing SASBackend/census_catalog instead of copying)` --rationale_for--> `source_modules()`  [INFERRED]
  docs/superpowers/specs/2026-09-15-pyqt6-sas-census-wizard-design.md → src/pyqt6_sas_census/services/source_adapter.py
- `QThread Worker Boundary (GUI thread must not block on SASPy calls)` --rationale_for--> `SasWorker`  [INFERRED]
  docs/superpowers/specs/2026-09-15-pyqt6-sas-census-wizard-design.md → src/pyqt6_sas_census/services/workers.py
- `PyQt6 SAS Census Wizard README` --references--> `SasService`  [EXTRACTED]
  README.md → src/pyqt6_sas_census/services/sas_service.py
- `PyQt6 SAS Census Wizard README` --references--> `SasWorker`  [EXTRACTED]
  README.md → src/pyqt6_sas_census/services/workers.py
- `Sequential Unlock State Machine (mirrors highest_unlocked_step)` --rationale_for--> `highest_unlocked_step()`  [EXTRACTED]
  docs/superpowers/specs/2026-09-15-pyqt6-sas-census-wizard-design.md → src/pyqt6_sas_census/state.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Graft instructions replicated across agent config files** — agents_graft, github_copilot_instructions_graft, gemini_graft [EXTRACTED 1.00]
- **Pages sharing broken status_label pattern** — graphify_out_memory_query_20260920_032326_cb2f2523_which_feature_s__are_missing_in_the_application_connectionpage, graphify_out_memory_query_20260920_032326_cb2f2523_which_feature_s__are_missing_in_the_application_catalogpage, graphify_out_memory_query_20260920_032326_cb2f2523_which_feature_s__are_missing_in_the_application_profilepage, graphify_out_memory_query_20260920_032326_cb2f2523_which_feature_s__are_missing_in_the_application_querypage [EXTRACTED 1.00]

## Communities (23 total, 5 thin omitted)

### Community 0 - "App Launcher & Imports"
Cohesion: 0.09
Nodes (34): Launcher script for the PyQt6 SAS Census Wizard., dataclasses, pandas, pyqt6_qtcore, pyqt6_qtgui, pyqt6_qtwidgets, main(), PyQt6 SAS Census wizard package. (+26 more)

### Community 1 - "Source Adapter & Tests"
Cohesion: 0.05
Nodes (37): Source Adapter Reuse Pattern (wrap existing SASBackend/census_catalog instead of copying), logging, os, pathlib, pytest, re, Path, Server settings for the PyQt6 SAS Census application. Mirrors the defaults… (+29 more)

### Community 2 - "Query Page & Qt Widgets"
Cohesion: 0.06
Nodes (18): QSyntaxHighlighter, QWidget, QWizardPage, QueryPage, Page 5: Query Builder - build and run Census API query with variable chunking., CodePreviewWidget, DataFrameWidget, DataFrame (+10 more)

### Community 3 - "Wizard State Machine"
Cohesion: 0.11
Nodes (30): Sequential Unlock State Machine (mirrors highest_unlocked_step), highest_unlocked_step(), Shared state for the five-step SAS Census wizard., Clear the active session and all state that depends on it., Return whether *result* is a mapping with a truthy ``success`` value., Return the highest zero-based wizard step currently available., result_succeeded(), WizardState (+22 more)

### Community 4 - "SAS Service"
Cohesion: 0.12
Nodes (13): OperationResult, Any, Result of a SAS operation., Service wrapping SAS backend operations., SasService, Smoke test to verify all application modules import correctly., test_application_modules_import(), FakeBackend (+5 more)

### Community 5 - "Graft Hooks"
Cohesion: 0.12
Nodes (24): best(), entry(), { execFileSync }, fromPkg(), fs, globalRoot(), newer(), path (+16 more)

### Community 6 - "SAS Log Widget"
Cohesion: 0.12
Nodes (12): Toggle collapsed/expanded state., Return True if currently expanded., Programmatically expand or collapse the log viewer., Collapsible/expandable read-only SAS log viewer with line count and header…, SasLogWidget, Tests for reusable UI widgets, specifically SasLogWidget., test_sas_log_widget_collapse_and_expand(), test_sas_log_widget_content_and_lines() (+4 more)

### Community 7 - "Profile Page & UI"
Cohesion: 0.12
Nodes (10): QLabel, UI package for PyQt6 SAS Census., ProfilePage, pyqtSlot, QWizardPage, Page 3: Dataset Profile - run getDsFullInfo for selected catalog row., pyqtSlot, Update an existing status label's text and success/failure color. (+2 more)

### Community 8 - "DataFrame Model"
Cohesion: 0.13
Nodes (12): Orientation, QAbstractTableModel, QModelIndex, DataFrameModel, Any, DataFrame, QAbstractTableModel backed by a pandas DataFrame., Models package for PyQt6 SAS Census. (+4 more)

### Community 9 - "Catalog Page"
Cohesion: 0.17
Nodes (6): CatalogPage, pyqtSlot, QWizardPage, Return the first matching value, case-insensitively, as a string., Re-highlight the previously selected row after returning to the page., Page 2: Collect All Datasets - run getAllDataSets and preview catalog.

### Community 10 - "Worker Threading"
Cohesion: 0.13
Nodes (8): QThread Worker Boundary (GUI thread must not block on SASPy calls), QObject, Worker that runs a callable in a separate thread., SasWorker, pyqtSlot, QWizardPage, Page 4: Catalog Search - search Census catalog by keyword and vintage., SearchPage

### Community 11 - "Resume Evaluator & Scripts"
Cohesion: 0.18
Nodes (15): argparse, ast, concurrent_futures, json, collect_files(), DimensionResult, evaluate_resume(), extract_text() (+7 more)

### Community 12 - "Connection Page"
Cohesion: 0.18
Nodes (4): ConnectionPage, pyqtSlot, QWizardPage, Page 1: SAS Session - connect to SAS and initialize environment.

### Community 13 - "Wizard Window & Docs"
Cohesion: 0.19
Nodes (7): PyQt6 SAS Census API Wizard Design Doc, QWizard, PyQt6 SAS Census Wizard README, Main wizard window with five pages and unlock logic., Reset state and navigate back to page 1., WizardWindow, Streamlit_app.py (behavior reference)

### Community 14 - "Graft Instructions"
Cohesion: 0.18
Nodes (12): Graft repo context graph (AGENTS), graft skill, graft ask command, graft build / check lifecycle, graft callers command, graft grep command, graft map command, graft MCP tools (+4 more)

### Community 15 - "Missing Features Query"
Cohesion: 0.46
Nodes (8): CatalogPage, ConnectionPage, pyqt6_sas_census __init__ main() stub, ProfilePage, Query: Which features are missing in the application, QueryPage (missing validation), SearchPage, status_label (broken status feedback)

### Community 16 - "Graft MCP Config"
Cohesion: 0.50
Nodes (3): npx, graft, @nanonets/graft

### Community 17 - "Resume Deps"
Cohesion: 0.67
Nodes (3): pypdf, python-docx, typesafe-sdk

## Ambiguous Edges - Review These
- `QueryPage (missing validation)` → `pyqt6_sas_census __init__ main() stub`  [AMBIGUOUS]
  graphify-out/memory/query_20260920_032326_cb2f2523_which_feature_s__are_missing_in_the_application.md · relation: conceptually_related_to

## Knowledge Gaps
- **21 isolated node(s):** `path`, `fs`, `{ pathToFileURL }`, `{ execFileSync }`, `path` (+16 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 161 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **5 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **What is the exact relationship between `QueryPage (missing validation)` and `pyqt6_sas_census __init__ main() stub`?**
  _Edge tagged AMBIGUOUS (relation: conceptually_related_to) - confidence is low._
- **Why does `SasService` connect `SAS Service` to `App Launcher & Imports`, `Source Adapter & Tests`, `Query Page & Qt Widgets`, `Wizard State Machine`, `Profile Page & UI`, `Catalog Page`, `Worker Threading`, `Connection Page`, `Wizard Window & Docs`?**
  _High betweenness centrality (0.108) - this node is a cross-community bridge._
- **Why does `SasLogWidget` connect `SAS Log Widget` to `App Launcher & Imports`, `Query Page & Qt Widgets`, `SAS Service`, `Profile Page & UI`, `Catalog Page`, `Worker Threading`, `Connection Page`?**
  _High betweenness centrality (0.103) - this node is a cross-community bridge._
- **Why does `DataFrameWidget` connect `Query Page & Qt Widgets` to `App Launcher & Imports`, `SAS Service`, `Profile Page & UI`, `DataFrame Model`, `Catalog Page`?**
  _High betweenness centrality (0.089) - this node is a cross-community bridge._
- **Are the 24 inferred relationships involving `WizardState` (e.g. with `CatalogPage` and `ConnectionPage`) actually correct?**
  _`WizardState` has 24 INFERRED edges - model-reasoned connections that need verification._
- **Are the 13 inferred relationships involving `SasService` (e.g. with `CatalogPage` and `ConnectionPage`) actually correct?**
  _`SasService` has 13 INFERRED edges - model-reasoned connections that need verification._
- **Are the 12 inferred relationships involving `SasLogWidget` (e.g. with `CatalogPage` and `ConnectionPage`) actually correct?**
  _`SasLogWidget` has 12 INFERRED edges - model-reasoned connections that need verification._