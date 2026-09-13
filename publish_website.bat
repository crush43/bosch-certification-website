@echo off
setlocal
chcp 65001 >nul
cd /d "%~dp0"

echo ============================================
echo Bosch Certification Website - Safe Publish
echo ============================================
echo.
echo Step 1: Synchronize and validate Excel data.
set "NO_PAUSE=1"
call "%~dp0sync_website.bat"
set "SYNC_EXIT=%ERRORLEVEL%"
set "NO_PAUSE="

if not "%SYNC_EXIT%"=="0" (
  echo.
  echo [BLOCKED] Synchronization failed. Nothing will be committed or pushed.
  pause
  exit /b %SYNC_EXIT%
)

where git >nul 2>&1
if errorlevel 1 (
  echo [BLOCKED] Git was not found.
  pause
  exit /b 1
)

git rev-parse --is-inside-work-tree >nul 2>&1
if errorlevel 1 (
  echo [BLOCKED] This folder is not a Git repository. Ask the administrator to configure it first.
  pause
  exit /b 1
)

for /f "delims=" %%B in ('git branch --show-current') do set "CURRENT_BRANCH=%%B"
if /I not "%CURRENT_BRANCH%"=="main" (
  echo [BLOCKED] Current branch is "%CURRENT_BRANCH%". Publishing is only allowed from main.
  pause
  exit /b 1
)

git remote get-url origin >nul 2>&1
if errorlevel 1 (
  echo [BLOCKED] Git remote "origin" is not configured.
  pause
  exit /b 1
)

echo.
echo Step 2: Review the website locally before continuing.
echo Run preview_website.bat in another window and check HOME, ENTER1, ENTER2 and ENTER3.
choice /C YN /N /M "Have you completed the local preview and confirmed the data? [Y/N]: "
if errorlevel 2 (
  echo Publish cancelled. No Git changes were made.
  pause
  exit /b 0
)

echo.
echo Files eligible for the release commit:
git status --short
echo.
choice /C YN /N /M "Stage the approved website files? [Y/N]: "
if errorlevel 2 (
  echo Publish cancelled. No files were staged by this script.
  pause
  exit /b 0
)

git add -- index.html logo.png data assets .github README.md requirements.txt scripts docs DATA_MAPPING.md STEP4_FINAL_REPORT.md config.example.json .gitignore .gitattributes sync.bat sync_website.bat preview_website.bat publish_website.bat
if errorlevel 1 (
  echo [BLOCKED] Git staging failed. Nothing will be pushed.
  pause
  exit /b 1
)

git diff --cached --quiet
if not errorlevel 1 (
  echo Nothing changed in the approved release files.
  pause
  exit /b 0
)

set "COMMIT_MESSAGE="
set /p "COMMIT_MESSAGE=Commit message [Update certification website]: "
if not defined COMMIT_MESSAGE set "COMMIT_MESSAGE=Update certification website"

git commit -m "%COMMIT_MESSAGE%"
if errorlevel 1 (
  echo [BLOCKED] Git commit failed. Nothing will be pushed.
  pause
  exit /b 1
)

echo.
choice /C YN /N /M "Push this commit to origin/main and trigger GitHub Pages? [Y/N]: "
if errorlevel 2 (
  echo Commit created locally. Push cancelled.
  pause
  exit /b 0
)

git push origin main
if errorlevel 1 (
  echo [FAILED] Git push failed. The local commit is preserved.
  pause
  exit /b 1
)

echo.
echo [SUCCESS] Push completed. Check the GitHub Actions deployment before announcing the update.
pause
