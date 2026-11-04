@echo off
rem FemtoNews: download the latest FemtoNews.html from the GitHub Pages site (the crawl itself runs on GitHub).
rem Windows Task Scheduler runs this every day. Needs only curl.exe, built into Windows 10/11.
setlocal
cd /d "%~dp0"
if not exist logs mkdir logs
set URL=https://linshulang12-u.github.io/FemtoNews/FemtoNews.html
echo ==== %date% %time% ==== >> logs\sync.log
curl.exe -fsSL --retry 3 --max-time 120 -o FemtoNews.download "%URL%" >> logs\sync.log 2>&1
if errorlevel 1 (
  echo download failed, kept the previous FemtoNews.html >> logs\sync.log
  if exist FemtoNews.download del FemtoNews.download
  exit /b 1
)
move /Y FemtoNews.download FemtoNews.html >nul
echo updated FemtoNews.html >> logs\sync.log
exit /b 0
