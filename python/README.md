# Cronômetro em Python

Aplicativo de cronômetro com interface gráfica em Tkinter (biblioteca padrão do Python, sem dependências externas).

## Arquivos

- `cronometro.py`: Interface gráfica (`CronometroApp`) e ponto de entrada do aplicativo.
- `stopwatch_engine.py`: Motor de contagem de precisão (`StopwatchEngine`), registro de voltas (`LapRecord`) e formatação (`format_time`).
- `test_stopwatch_engine.py`: Testes unitários do motor do cronômetro.

## Como executar

```powershell
python cronometro.py
```

## Atalhos de teclado

- `Espaço`: Iniciar / Pausar / Retomar
- `V`: Registrar volta
- `R`: Zerar cronômetro

## Como rodar os testes

```powershell
python -m unittest discover -v
```
