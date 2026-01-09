@echo off
setlocal

title Gerador Mensagens Merchan (TESTE)

REM Forca UTF-8 no console
chcp 65001 >nul
set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8

REM Forca envio para numero de teste (sem mexer no config.py)
set MERCHAN_USE_TEST_PHONE=1
set MERCHAN_TEST_PHONE_E164=+5585986068742
set MERCHAN_MODO_TESTE=1

REM Usa a pasta do proprio .bat
set SCRIPT_DIR=%~dp0
cd /d "%SCRIPT_DIR%" || (
  echo ERRO: nao foi possivel acessar a pasta: "%SCRIPT_DIR%"
  pause
  exit /b 1
)

set LOG_FILE=%SCRIPT_DIR%run_teste.log

echo.
echo ============================================================
echo Iniciando TESTE em %DATE% %TIME%
echo Pasta: %SCRIPT_DIR%
echo Log:   %LOG_FILE%
echo ============================================================
echo.

echo Executando: python main.py --teste
echo.

python main.py --teste 1>>"%LOG_FILE%" 2>>&1
set EXIT_CODE=%ERRORLEVEL%

echo.
echo ============================================================
echo Finalizado com codigo: %EXIT_CODE%
echo (Consulte o log para detalhes: %LOG_FILE%)
echo ============================================================
echo.

pause

endlocal
