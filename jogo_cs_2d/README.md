# CS 2D — Arena Tática (Python)

Jogo de tiro tático em 2D inspirado em Counter-Strike, feito em Python com Tkinter:

- **Movimentação em WASD**: `W` (frente/cima), `S` (trás/baixo), `A` (esquerda) e `D` (direita).
- **Visão e mira com o mouse**: cone de visão 2D recortado pelas paredes e mira laser até o cursor.
- **Tiro e recarga**: botão esquerdo do mouse atira e tecla `R` recarrega o pente (`15` balas).
- **Mapa pequeno tático**: arena compacta com paredes e caixas de cobertura.
- **2 oponentes**: dois bots com linha de visão real (não atiram através das paredes), movimentação lateral e cobertura.

## Arquivos

- `cs_2d.py`: Interface gráfica (`CS2DApp`) com cone de visão, mira personalizada, placar `CT x TR` e barra de recarga.
- `cs_engine.py`: Física 2D (`CS2DEngine`), mapa pequeno (`build_small_map`), raycasting, controle de munição/recarga e IA dos 2 oponentes.
- `test_cs_engine.py`: Testes unitários para WASD, mira, tiro, recarga com `R`, linha de visão e vitória do round.

## Como executar

```powershell
python cs_2d.py
```

## Como rodar os testes

```powershell
python -m unittest discover -v
```
