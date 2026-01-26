@echo off
setlocal

title Gerador Mensagens Merchan

REM Forca UTF-8 no console
chcp 65001 >nul
set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8

REM ============================================================
REM 1. COLE O CAMINHO QUE VOCÊ COPIOU ENTRE AS ASPAS ABAIXO:
set PY_EXE="C:\Users\Andre.Feitosa\AppData\Local\Python\pythoncore-3.14-64\python.exe"
REM ============================================================

REM Usa a pasta do próprio .bat
set SCRIPT_DIR=%~dp0
cd /d "%SCRIPT_DIR%" || (
    echo ERRO: nao foi possivel acessar a pasta: "%SCRIPT_DIR%"
    pause
    exit /b 1
)

set LOG_FILE=%SCRIPT_DIR%run.log

echo ============================================================
echo Iniciando execucao em %DATE% %TIME%
echo Executando: %PY_EXE% main.py
echo ============================================================

REM Se houver argumento --teste, ele será repassado
set MODE=%~1

REM Executa o script jogando tudo para o log
%PY_EXE% main.py %MODE% 1>>"%LOG_FILE%" 2>>&1
set EXIT_CODE=%ERRORLEVEL%

echo.
echo Finalizado com codigo: %EXIT_CODE%
echo (Consulte o log para detalhes: %LOG_FILE%)
echo ============================================================

if /I "%~1" neq "--silent" pause
endlocal