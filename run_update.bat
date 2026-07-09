@echo off
setlocal
cd /d "%~dp0"

if not exist logs mkdir logs

echo [%date% %time%] Iniciando actualizacion > logs\ultimo_update.log
python src\run_pipeline.py --all >> logs\ultimo_update.log 2>&1
set EXIT_CODE=%ERRORLEVEL%
echo [%date% %time%] Finalizado con codigo %EXIT_CODE% >> logs\ultimo_update.log

type logs\ultimo_update.log
if /I "%~1"=="--pause" pause
exit /b %EXIT_CODE%
