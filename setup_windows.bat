@echo off
rem FemtoNews one-time setup for this PC: keep a local copy of the site in sync with GitHub every day.
rem The crawl runs on GitHub Actions; this PC only downloads the result. No Python needed.
setlocal
cd /d "%~dp0"
if not exist logs mkdir logs
echo [1/3] Downloading the latest site from https://linshulang12-u.github.io/FemtoNews ...
call "%~dp0sync_from_github.bat"
if errorlevel 1 echo     Not published yet - keeping the current copy. It will update once GitHub Pages is on.
echo.
echo [2/3] Registering the Windows task "FemtoNews daily sync" (every day 08:17) ...
schtasks /Delete /F /TN "FemtoNews daily update" >nul 2>nul
schtasks /Create /F /SC DAILY /ST 08:17 /TN "FemtoNews daily sync" /TR "\"%~dp0sync_from_github.bat\""
if errorlevel 1 (
  echo     Could not register the task. Tell Claude; the details are above.
  pause
  exit /b 1
)
echo.
echo [3/3] Opening the site ...
start "" "%~dp0FemtoNews.html"
echo.
echo Done. Online: https://linshulang12-u.github.io/FemtoNews/   Local copy: FemtoNews.html (refreshed daily at 08:17)
pause
