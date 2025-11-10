@echo off
REM === תמיד לרוץ מתיקיית הקבצים ===
cd /d "%~dp0"

REM === ננסה להריץ את פייתון בצורה שלא דורשת אדמין ===
REM קודם "py" (הלאנצ’ר), אחרת "python"
where py >nul 2>&1 && (set PY=py) || (set PY=python)

REM === רענון נתונים מהנתב (ללא התקנות גלובליות) ===
%PY% -m pip install --user --quiet requests jsonpath-ng >nul 2>&1
%PY% local_refresh_mofet.py

REM === שרת מקומי ללא אדמין (ננסה 8000, ואם תפוס – 8001) ===
set PORT=8000
start "server8000" /min cmd /c "%PY% -m http.server 8000"
REM המתנה קצרה כדי לראות אם עלה
ping -n 2 127.0.0.1 >nul

REM אם 8000 לא מגיב – ננסה 8001
powershell -NoProfile -Command ^
  "try{(Invoke-WebRequest -UseBasicParsing http://localhost:8000 -TimeoutSec 1) | Out-Null; $true} catch {exit 1}"
if errorlevel 1 (
  set PORT=8001
  start "server8001" /min cmd /c "%PY% -m http.server 8001"
)

REM === פתיחת הדשבורד דרך השרת (לא file:// כדי ש-fecth יעבוד) ===
start "" "http://localhost:%PORT%/dashboard.html"
exit /b
