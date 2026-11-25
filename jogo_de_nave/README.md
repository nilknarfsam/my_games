# Jogo de Nave (Python)

Jogo de tiro espacial arcade (*shoot 'em up*) em Python com Tkinter:

- **Movimentação completa**: setas `↑ ↓ ← →` (ou `WASD`) para frente, trás, esquerda e direita.
- **3 vidas em corações (`♥ ♥ ♥`)**: escudo temporário ao sofrer dano.
- **3 níveis de tiro**: evolui até o nível 3 conforme você derrota inimigos sem morrer (ou ao coletar bônus de arma); ao perder uma vida, volta para o nível 1.
- **Bônus na tela com limite de 20 segundos**:
  - **Arma Especial (`ARMA`)**: disparo quíntuplo por até **20 segundos**.
  - **Bomba (`BOMB`)**: detonação em área com a tecla `B` com prazo de **20 segundos** para uso.
- **Inimigos aleatórios e Naves Malucas**: caças comuns, zigue-zague, atiradores e **naves malucas** rápidas e imprevisíveis difíceis de acertar.

## Arquivos

- `nave.py`: Interface gráfica (`NaveApp`) com campo estelar animado, HUD com corações e temporizadores de 20s.
- `space_game_engine.py`: Lógica do jogo (`SpaceGameEngine`), 3 níveis de tiro, bônus de 20s, inimigos aleatórios e naves malucas.
- `test_space_game_engine.py`: Testes unitários do motor do jogo.

## Controles

- `←` `→` `↑` `↓` (ou `W` `A` `S` `D`): Mover a nave
- `Espaço` (ou botão **Auto-Tiro**): Atirar
- `B`: Detonar Bomba coletada
- `P`: Pausar / Retomar
- `Enter` ou `R`: Reiniciar

## Como executar

```powershell
python nave.py
```

## Como rodar os testes

```powershell
python -m unittest discover -v
```
