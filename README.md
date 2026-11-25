# My Games — Coleção de Jogos e Utilitários

Repositório pessoal de jogos 2D e utilitários desenvolvidos em **Python (Tkinter)**, **C++ (Win32)** e **Godot 4**, com foco principal atual no **CS 2D — Modo Single-Player com 2 Oponentes**.

> 📘 **Documentação completa do repositório (arquitetura, regras, parâmetros e testes):** [`docs/DOCUMENTACAO.md`](docs/DOCUMENTACAO.md)

---

## 🎯 Projeto em Destaque: CS 2D — Arena Tática (Single-Player)

Local: [`jogo_cs_2d/`](jogo_cs_2d/README.md)

Um jogo de tiro tático em 2D com visão de cima inspirado em *Counter-Strike*, onde você enfrenta **2 oponentes controlados por IA** em um mapa compacto cheio de paredes e caixas de cobertura.

### Principais mecânicas
- **Movimentação tática (`WASD`)**: deslize pelas paredes e use as coberturas do mapa (`760×540`) sem travar nas quinas.
- **Visão e mira pelo mouse**: cone de visão 2D recortado em tempo real pelas paredes e caixas, acompanhado por linha de mira laser até o cursor.
- **Tiro e recarga (`R`)**: pente com **15 balas**, cadência rápida no botão esquerdo do mouse e recarga de `1.25s` com barra de progresso na tela.
- **2 Oponentes com linha de visão real**: os dois bots patrulham a arena, fazem *strafe* lateral em combate e só atiram quando têm visão direta sua (sem atirar através das paredes).
- **Sistema de Rounds (`CT x TR`)**: elimine os dois oponentes para vencer o round e acompanhar o placar acumulado.

### Controles do CS 2D

| Tecla / Botão | Ação |
| --- | --- |
| `W` | Mover para frente (cima) |
| `S` | Mover para trás (baixo) |
| `A` | Mover para a esquerda |
| `D` | Mover para a direita |
| `Mouse` | Controlar visão e mira 360° |
| `Botão Esquerdo` | Atirar |
| `R` | Recarregar pente (`15` balas) |
| `P` | Pausar / Retomar |
| `Enter` | Iniciar próximo round |

### Como jogar e testar o CS 2D

- **Atalho direto (Windows)**: dê um duplo clique em [`jogar_cs_2d.bat`](jogar_cs_2d.bat) na raiz do repositório (ou execute `.\jogar_cs_2d.bat` no terminal).

```powershell
# Executar direto pelo atalho
.\jogar_cs_2d.bat

# Ou via Python
python .\jogo_cs_2d\cs_2d.py

# Rodar os testes unitários
python -m unittest discover -s jogo_cs_2d -v
```

### Arquitetura do `jogo_cs_2d/`
- [`jogo_cs_2d/cs_engine.py`](jogo_cs_2d/cs_engine.py): Motor 2D puro (`CS2DEngine`), mapa pequeno (`build_small_map`), raycasting de visão, física de colisão, munição/recarga e IA dos 2 oponentes.
- [`jogo_cs_2d/cs_2d.py`](jogo_cs_2d/cs_2d.py): Interface gráfica em Tkinter (`CS2DApp`) com cone de visão, HUD tático e mira personalizada.
- [`jogo_cs_2d/test_cs_engine.py`](jogo_cs_2d/test_cs_engine.py): Testes unitários de movimentação, mira, recarga, linha de visão e rounds.

---

## 🎮 Outros Jogos no Repositório

| Pasta | Projeto | Destaques | Comando para executar |
| --- | --- | --- | --- |
| [`jogo_da_forca/`](jogo_da_forca/README.md) | **Jogo da Forca** | 100 palavras aleatórias com dicas, cronômetro de 20s por letra (conta como erro se acabar) e teclado virtual/físico | `python .\jogo_da_forca\forca.py` |
| [`jogo_de_carro/`](jogo_de_carro/README.md) | **Jogo de Carro (3 Faixas)** | Controle pelas setas, 10 níveis de velocidade jogáveis e carros aleatórios que mudam de estilo e faixa | `python .\jogo_de_carro\carro.py` |
| [`jogo_de_nave/`](jogo_de_nave/README.md) | **Jogo de Nave** | Movimento em 4 direções, 3 corações, 3 níveis de tiro, bombas/armas especiais com limite de 20s e naves malucas | `python .\jogo_de_nave\nave.py` |
| [`jogo_da_cobrinha/`](jogo_da_cobrinha/README.md) | **Jogo da Cobrinha** | Crescimento progressivo, comida bônus, objetos de obstáculo e outras cobras rivais na arena | `python .\jogo_da_cobrinha\cobrinha.py` |

---

## ⏱️ Utilitários (Cronômetros)

- [`python/`](python/README.md): Cronômetro com interface gráfica em **Python + Tkinter**, registro de voltas e atalhos (`Espaço`, `V`, `R`).
  ```powershell
  python .\python\cronometro.py
  ```
- [`cpp/`](cpp/README.md): Mesma aplicação em **C++17 + Win32 API**, com compilação estática via `g++`:
  ```powershell
  .\cpp\build.ps1
  .\cpp\cronometro.exe
  ```

---

## 🌐 Base Futura (Multiplayer em Rede)

- [`jogo_cs_2d_godot/`](jogo_cs_2d_godot/README.md): Estrutura inicial do CS 2D em **Godot 4 (`ENetMultiplayerPeer` / UDP)** com servidor autoritativo e sombras 2D reais, reservada para quando evoluirmos para o modo multiplayer em rede.

---

## 🛠️ Requisitos

- **Jogos e utilitários Python**: Python 3.12+ com `Tkinter` (incluso na instalação padrão do Python no Windows, sem dependências externas).
- **Cronômetro C++**: `g++` (MSYS2 / MinGW) para recompilar via `cpp/build.ps1`.
- **Projeto Godot 4**: Godot 4.2+ (`winget install GodotEngine.GodotEngine`).
