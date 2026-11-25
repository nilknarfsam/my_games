# CS 2D — Arena Tática (Single-Player com 2 Oponentes)

Jogo de tiro tático em 2D inspirado em *Counter-Strike*, desenvolvido em **Python + Tkinter** (sem dependências externas).

## Destaques

- **Bonecos detalhados vistos de cima**: ombros, colete tático, mochila, botas com passo animado, dois braços segurando a arma, capacete e visor direcionado ao mouse.
- **Som de passos e furtividade (`Shift`)**: seus passos e os dos inimigos emitem áudio e anéis visuais no mapa; segure `Shift` para andar mais devagar (`112 px/s`) **sem fazer barulho**, evitando alertar os bots e permitindo pegá-los de surpresa por trás!
- **Menu inicial e de opções (`Esc`)**: escolha **Dificuldade** (`Fácil`, `Normal`, `Difícil`), **Arma Inicial** (`Rifle Tático`, `Submetralhadora`, `Pistola Pesada`), **Quantidade de Oponentes** (`1` a `4`, padrão `2`) e ative/desative cone de visão, mira laser e som.
- **Movimentação em `WASD`**: `W` (frente/cima), `S` (trás/baixo), `A` (esquerda) e `D` (direita) com deslizamento suave em paredes e caixas.
- **Visão e mira com o mouse**: rotação em 360°, cone de visão 2D recortado em tempo real pelas paredes (`cast_ray`) e mira laser.
- **Tiro e recarga**: botão esquerdo do mouse dispara e tecla `R` recarrega com barra de progresso acima do personagem.
- **Mapa tático médio (`940×600`)**: paredes externas, bunker central, divisórias e caixas de cobertura para caçar e flanquear os oponentes.

## Controles

| Tecla / Botão | Ação |
| --- | --- |
| `W` / `S` / `A` / `D` | Mover na arena |
| `Segurar Shift` | Andar devagar e silencioso (sem passos) |
| `Mouse` | Visão e mira |
| `Botão Esquerdo` | Atirar |
| `R` | Recarregar pente |
| `P` | Pausar / Retomar |
| `Esc` | Abrir Menu / Opções |
| `Enter` | Próximo round |

## Arquivos

- `cs_2d.py`: Interface gráfica (`CS2DApp`) com cone de visão, ondas sonoras de passos, mira personalizada, barra de recarga e placar `CT x TR`.
- `cs_engine.py`: Motor de jogo (`CS2DEngine`), mapa tático (`build_small_map`), raycasting de visão, furtividade com `Shift`, passos, projéteis, munição/recarga e IA dos oponentes.
- `sound_fx.py`: Síntese procedural em memória (`SoundManager`) de passos, tiros e recarga sem arquivos externos.
- `test_cs_engine.py`: Testes unitários cobrindo movimentação, furtividade, passos, mira, disparo, recarga, linha de visão e vitória do round.

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
