# Xadrez 3D (Three.js + WebGL)

Jogo completo de **Xadrez em 3D** no navegador com **Three.js**, **Vite**, peças Staunton esculpidas proceduralmente (`LatheGeometry` / `ExtrudeGeometry`) e **IA Minimax com poda Alpha-Beta**.

## Recursos

- **Regras oficiais completas**: roque curto e longo, captura *en passant*, promoção de peão com escolha de peça (`♕ ♖ ♗ ♘`), detecção de xeque, xeque-mate, afogamento, repetição tripla, regra dos 50 lances e material insuficiente.
- **Roque intuitivo em 3D**:
  - Selecione o Rei e clique na casa destino (`g1`/`c1`) **ou diretamente na Torre (`h1`/`a1`)** (marcadas com anel dourado).
  - Também funciona selecionando a Torre e clicando no Rei, ou pelos botões **Roque Curto (`O-O`)** e **Roque Longo (`O-O-O`)** na HUD quando disponíveis.
  - Rei e Torre executam animação simultânea em 3D.
- **Modos de jogo e Relógio**:
  - **Contra IA** (de Brancas ou de Pretas) em 3 níveis (**Fácil**, **Média**, **Difícil**) e **2 Jogadores (Local)**.
  - **Relógio configurável**: Sem Limite, **Blitz (5 min)** ou **Rápido (10 min)**.
- **Análise e Assistência**:
  - **Barra de avaliação** da posição em tempo real + botão **Dica de Jogada (`H`)** destacando o lance sugerido em verde no tabuleiro 3D.
  - Câmera orbital livre (arrastar e zoom), botão **Girar Câmera (`C`)**, histórico em notação algébrica (`SAN`), peças capturadas, **Desfazer (`U`)** e áudio procedural (`M`).

## Mapa de Melhorias

Veja o plano completo das próximas fases em [`ROADMAP.md`](ROADMAP.md).

## Como jogar

```powershell
# Pelo atalho na raiz do repositório
.\jogar_xadrez_3d.bat

# Ou manualmente dentro da pasta
cd .\jogo_xadrez_3d
npm install
npm run dev
```

## Testes e Build

```powershell
cd .\jogo_xadrez_3d
npm test
npm run build
```
