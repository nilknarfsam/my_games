# Xadrez 3D (Three.js + WebGL)

Jogo completo de **Xadrez em 3D** para **PC e Celular** no navegador com **Three.js**, **Vite**, peças Staunton esculpidas proceduralmente (`LatheGeometry` / `ExtrudeGeometry`) e **IA em Web Worker** com **Livro de Aberturas**, **Transposition Table (Zobrist)** e **Quiescence Search**.

## Recursos

- **Compatível com Celular e Touch**:
  - Layout responsivo exclusivo em telas menores (barra compacta superior + barra inferior de ações + gaveta **Opções & Histórico**), câmera adaptada ao modo retrato para exibir o tabuleiro completo e gestos de toque (`arrastar` para orbitar, `pinça` para zoom, `toque` para selecionar/mover).
- **Regras oficiais completas**: roque curto e longo, captura *en passant*, promoção de peão com escolha de peça (`♕ ♖ ♗ ♘`), detecção de xeque, xeque-mate, afogamento, repetição tripla, regra dos 50 lances e material insuficiente.
- **Roque intuitivo em 3D**:
  - Selecione o Rei e clique na casa destino (`g1`/`c1`) **ou diretamente na Torre (`h1`/`a1`)** (marcadas com anel dourado), ou toque nos botões **Roque Curto (`O-O`)** e **Roque Longo (`O-O-O`)**.
- **IA Turbinada em Segundo Plano (`Web Worker`)**:
  - **Livro de aberturas** catalogado com identificação em tempo real na HUD (*Espanhola*, *Italiana*, *Siciliana*, *Francesa*, *Gambito da Dama*, *Índia do Rei*, etc.).
  - **Quiescence Search + Zobrist Transposition Table** para evitar erros táticos em trocas de peças mantendo 60 FPS.
- **Relógio com Incremento & Persistência**:
  - Modos **Contra IA** (Brancas ou Pretas em 3 dificuldades) e **2 Jogadores (Local)**.
  - Relógio com **Sem Limite**, **Blitz 3+2**, **Blitz 5 min**, **Blitz 5+3** e **Rápido 10 min**.
  - **Auto-save** da partida e placar histórico (`V · E · D`) contra a IA salvos em `localStorage`.

## Mapa de Melhorias (inclui Plano Multiplayer)

Veja o planejamento completo das próximas fases — incluindo a arquitetura detalhada da **Fase 3 (Multiplayer em Rede via WebSocket)** — em [`ROADMAP.md`](ROADMAP.md).

## Como jogar (PC e Celular na mesma rede Wi-Fi)

```powershell
# Pelo launcher na raiz
.\launcher\jogar_xadrez_3d.bat

# Ou manualmente dentro da pasta
cd .\jogo_xadrez_3d
npm install
npm run dev
```

Ao iniciar, o Vite exibirá no terminal um endereço **Network** (ex.: `http://192.168.0.15:5174`). Basta abrir esse endereço no navegador do celular (conectado no mesmo Wi-Fi). *Caso o Windows Firewall bloqueie na primeira vez, permita o acesso do Node.js na rede privada.*

## Testes e Build

```powershell
cd .\jogo_xadrez_3d
npm test
npm run build
```
