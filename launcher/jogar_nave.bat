@echo off
setlocal
cd /d "%~dp0..\jogo_de_nave"

where pythonw >nul 2>nul
if %errorlevel%==0 (
    start "" pythonw "%~dp0..\jogo_de_nave\nave.py"
    exit /b 0
)

python "%~dp0..\jogo_de_nave\nave.py"
if errorlevel 1 (
    echo.
    echo Nao foi possivel iniciar o Jogo de Nave. Verifique se o Python 3 esta no PATH.
    pause
    exit /b 1
)
