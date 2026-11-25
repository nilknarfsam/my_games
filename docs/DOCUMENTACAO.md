# Documentação Completa — My Games

Guia técnico e de uso completo de todos os projetos do repositório `my_games`, com foco principal no **CS 2D — Arena Tática (Single-Player)** e referência detalhada de todos os módulos, controles, testes automatizados e fluxo Git.

---

## 1. Estrutura Geral do Repositório

```text
my_games/
├── jogar_cs_2d.bat               # Atalho direto no Windows para abrir o CS 2D (single-player)
├── jogar_tetris_3d.bat           # Atalho direto no Windows para abrir o Tetris 3D
├── jogar_xadrez_3d.bat           # Atalho direto no Windows para abrir o Xadrez 3D
├── README.md                     # Página inicial com índice de todos os projetos
├── .gitignore                    # Ignora __pycache__, *.exe, .godot/, node_modules/, dist/
├── docs/
│   └── DOCUMENTACAO.md           # Esta documentação completa
├── jogo_tetris_3d/               # Tetris 3D (Three.js + Vite + ES Modules)
│   ├── index.html
│   ├── package.json
│   ├── vite.config.js
│   ├── src/
│   │   ├── main.js
│   │   ├── sound.js
│   │   ├── style.css
│   │   ├── tetris_engine.js
│   │   └── tetris_engine.test.js
│   └── README.md
├── jogo_xadrez_3d/               # Xadrez 3D (Three.js + Vite + IA Minimax)
│   ├── index.html
│   ├── package.json
│   ├── ROADMAP.md
│   ├── vite.config.js
│   ├── src/
│   │   ├── ai_worker.js
│   │   ├── main.js
│   │   ├── openings.js
│   │   ├── piece_meshes.js
│   │   ├── sound.js
│   │   ├── style.css
│   │   ├── chess_engine.js
│   │   └── chess_engine.test.js
│   └── README.md
├── jogo_cs_2d/                   # [FOCO ATUAL] CS 2D Single-Player (Python + Tkinter)
│   ├── cs_2d.py
│   ├── cs_engine.py
│   ├── test_cs_engine.py
│   └── README.md
├── jogo_da_forca/                # Jogo da Forca: 100 palavras + cronômetro de 20s
│   ├── forca.py
│   ├── hangman_engine.py
│   ├── test_hangman_engine.py
│   └── README.md
├── jogo_de_carro/                # Jogo de Carro: 3 faixas, 10 níveis e tráfego dinâmico
│   ├── carro.py
│   ├── car_game_engine.py
│   ├── test_car_game_engine.py
│   └── README.md
├── jogo_de_nave/                 # Jogo de Nave: 4 direções, 3 corações, 3 níveis e bônus 20s
│   ├── nave.py
│   ├── space_game_engine.py
│   ├── test_space_game_engine.py
│   └── README.md
├── jogo_da_cobrinha/             # Jogo da Cobrinha: crescimento, objetos e cobras rivais
│   ├── cobrinha.py
│   ├── snake_game_engine.py
│   ├── test_snake_game_engine.py
│   └── README.md
├── python/                       # Cronômetro em Python (Tkinter)
│   ├── cronometro.py
│   ├── stopwatch_engine.py
│   ├── test_stopwatch_engine.py
│   └── README.md
├── cpp/                          # Cronômetro em C++17 (Win32 API)
│   ├── main.cpp
│   ├── stopwatch_engine.hpp
│   ├── stopwatch_engine.cpp
│   ├── test_stopwatch_engine.cpp
│   ├── build.ps1
│   └── README.md
└── jogo_cs_2d_godot/             # Base futura Multiplayer ENet/UDP em Godot 4
    ├── project.godot
    ├── scenes/
    ├── scripts/
    └── README.md
```

---

## 2. CS 2D — Arena Tática (Single-Player com 2 Oponentes)

**Pasta:** `jogo_cs_2d/`  
**Atalho direto:** `jogar_cs_2d.bat` (na raiz do repositório)

### 2.1 Visão geral da jogabilidade
- Ao abrir o jogo, você passa pelo **Menu & Opções** (`Esc` para reabrir a qualquer momento), podendo escolher:
  - **Dificuldade dos oponentes**: `Fácil`, `Normal` ou `Difícil`;
  - **Arma inicial**: `Rifle Tático` (15 balas, dano 34), `Submetralhadora` (25 balas, dano 22) ou `Pistola Pesada` (9 balas, dano 50);
  - **Quantidade de oponentes**: de `1` a `4` bots (padrão `2`);
  - **Visuais táticos**: ativar/desativar o cone de visão 2D e a mira laser.
- Os personagens são desenhados **vistos de cima** (`_draw_topdown_soldier`): sombra no chão, botas animadas ao andar, mochila, ombros/colete tático, braços segurando a arma selecionada, capacete e visor voltado para o mouse.
- **Passos sonoros e furtividade (`Shift`)**: tanto você quanto os inimigos geram som e anéis visuais ao correr (`SoundRipple` + `SoundManager` via `winsound`). Ao **segurar `Shift`**, você anda mais devagar (`112 px/s`) e **sem emitir passos**, permitindo flanquear e pegar os oponentes de surpresa (bots têm tempo de reação extra quando surpreendidos por trás sem ouvir passos).
- O mapa expandido (`940×600`) conta com bunker central, corredores e pilares de cobertura para caçar os oponentes.
- Os movimentos seguem `WASD` com deslizamento suave ao encostar em paredes ou caixas (`_move_circle_with_slide`), e os bots usam `has_line_of_sight` antes de atirar (não atiram através das paredes).

### 2.2 Controles
- `W` / `S` / `A` / `D`: movimentação para frente (cima), trás (baixo), esquerda e direita.
- `Segurar Shift`: andar silenciosamente (mais devagar e sem som de passos).
- `Mouse`: mira e orientação do cone de visão.
- `Botão Esquerdo do Mouse`: disparar (clique único ou segurando).
- `R`: recarregar o pente.
- `P`: pausar ou retomar o round.
- `Esc`: abrir ou fechar o Menu & Opções.
- `Enter`: iniciar o próximo round após vitória ou derrota.

### 2.3 Arquitetura e classes principais (`jogo_cs_2d/`)
- `RectObstacle`: representa paredes (`"wall"`) e caixas (`"crate"`).
- `InputState`: snapshot das teclas `W/A/S/D`, `shift`, posição do mouse, disparo e recarga.
- `SoundRipple`: anel visual de som gerado por passos do jogador (quando não segura `Shift`) e dos bots.
- `SoundManager` (`sound_fx.py`): sintetiza em memória e toca áudio WAV assíncrono de passos, tiros e recarga.
- `Projectile`: projéteis de jogador e dos bots, com checagem por segmento (`segment_intersects_rect`) para evitar atravessar paredes.
- `Opponent`: estado de cada bot (`hp=100`, `ammo=10`, patrulha, investigação de som, *strafe* e recarga).
- `CS2DEngine`: motor independente de interface gráfica, facilitando testes unitários determinísticos (`test_cs_engine.py`) e futuras expansões.
- `CS2DApp` (`jogo_cs_2d/cs_2d.py`): renderiza a arena em `tk.Canvas` (~60 FPS via `after(16, ...)`), HUD de HP/Munição/Furtividade/Oponentes/Placar, cone de visão e barra de recarga.

### 2.4 Parâmetros fáceis de ajustar (`jogo_cs_2d/cs_engine.py`)
- Tamanho da arena: `MAP_WIDTH = 940.0`, `MAP_HEIGHT = 600.0`
- Jogador: `PLAYER_SPEED = 215.0`, `PLAYER_WALK_SPEED = 112.0`, `PLAYER_MAX_HP = 100`, `MAGAZINE_SIZE = 15`, `RELOAD_DURATION_SEC = 1.25`, `PLAYER_FIRE_COOLDOWN = 0.16`
- Áudio / Furtividade: `STEP_INTERVAL_RUN_DIST = 54.0`, `ENEMY_STEP_INTERVAL_DIST = 58.0`, `HEARING_RADIUS = 290.0`
- Oponentes: `ENEMY_COUNT = 2`, `ENEMY_SPEED = 145.0`, `ENEMY_MAX_HP = 100`, `ENEMY_FIRE_COOLDOWN = 0.48`, `ENEMY_MAGAZINE = 10`

---

## 3. Outros Jogos em Python (Tkinter)

### 3.1 Jogo da Forca (`jogo_da_forca/`)
- **Arquivos:** `forca.py` (`ForcaApp`), `hangman_engine.py` (`HangmanEngine`), `test_hangman_engine.py`.
- **Regras:** banco de **100 palavras únicas** divididas em 10 categorias com dicas; até `6` erros; **cronômetro de 20 segundos** por letra (`DEFAULT_TURN_SECONDS = 20`) que registra 1 erro automático se o tempo expirar (`record_timeout`).
- **Controles:** teclado virtual clicável (`A–Z`), teclado físico e `Enter` para sortear nova palavra.

### 3.2 Jogo de Carro — 3 Faixas (`jogo_de_carro/`)
- **Arquivos:** `carro.py` (`CarroApp`), `car_game_engine.py` (`CarGameEngine`), `test_car_game_engine.py`.
- **Regras:** pista de **3 faixas** com **10 níveis de velocidade** (`380 px/s` no Nível 1 até `695 px/s` no Nível 10). Os carros mudam de estilo (`sedan`, `esportivo`, `pickup`, `van`, `taxi`), cor e velocidade continuamente, podendo trocar de faixa mantendo sempre ao menos uma passagem livre.
- **Controles:** `←` / `→` (ou `A` / `D`) para mudar de faixa, `↑` / `↓` para avançar/recuar, `1`–`9` e `0` (nível 10), `P`/`Espaço` (pausa), `Enter`/`R` (reiniciar).

### 3.3 Jogo de Nave (`jogo_de_nave/`)
- **Arquivos:** `nave.py` (`NaveApp`), `space_game_engine.py` (`SpaceGameEngine`), `test_space_game_engine.py`.
- **Regras:** movimentação livre nas 4 direções, **3 vidas em corações**, **3 níveis de tiro** (evolui ao abater inimigos sem morrer e volta ao nível 1 ao perder vida), **bônus de Arma Especial e Bomba com limite de 20 segundos** (`SPECIAL_BONUS_LIMIT_SEC = 20.0`) e inimigos variados (`scout`, `zigzag`, `shooter` e **naves malucas** erráticas).
- **Controles:** setas ou `WASD` (mover), `Espaço` ou **Auto-Tiro** (atirar), `B` (detonar bomba), `P` (pausa), `Enter`/`R` (reiniciar).

### 3.4 Jogo da Cobrinha (`jogo_da_cobrinha/`)
- **Arquivos:** `cobrinha.py` (`CobrinhaApp`), `snake_game_engine.py` (`SnakeGameEngine`), `test_snake_game_engine.py`.
- **Regras:** grade `28×24`, crescimento ao comer (comida normal `+1`, comida bônus dourada a cada 5 acertos `+2`), **14 objetos de obstáculo** no campo e **2 cobras rivais autônomas** que também circulam pela arena.
- **Controles:** setas ou `WASD` (mover com buffer de curvas rápidas), `P`/`Espaço` (pausa), `Enter`/`R` (reiniciar).

---

## 4. Utilitários (Cronômetros)

### 4.1 Cronômetro Python (`python/`)
- **Arquivos:** `cronometro.py` (`CronometroApp`), `stopwatch_engine.py` (`StopwatchEngine`), `test_stopwatch_engine.py`.
- **Recursos:** contagem precisa com `time.perf_counter`, voltas com destaque automático de volta mais rápida/lenta e atalhos `Espaço` (Iniciar/Pausar), `V` (Volta) e `R` (Zerar).

### 4.2 Cronômetro C++ Win32 (`cpp/`)
- **Arquivos:** `main.cpp`, `stopwatch_engine.hpp`, `stopwatch_engine.cpp`, `test_stopwatch_engine.cpp`, `build.ps1`.
- **Recursos:** interface nativa Win32/GDI com *double buffering* e tema escuro equivalente à versão Python.
- **Compilação:** execute `.\cpp\build.ps1` (usa `g++ -std=c++17 -O2 -Wall -Wextra -municode -mwindows -static`).

---

## 5. Jogos 3D WebGL (Three.js + Vite)

### 5.1 Tetris 3D (`jogo_tetris_3d/`)
- **Atalho direto:** `jogar_tetris_3d.bat` (na raiz do repositório).
- **Arquivos principais:** `src/tetris_engine.js` (`TetrisEngine`), `src/tetris_engine.test.js`, `src/main.js`, `src/sound.js`, `index.html`, `src/style.css`.
- **Recursos:** tabuleiro `10×20` em 3D com blocos chanfrados (`RoundedBoxGeometry`), sombras suaves, câmera orbital interativa + 3 presets (`3D Clássica`, `Frontal`, `Dinâmica`), sorteio *7-bag*, *wall-kick*, *lock delay*, peça fantasma (*ghost*), *hold*, partículas na limpeza de linhas, recorde em `localStorage` e áudio procedural via Web Audio API.

### 5.2 Xadrez 3D (`jogo_xadrez_3d/`)
- **Atalho direto:** `launcher/jogar_xadrez_3d.bat` (ou `npm run dev` dentro da pasta).
- **Arquivos principais:** `src/chess_engine.js` (`ChessEngine`, `chooseAIMove`), `src/openings.js`, `src/ai_worker.js`, `src/chess_engine.test.js`, `src/piece_meshes.js`, `src/main.js`, `src/sound.js`, `index.html`, `src/style.css`, `vite.config.js`, `ROADMAP.md`.
- **Recursos:** peças Staunton esculpidas em 3D (`LatheGeometry` e `ExtrudeGeometry`), **suporte completo para Celular e Touch** (HUD responsiva com gaveta de opções, câmera adaptativa em retrato e `host: true` no Vite para abrir via Wi-Fi), regras oficiais completas (roque curto/longo com animação simultânea Rei+Torre, *en passant*, promoção de peão, xeque, xeque-mate, afogamento, repetição tripla, regra dos 50 lances e material insuficiente), roque intuitivo (Rei→casa, Rei→Torre, Torre→Rei ou botões contextuais na HUD), **IA em Web Worker com Livro de Aberturas, Quiescence Search e Zobrist Transposition Table**, relógio com incremento Fischer (`3+2`, `5+3`, `5 min`, `10 min`), barra de avaliação, dica de jogada (`H`), auto-save e placar `V · E · D` em `localStorage`, modo **Contra IA** (3 dificuldades) e **2 Jogadores (Local)**, histórico em notação algébrica (`SAN`) e Desfazer (`U`).
- **Multiplayer em Rede (Planejado — Fase 3):** arquitetura detalhada em `jogo_xadrez_3d/ROADMAP.md` prevendo servidor WebSocket autoritativo (`ws` + `ChessEngine`), salas por código curto e sincronização de relógio/lances para LAN e Internet.

---

## 6. Base Futura Multiplayer em Godot 4 (`jogo_cs_2d_godot/`)

- Utiliza **Godot 4.2+** (testado na importação headless com **Godot 4.7.2**) e **`ENetMultiplayerPeer` (UDP)** com servidor autoritativo.
- Inclui lobby Host/Cliente, `MultiplayerSpawner`, `MultiplayerSynchronizer`, sombras 2D com `PointLight2D` + `LightOccluder2D` e opção de incluir os 2 bots oponentes.
- Para abrir no editor:
  ```powershell
  godot --editor --path .\jogo_cs_2d_godot
  ```

---

## 7. Testes Automatizados

Todos os motores de lógica dos jogos e cronômetros são desacoplados da interface gráfica e possuem testes unitários:

```powershell
# Node.js (Jogos 3D): testes unitários e build de produção
cd .\jogo_tetris_3d; npm test; npm run build; cd ..
cd .\jogo_xadrez_3d; npm test; npm run build; cd ..

# Python: rodar testes de cada módulo
python -m unittest discover -s jogo_cs_2d -v
python -m unittest discover -s jogo_da_forca -v
python -m unittest discover -s jogo_de_carro -v
python -m unittest discover -s jogo_de_nave -v
python -m unittest discover -s jogo_da_cobrinha -v
python -m unittest discover -s python -v

# C++: compilar e executar suíte de testes
.\cpp\build.ps1

# Godot 4: validação headless de importação e carregamento
godot_console --path .\jogo_cs_2d_godot --headless --import --quit
```

---

## 8. Fluxo Git Padrão (Branches + Pull Request)

Adotamos o fluxo de **branch de feature + Pull Request** para testar novas melhorias antes do merge na `main`:

```powershell
# 1. Criar uma branch a partir da main atualizada
git checkout main
git pull origin main
git checkout -b feat/nome-da-melhoria

# 2. Implementar, rodar testes e build
# (ex.: npm test && npm run build)

# 3. Commitar, enviar a branch e abrir Pull Request via GitHub CLI
git add .
git commit -m "Descricao clara da melhoria"
git push -u origin feat/nome-da-melhoria
gh pr create --base main --head feat/nome-da-melhoria --title "Titulo da PR" --body "Resumo e checklist de testes"
```
