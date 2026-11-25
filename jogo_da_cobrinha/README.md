# Jogo da Cobrinha (Python)

Jogo da Cobrinha clássico em Python com Tkinter, incluindo crescimento progressivo, **obstáculos (objetos)** espalhados pelo campo e **outras cobras rivais** circulando pela arena.

## Arquivos

- `cobrinha.py`: Interface gráfica (`CobrinhaApp`) com grade visual, placar de tamanho/pontos/recorde, cobras rivais coloridas e objetos de obstáculo.
- `snake_game_engine.py`: Motor do jogo (`SnakeGameEngine`), fila de direção para curvas rápidas, crescimento ao comer, obstáculos e IA das cobras rivais (`RivalSnake`).
- `test_snake_game_engine.py`: Testes unitários para crescimento, curvas rápidas, colisões com paredes, objetos e outras cobras.

## Controles

- `←` `→` `↑` `↓` (ou `W` `A` `S` `D`): Mover a cobrinha
- `P` ou `Espaço`: Pausar / Retomar
- `Enter` ou `R`: Reiniciar

## Como executar

```powershell
python cobrinha.py
```

## Como rodar os testes

```powershell
python -m unittest discover -v
```
