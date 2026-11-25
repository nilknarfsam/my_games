# Jogo de Carro — 3 Faixas (Python)

Jogo arcade em Python com Tkinter onde você dirige um carro em uma pista de **3 faixas**, desviando de carros aleatórios que mudam de visual, velocidade e faixa ao longo de **10 níveis jogáveis** (o Nível 1 já inicia na velocidade do antigo Nível 3).

## Arquivos

- `carro.py`: Interface gráfica (`CarroApp`) com pista animada, veículos com estilos variados (`sedan`, `esportivo`, `pickup`, `van`, `taxi`), seletor de níveis (`1`–`10`), pausa e placar.
- `car_game_engine.py`: Lógica das 3 faixas (`CarGameEngine`), configuração dos 10 níveis (`SPEED_LEVELS`), mutação contínua dos carros e spawn/troca de faixa seguros.
- `test_car_game_engine.py`: Testes unitários dos 10 níveis, movimentação, colisão, mutação por nível e garantia de pista sempre passável.

## Controles

- `←` / `→` (ou `A` / `D`): Mudar entre as 3 faixas
- `↑` / `↓`: Avançar / recuar na pista
- `1` a `9` e `0` (nível 10): Selecionar nível de velocidade (`1`–`10`)
- `P` ou `Espaço`: Pausar / Retomar
- `Enter` ou `R`: Reiniciar

## Como executar

```powershell
python carro.py
```

## Como rodar os testes

```powershell
python -m unittest discover -v
```
