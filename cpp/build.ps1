$ErrorActionPreference = "Stop"

Push-Location $PSScriptRoot
try {
    g++ -std=c++17 -O2 -Wall -Wextra -municode -mwindows -static `
        main.cpp stopwatch_engine.cpp -o cronometro.exe `
        -lcomctl32 -lgdi32

    g++ -std=c++17 -O2 -Wall -Wextra -static `
        test_stopwatch_engine.cpp stopwatch_engine.cpp -o test_stopwatch_engine.exe

    .\test_stopwatch_engine.exe
    Write-Output "Build concluido: $PSScriptRoot\cronometro.exe"
}
finally {
    Pop-Location
}
