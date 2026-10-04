<#
.SYNOPSIS
    Build Windows executable for PyQt6 SAS Census Wizard using PyInstaller.

.DESCRIPTION
    Creates a standalone Windows executable from the PyQt6 application.
    Requires PyInstaller to be installed (pip install pyinstaller).

.NOTES
    - The application requires a local SAS installation and SASPy configuration
      on the target workstation. This build script only packages Python dependencies.
    - SAS macros must be available at runtime (set SAS_PROJECT_ROOT if not auto-detected).
#>

param()

# Exit on any error
$ErrorActionPreference = "Stop"

# Ensure we're in the project root
$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Definition
Set-Location $projectRoot

Write-Host "Building PyQt6 SAS Census Wizard..." -ForegroundColor Cyan

# Check for PyInstaller
try {
    python -m PyInstaller --version | Out-Null
}
catch {
    Write-Error "PyInstaller not found. Install with: pip install pyinstaller"
    exit 1
}

# Clean previous builds
if (Test-Path "build") {
    Remove-Item -Recurse -Force "build"
    Write-Host "Cleaned previous build directory"
}
if (Test-Path "dist") {
    Remove-Item -Recurse -Force "dist"
    Write-Host "Cleaned previous dist directory"
}
if (Test-Path "PyQt6SasCensus.spec") {
    Remove-Item -Force "PyQt6SasCensus.spec"
    Write-Host "Cleaned previous spec file"
}

# Run PyInstaller
$pyInstallerArgs = @(
    "--noconfirm"
    "--clean"
    "--windowed"
    "--name", "PyQt6SasCensus"
    "app.py"
)

Write-Host "Running PyInstaller with args: $pyInstallerArgs" -ForegroundColor Yellow
python -m PyInstaller @pyInstallerArgs

# Verify output
$exePath = "dist\PyQt6SasCensus\PyQt6SasCensus.exe"
if (Test-Path $exePath) {
    Write-Host "Build successful! Executable: $exePath" -ForegroundColor Green
    Write-Host ""
    Write-Host "To run the application:" -ForegroundColor Cyan
    Write-Host "  $exePath"
    Write-Host ""
    Write-Host "Note: The target workstation must have:" -ForegroundColor Yellow
    Write-Host "  - SAS 9.4 or Viya installed"
    Write-Host "  - SASPy configured (sascfg_personal.py)"
    Write-Host "  - SAS Census API macros available"
}
else {
    Write-Error "Build failed: Executable not found at $exePath"
    exit 1
}