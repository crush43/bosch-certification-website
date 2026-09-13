@echo off
rem Compatibility entry point. This script only synchronizes data; it never pushes to GitHub.
call "%~dp0sync_website.bat"
exit /b %ERRORLEVEL%
