@echo off
setlocal
cd /d "%~dp0..\jogo_tetris_3d"

if not exist "node_modules" (
    echo Instalando dependencias do Tetris 3D...
    call npm install
    if errorlevel 1 (
        echo Nao foi possivel instalar as dependencias. Verifique se o Node.js esta no PATH.
        pause
        exit /b 1
    )
)

echo Iniciando Tetris 3D no navegador...
call npm run dev
if errorlevel 1 (
    echo.
    echo Nao foi possivel iniciar o Tetris 3D. Verifique se o Node.js/npm esta no PATH.
    pause
    exit /b 1
)
