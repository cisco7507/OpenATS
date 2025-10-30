# PowerShell Build Script for ATS-OSS on Windows (ARM64)
#
# Description:
# This script packages the ATS-OSS application into standalone executables
# for the FastAPI server and the PyQt6 GUI for Windows on ARM64.
#
# Pre-requisites:
# 1.  Windows 11 (ARM64 version).
# 2.  Python 3.11+ (ARM64 version) installed and in PATH.
# 3.  All project dependencies from `requirements.txt` installed (`pip install -r requirements.txt`).
# 4.  PyInstaller installed (`pip install pyinstaller`).
# 5.  `ffmpeg` executable must be available in the system's PATH.
#
# Usage:
# Run this script from the project root directory in a PowerShell terminal:
# .\build.ps1
#

# --- Configuration ---
$AppName = "ATS-OSS"
$ServerExeName = "ats_oss_server"
$GuiExeName = "ats_oss_gui"
$DistPath = "dist"
$BuildPath = "build/pyinstaller_temp" # Temporary build files
$IconPath = "build/windows/app.ico"
$VersionFile = "build/windows/version_info.txt"

# --- Build Steps ---

# Clean previous builds
Write-Host "Cleaning up previous build directories..."
if (Test-Path $DistPath) { Remove-Item -Recurse -Force $DistPath }
if (Test-Path $BuildPath) { Remove-Item -Recurse -Force $BuildPath }

# Build the FastAPI Server
Write-Host "Building the FastAPI server executable..."
pyinstaller --name $ServerExeName `
    --onefile `
    --target-architecture arm64 `
    --distpath $DistPath `
    --workpath $BuildPath `
    --add-data "ats_oss/workflows;ats_oss/workflows" `
    --add-data "config.yaml;." `
    --hidden-import "ats_oss.api.routes_workflows" `
    --hidden-import "ats_oss.api.routes_jobs" `
    --version-file $VersionFile `
    ats_oss/api/server.py

# Build the PyQt6 GUI
Write-Host "Building the PyQt6 GUI executable..."
pyinstaller --name $GuiExeName `
    --onefile `
    --windowed `
    --target-architecture arm64 `
    --distpath $DistPath `
    --workpath $BuildPath `
    --icon $IconPath `
    --add-data "ats_oss/workflows;ats_oss/workflows" `
    --add-data "config.yaml;." `
    --version-file $VersionFile `
    ats_oss/gui/app.py

Write-Host "Build complete. Executables are in the '$DistPath' directory."
