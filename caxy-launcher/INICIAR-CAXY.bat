@echo off
cd /d "%~dp0"
where py >nul 2>&1
if not errorlevel 1 (
 py -3 caxy_navegador.py
) else (
 where python >nul 2>&1
 if errorlevel 1 (
  echo Instale Python 3 em https://www.python.org/downloads/windows/ e tente novamente.
  pause
  exit /b 1
 )
 python caxy_navegador.py
)
pause
