@echo off
setlocal
cd /d "%~dp0..\jogo_de_carro"

where pythonw >nul 2>nul
if %errorlevel%==0 (
    start "" pythonw "%~dp0..\jogo_de_carro\carro.py"
    exit /b 0
)

python "%~dp0..\jogo_de_carro\carro.py"
if errorlevel 1 (
    echo.
    echo Nao foi possivel iniciar o Jogo de Carro. Verifique se o Python 3 esta no PATH.
    pause
    exit /b 1
)
