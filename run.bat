@echo off
setlocal

REM --- Ajuste o caminho caso mude de pasta ---
set SCRIPT_DIR=B:\Trade\Compartilhado\Inteligência de Mercado\Scripts\gerador_mensagens_merchan

cd /d "%SCRIPT_DIR%" || exit /b 1

REM Rodar envio real
python main.py --enviar

endlocal
