@echo off
REM Build single-file EXE for the whichscript opener (no console window)
REM Requires: PyInstaller installed in the active Python environment

setlocal
set SCRIPT_DIR=%~dp0
pushd "%SCRIPT_DIR%.."

pyinstaller --noconsole --onefile "whichscript\open_generating_script.pyw" -n whichscript-open

echo.
echo If successful, your EXE is at: dist\whichscript-open.exe
popd
endlocal

