# Cronômetro em C++ (Win32)

Aplicativo de cronômetro com interface gráfica nativa do Windows (Win32 API + GDI + Common Controls), sem dependências externas.

## Arquivos

- `main.cpp`: Interface gráfica Win32 em tema escuro (`Cronômetro`).
- `stopwatch_engine.hpp` / `stopwatch_engine.cpp`: Motor de contagem com `std::chrono::steady_clock` (`StopwatchEngine`), registro de voltas (`LapRecord`) e formatação (`format_time`).
- `test_stopwatch_engine.cpp`: Testes unitários do motor em C++.
- `build.ps1`: Script para compilar o aplicativo e rodar os testes unitários.

## Como compilar e executar

```powershell
.\build.ps1
.\cronometro.exe
```

## Atalhos de teclado

- `Espaço`: Iniciar / Pausar / Retomar
- `V`: Registrar volta
- `R`: Zerar cronômetro
