# Xadrez 3D (Three.js + WebGL)

Jogo completo de **Xadrez em 3D** no navegador com **Three.js**, **Vite**, peças Staunton esculpidas proceduralmente (`LatheGeometry` / `ExtrudeGeometry`) e **IA Minimax com poda Alpha-Beta**.

## Recursos

- **Regras oficiais completas**: roque curto e longo, captura *en passant*, promoção de peão com escolha de peça (`♕ ♖ ♗ ♘`), detecção de xeque, xeque-mate, afogamento, regra dos 50 lances e material insuficiente.
- **Modos de jogo**:
  - **Contra IA** (jogando de Brancas ou de Pretas) com 3 níveis: **Fácil**, **Média** e **Difícil**.
  - **2 Jogadores (Local)** no mesmo computador.
- **Visual e interatividade 3D**:
  - Seleção de peças e casas por *raycasting* com o mouse, indicadores 3D de movimentos válidos e capturas, destaque do último lance e alerta no Rei em xeque.
  - Câmera orbital livre (arrastar e zoom) + botão para inverter a visão (`C`).
  - Histórico de lances em notação algébrica (`SAN`), peças capturadas, botão **Desfazer (`U`)** e áudio procedural.

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
