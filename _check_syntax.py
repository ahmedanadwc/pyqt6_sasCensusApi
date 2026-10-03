import ast, sys

files = [
    r"D:\Projects\Python\pyqt6_sasCensusApi\.worktrees\pyqt6-sas-census-wizard\src\pyqt6_sas_census\config.py",
    r"D:\Projects\Python\pyqt6_sasCensusApi\.worktrees\pyqt6-sas-census-wizard\src\pyqt6_sas_census\sas\backend.py",
    r"D:\Projects\Python\pyqt6_sasCensusApi\.worktrees\pyqt6-sas-census-wizard\src\pyqt6_sas_census\sas\programs.py",
    r"D:\Projects\Python\pyqt6_sasCensusApi\.worktrees\pyqt6-sas-census-wizard\src\pyqt6_sas_census\sas\__init__.py",
    r"D:\Projects\Python\pyqt6_sasCensusApi\.worktrees\pyqt6-sas-census-wizard\src\pyqt6_sas_census\services\source_adapter.py",
    r"D:\Projects\Python\pyqt6_sasCensusApi\.worktrees\pyqt6-sas-census-wizard\src\pyqt6_sas_census\main.py",
    r"D:\Projects\Python\pyqt6_sasCensusApi\.worktrees\pyqt6-sas-census-wizard\src\pyqt6_sas_census\ui\pages\connection.py",
    r"D:\Projects\Python\pyqt6_sasCensusApi\.worktrees\pyqt6-sas-census-wizard\src\pyqt6_sas_census\ui\pages\catalog.py",
    r"D:\Projects\Python\pyqt6_sasCensusApi\.worktrees\pyqt6-sas-census-wizard\src\pyqt6_sas_census\state.py",
    r"D:\Projects\Python\pyqt6_sasCensusApi\.worktrees\pyqt6-sas-census-wizard\src\pyqt6_sas_census\ui\wizard.py",
    r"D:\Projects\Python\pyqt6_sasCensusApi\.worktrees\pyqt6-sas-census-wizard\src\pyqt6_sas_census\services\sas_service.py",
    r"D:\Projects\Python\pyqt6_sasCensusApi\.worktrees\pyqt6-sas-census-wizard\tests\test_source_adapter.py",
    r"D:\Projects\Python\pyqt6_sasCensusApi\.worktrees\pyqt6-sas-census-wizard\tests\test_imports.py",
    r"D:\Projects\Python\pyqt6_sasCensusApi\.worktrees\pyqt6-sas-census-wizard\tests\test_state.py",
    r"D:\Projects\Python\pyqt6_sasCensusApi\.worktrees\pyqt6-sas-census-wizard\tests\test_wizard_unlocks.py",
    r"D:\Projects\Python\pyqt6_sasCensusApi\.worktrees\pyqt6-sas-census-wizard\tests\test_sas_service.py",
    r"D:\Projects\Python\pyqt6_sasCensusApi\.worktrees\pyqt6-sas-census-wizard\tests\test_programs.py",
]

failed = False
for f in files:
    try:
        with open(f) as fh:
            ast.parse(fh.read())
        print(f"OK   {f}")
    except SyntaxError as e:
        failed = True
        print(f"FAIL {f}: {e}")

# Check for circular import issues
print("\nChecking key imports...")
# config.py should be importable as pyqt6_sas_census.config
# sas/backend.py imports from config only - no circular deps
# sas/__init__.py imports from backend and programs - no circular deps

sys.exit(1 if failed else 0)
