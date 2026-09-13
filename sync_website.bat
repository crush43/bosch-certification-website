@echo off
setlocal
chcp 65001 >nul
cd /d "%~dp0"

echo ============================================
echo Bosch Certification Website - Data Sync
echo ============================================
echo.

where py >nul 2>&1
if not errorlevel 1 goto run_with_py

where python >nul 2>&1
if not errorlevel 1 goto run_with_python

echo [ERROR] Python was not found.
echo Install Python 3 and then run: python -m pip install -r requirements.txt
set "SYNC_EXIT=9009"
goto finish

:run_with_py
py -3 scripts\sync_excel.py %*
set "SYNC_EXIT=%ERRORLEVEL%"
goto result

:run_with_python
python scripts\sync_excel.py %*
set "SYNC_EXIT=%ERRORLEVEL%"

:result
echo.
if "%SYNC_EXIT%"=="0" (
  echo [SUCCESS] Website data is ready for local preview.
) else (
  echo [FAILED] Website data was not replaced. Do not publish.
)

:finish
echo.
if not "%NO_PAUSE%"=="1" pause
exit /b %SYNC_EXIT%
