# CS 2D — Arena Tática (Single-Player com 2 Oponentes)

Jogo de tiro tático em 2D inspirado em *Counter-Strike*, desenvolvido em **Python + Tkinter** (sem dependências externas).

## Destaques

- **Bonecos detalhados vistos de cima**: ombros, colete tático, mochila, botas com passo animado, dois braços segurando a arma, capacete e visor direcionado ao mouse.
- **Menu inicial e de opções (`Esc`)**: escolha **Dificuldade** (`Fácil`, `Normal`, `Difícil`), **Arma Inicial** (`Rifle Tático`, `Submetralhadora`, `Pistola Pesada`), **Quantidade de Oponentes** (`1` a `4`, padrão `2`) e ative/desative cone de visão e mira laser.
- **Movimentação em `WASD`**: `W` (frente/cima), `S` (trás/baixo), `A` (esquerda) e `D` (direita) com deslizamento suave em paredes e caixas.
- **Visão e mira com o mouse**: rotação em 360°, cone de visão 2D recortado em tempo real pelas paredes (`cast_ray`) e mira laser.
- **Tiro e recarga**: botão esquerdo do mouse dispara e tecla `R` recarrega com barra de progresso acima do personagem.
- **Mapa pequeno tático (`760×540`)**: paredes externas, muros laterais e caixas de cobertura para *peek* e troca de tiro.

## Controles

| Tecla / Botão | Ação |
| --- | --- |
| `W` / `S` / `A` / `D` | Mover na arena |
| `Mouse` | Visão e mira |
| `Botão Esquerdo` | Atirar |
| `R` | Recarregar pente |
| `P` | Pausar / Retomar |
| `Enter` | Próximo round |

## Arquivos

- `cs_2d.py`: Interface gráfica (`CS2DApp`) com cone de visão, mira personalizada, barra de recarga e placar `CT x TR`.
- `cs_engine.py`: Motor de jogo (`CS2DEngine`), mapa pequeno (`build_small_map`), raycasting de visão, projéteis, munição/recarga e IA dos 2 oponentes.
- `test_cs_engine.py`: Testes unitários cobrindo movimentação, mira, disparo, recarga, linha de visão e vitória do round.

## Como executar e testar

```powershell
# Pelo atalho na raiz do repositório:
.\jogar_cs_2d.bat

# Ou direto pelo Python:
python .\jogo_cs_2d\cs_2d.py

# Rodar testes unitários:
python -m unittest discover -s jogo_cs_2d -v
```

Veja também a [Documentação Completa do Repositório](../docs/DOCUMENTACAO.md).
