@echo off
setlocal
chcp 65001 >nul
cd /d "%~dp0"

echo ============================================
echo Bosch Certification Website - Production Publish
echo ============================================
echo.

where git >nul 2>&1
if errorlevel 1 (
  echo [BLOCKED] Git was not found.
  pause
  exit /b 1
)

git rev-parse --is-inside-work-tree >nul 2>&1
if errorlevel 1 (
  echo [BLOCKED] This folder is not a Git repository.
  pause
  exit /b 1
)

for /f "delims=" %%B in ('git branch --show-current') do set "CURRENT_BRANCH=%%B"
if /I not "%CURRENT_BRANCH%"=="main" (
  echo [BLOCKED] Current branch is "%CURRENT_BRANCH%". Production publishing is only allowed from main.
  pause
  exit /b 1
)

git remote get-url origin >nul 2>&1
if errorlevel 1 (
  echo [BLOCKED] Git remote "origin" is not configured.
  pause
  exit /b 1
)

set "DIRTY="
for /f "delims=" %%S in ('git status --porcelain --untracked-files^=all') do set "DIRTY=1"
if defined DIRTY (
  echo [BLOCKED] The Git working folder already contains changes.
  echo Ask the website administrator to review, commit, or remove them before a production publish.
  git status --short
  pause
  exit /b 1
)

echo Step 1: Update the local main branch without overwriting remote work.
git pull --rebase origin main
if errorlevel 1 (
  echo [BLOCKED] Git pull/rebase failed or found a conflict.
  echo Resolve the Git problem manually. No synchronization or publish was attempted.
  pause
  exit /b 1
)

echo.
echo Step 2: Create and validate a production snapshot from the configured shared Excel source.
set "NO_PAUSE=1"
call "%~dp0sync_website.bat" --production
set "SYNC_EXIT=%ERRORLEVEL%"
set "NO_PAUSE="
if not "%SYNC_EXIT%"=="0" (
  echo.
  echo [BLOCKED] LOCAL SYNC FAILED. Existing website data was not replaced and nothing will be pushed.
  pause
  exit /b %SYNC_EXIT%
)

echo.
echo Step 3: Review the website locally before continuing.
echo Run preview_website.bat in another window and check HOME, ENTER1, ENTER2 and ENTER3.
choice /C YN /N /M "Have you completed the local preview and confirmed the data? [Y/N]: "
if errorlevel 2 (
  echo Publish cancelled. Local synchronization succeeded, but no Git publish was attempted.
  pause
  exit /b 0
)

where py >nul 2>&1
if not errorlevel 1 goto validate_with_py
where python >nul 2>&1
if not errorlevel 1 goto validate_with_python
echo [BLOCKED] Python was not found for final validation.
pause
exit /b 1

:validate_with_py
py -3 scripts\validate_site.py
set "VALIDATE_EXIT=%ERRORLEVEL%"
set "PYTHON_RUNNER=py -3"
goto validation_result

:validate_with_python
python scripts\validate_site.py
set "VALIDATE_EXIT=%ERRORLEVEL%"
set "PYTHON_RUNNER=python"

:validation_result
if not "%VALIDATE_EXIT%"=="0" (
  echo [BLOCKED] Final website validation failed. Nothing will be committed or pushed.
  pause
  exit /b %VALIDATE_EXIT%
)

echo.
echo Step 4: Review files eligible for the release commit.
git status --short
choice /C YN /N /M "Stage the approved website files? [Y/N]: "
if errorlevel 2 (
  echo Publish cancelled. No files were staged by this script.
  pause
  exit /b 0
)

git add -- index.html logo.png data assets .github README.md requirements.txt scripts tests docs DATA_MAPPING.md PROJECT_HANDOFF.md STEP4_FINAL_REPORT.md STEP6_FINAL_REPORT.md STEP7_FINAL_REPORT.md config.example.json .gitignore .gitattributes sync.bat sync_website.bat preview_website.bat publish_website.bat
if errorlevel 1 (
  echo [BLOCKED] Git staging failed. Nothing will be pushed.
  pause
  exit /b 1
)

git diff --cached --check
if errorlevel 1 (
  echo [BLOCKED] Git found invalid staged changes. Nothing will be pushed.
  pause
  exit /b 1
)

git diff --cached --quiet
if not errorlevel 1 (
  echo Nothing changed in the approved release files. No publication was created.
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
choice /C YN /N /M "Push this reviewed commit to origin/main? [Y/N]: "
if errorlevel 2 (
  echo Local commit created. Push cancelled; the online site remains on the previous version.
  pause
  exit /b 0
)

git push origin main
if errorlevel 1 (
  echo [FAILED] LOCAL SYNC SUCCESS / PUBLISH FAILED.
  echo The local commit is preserved. The online site remains on the previous version.
  pause
  exit /b 1
)

git fetch origin main >nul 2>&1
if errorlevel 1 (
  echo [WARNING] Push succeeded, but the remote verification fetch failed.
  pause
  exit /b 1
)

%PYTHON_RUNNER% scripts\record_publish.py
if errorlevel 1 (
  echo [WARNING] PUBLISH SUCCESS / HISTORY RECORD FAILED.
  echo The remote commit exists, but the local publish history requires administrator attention.
  pause
  exit /b 1
)

echo.
echo [SUCCESS] Production data was synchronized, reviewed, committed and pushed.
echo Check the approved hosting platform separately before announcing the website update.
pause
exit /b 0
