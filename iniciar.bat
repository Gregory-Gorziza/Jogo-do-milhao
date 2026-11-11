@echo off
setlocal
cd /d "%~dp0"

py -3 --version >nul 2>&1
if errorlevel 1 (
    python --version >nul 2>&1
    if errorlevel 1 (
        echo Python nao foi encontrado. Instale o Python 3 e tente novamente.
        goto erro
    )
    python -m venv ".venv"
) else (
    py -3 -m venv ".venv"
)
if errorlevel 1 goto erro

".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 goto erro

echo.
echo Jogo iniciado em http://127.0.0.1:5000
echo Pressione Ctrl+C para encerrar.
".venv\Scripts\python.exe" app.py
if errorlevel 1 goto erro
exit /b 0

:erro
echo.
echo Nao foi possivel iniciar o jogo.
pause
exit /b 1
