@echo off
setlocal
chcp 65001 >nul
cd /d "%~dp0"

echo ============================================
echo Bosch Certification Website - Local Preview
echo ============================================
echo.
echo Open: http://localhost:8080
echo Press Ctrl+C to stop the preview server.
echo.

where py >nul 2>&1
if not errorlevel 1 goto preview_with_py

where python >nul 2>&1
if not errorlevel 1 goto preview_with_python

echo [ERROR] Python was not found.
pause
exit /b 9009

:preview_with_py
if not "%NO_BROWSER%"=="1" start "" "http://localhost:8080"
py -3 -m http.server 8080 --bind 127.0.0.1
goto finish

:preview_with_python
if not "%NO_BROWSER%"=="1" start "" "http://localhost:8080"
python -m http.server 8080 --bind 127.0.0.1

:finish
echo.
echo Preview server stopped.
if not "%NO_PAUSE%"=="1" pause
