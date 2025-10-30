#!/bin/bash
# This script is for Linux/macOS. For Windows, change the --add-data separator from ':' to ';'.

# SERVER
pyinstaller --noconfirm --clean --name "ATS-OSS-Server" --icon "build/windows/app.ico" --version-file "build/windows/version_info.txt" --hidden-import "pydantic" --hidden-import "pydantic_core" --hidden-import "anyio" --hidden-import "starlette" --hidden-import "uvicorn" --collect-all "pydantic" --collect-all "pydantic_core" --add-data "ats_oss/workflows:ats_oss/workflows" --add-data "ats_oss/config/config.yaml:ats_oss/config" ats_oss/api/server.py

# GUI
pyinstaller --noconfirm --clean --name "ATS-OSS-GUI" --icon "build/windows/app.ico" --version-file "build/windows/version_info.txt" --hidden-import "PySide6" --collect-all "PySide6" --collect-submodules "PySide6" --collect-data "PySide6" --add-data "ats_oss/workflows:ats_oss/workflows" --add-data "ats_oss/config/config.yaml:ats_oss/config" ats_oss/gui/app.py
