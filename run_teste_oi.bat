@echo off
setlocal

title WhatsApp (TESTE) - Enviar OI

REM Forca UTF-8 no console
chcp 65001 >nul
set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8

REM Forca o numero de teste (sem mexer no config.py)
set MERCHAN_TEST_PHONE_E164=+5585986068742

REM Usa a pasta do proprio .bat
set SCRIPT_DIR=%~dp0
cd /d "%SCRIPT_DIR%" || (
  echo ERRO: nao foi possivel acessar a pasta: "%SCRIPT_DIR%"
  pause
  exit /b 1
)

set LOG_FILE=%SCRIPT_DIR%run_teste_oi.log

echo.
echo ============================================================
echo Iniciando TESTE (OI) em %DATE% %TIME%
echo Pasta: %SCRIPT_DIR%
echo Log:   %LOG_FILE%
echo ============================================================
echo.

REM Preferir Python da venv se existir
set PY_EXE=python
if exist "%SCRIPT_DIR%.venv\Scripts\python.exe" set PY_EXE=%SCRIPT_DIR%.venv\Scripts\python.exe

echo Executando: %PY_EXE% teste_envio_oi.py
echo.

"%PY_EXE%" teste_envio_oi.py 1>>"%LOG_FILE%" 2>>&1
set EXIT_CODE=%ERRORLEVEL%

echo.
echo ============================================================
echo Finalizado com codigo: %EXIT_CODE%
echo (Consulte o log para detalhes: %LOG_FILE%)
echo ============================================================
echo.

pause

endlocal
