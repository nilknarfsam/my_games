# Xadrez 3D (Three.js + WebGL)

Jogo completo de **Xadrez em 3D** no navegador com **Three.js**, **Vite**, peças Staunton esculpidas proceduralmente (`LatheGeometry` / `ExtrudeGeometry`) e **IA em Web Worker** com **Livro de Aberturas**, **Transposition Table (Zobrist)** e **Quiescence Search**.

## Recursos

- **Regras oficiais completas**: roque curto e longo, captura *en passant*, promoção de peão com escolha de peça (`♕ ♖ ♗ ♘`), detecção de xeque, xeque-mate, afogamento, repetição tripla, regra dos 50 lances e material insuficiente.
- **Roque intuitivo em 3D**:
  - Selecione o Rei e clique na casa destino (`g1`/`c1`) **ou diretamente na Torre (`h1`/`a1`)** (marcadas com anel dourado).
  - Também funciona selecionando a Torre e clicando no Rei, ou pelos botões **Roque Curto (`O-O`)** e **Roque Longo (`O-O-O`)** na HUD quando disponíveis.
  - Rei e Torre executam animação simultânea em 3D.
- **IA Turbinada em Segundo Plano (`Web Worker`)**:
  - **Livro de aberturas** catalogado com identificação do nome da abertura em tempo real na HUD (*Espanhola*, *Italiana*, *Siciliana*, *Francesa*, *Gambito da Dama*, *Índia do Rei*, etc.).
  - **Quiescence Search + Zobrist Transposition Table** para evitar erros táticos em trocas de peças sem travar a câmera 3D.
- **Relógio com Incremento & Persistência**:
  - Modos **Contra IA** (de Brancas ou de Pretas em 3 dificuldades) e **2 Jogadores (Local)**.
  - Relógio com **Sem Limite**, **Blitz 3+2**, **Blitz 5 min**, **Blitz 5+3** e **Rápido 10 min**.
  - **Auto-save** da partida em andamento e placar histórico (`V · E · D`) contra a IA salvos em `localStorage`.
- **Análise e Assistência**:
  - **Barra de avaliação** da posição em tempo real + botão **Dica de Jogada (`H`)** destacando o lance sugerido em verde no tabuleiro 3D.
  - Câmera orbital livre (arrastar e zoom), botão **Girar Câmera (`C`)**, histórico em notação algébrica (`SAN`), peças capturadas, **Desfazer (`U`)** e áudio procedural (`M`).

## Mapa de Melhorias

Veja o plano completo das próximas fases em [`ROADMAP.md`](ROADMAP.md).

## Como jogar

```powershell
# Pelo launcher (quando na main / PR #2) ou via npm
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
