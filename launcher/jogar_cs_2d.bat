@echo off
setlocal
cd /d "%~dp0..\jogo_cs_2d"

where pythonw >nul 2>nul
if %errorlevel%==0 (
    start "" pythonw "%~dp0..\jogo_cs_2d\cs_2d.py"
    exit /b 0
)

python "%~dp0..\jogo_cs_2d\cs_2d.py"
if errorlevel 1 (
    echo.
    echo Nao foi possivel iniciar o CS 2D. Verifique se o Python 3 esta no PATH.
    pause
    exit /b 1
)
