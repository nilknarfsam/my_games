# Mapa de Melhorias — Xadrez 3D

Plano evolutivo do projeto **Xadrez 3D** (`jogo_xadrez_3d/`), organizado em fases incrementais via **Pull Requests**.

## Fase 1 — Roque Intuitivo, Relógio e Assistência (PR #1 — Concluída)
- [x] **Roque intuitivo de 3 formas**: clicar `Rei → casa destino (g1/c1)`, clicar `Rei → Torre (h1/a1)` (ou `Torre → Rei`), ou usar os botões contextuais `Roque Curto (O-O)` / `Roque Longo (O-O-O)` na HUD.
- [x] **Indicador visual dourado exclusivo** para casas de roque e Torre participante + **animação simultânea 3D** de Rei e Torre.
- [x] **Relógio de Xadrez** configurável (`Sem Limite`, `Blitz 5 min`, `Rápido 10 min`) com destaque do turno e derrota por tempo esgotado.
- [x] **Barra de Avaliação da Posição** em tempo real (`+0.0`, `+2.5`, `+Mate`) + botão **Dica (`H`)** destacando o melhor lance sugerido no tabuleiro 3D.
- [x] **Empate por Repetição Tripla** (`draw_repetition`) no motor `ChessEngine` com restauração completa no `undo()`.

## Fase 2A — Motor & IA Turbinada (PR #3 — Concluída)
- [x] **Web Worker dedicado (`src/ai_worker.js`)**: cálculo da IA fora da thread principal mantendo a câmera 3D fluida a 60 FPS.
- [x] **Quiescence Search + Transposition Table (Zobrist Hashing)**: evita erros de horizonte em capturas e acelera a busca Alpha-Beta.
- [x] **Livro de Aberturas (`src/openings.js`)**: variedade nas respostas da IA e identificação em tempo real do nome da abertura na HUD.
- [x] **Incremento Fischer (`3+2`, `5+3`) + Auto-Save e Placar (`localStorage`)**: salva partida em andamento e contabiliza `Vitórias / Empates / Derrotas` contra a IA.

## Fase 2B — Versão Mobile & Acesso LAN (PR #4 — Nesta PR)
- [x] **HUD responsiva para celular**: barra compacta no topo, barra de ações inferior com `safe-area-inset` e gaveta expansível (`Opções & Histórico`) para evitar sobreposição no tabuleiro.
- [x] **Câmera 3D adaptativa em modo retrato** (`aspect < 1`) mantendo todas as colunas `A–H` visíveis sem cortar as bordas.
- [x] **Controles por toque aprimorados**: `touch-action: none` no canvas, tolerância de toque ajustada (`14px`) e prevenção de pull-to-refresh acidental.
- [x] **Acesso direto na rede Wi-Fi (`host: true` no Vite)**: exibe o IP local no terminal ao iniciar para abrir direto no navegador do celular.

## Fase 2C — Visual 3D & Análise (Próximas PRs)
- [ ] **Temas de Tabuleiro 3D**: seletor de materiais na HUD (*Madeira Clássica*, *Mármore Real*, *Ardósia Minimalista*, *Cyber Neon*).
- [ ] **Cemitério 3D de peças capturadas** na mesa e partículas de captura/xeque-mate.
- [ ] **Importar / Exportar FEN e PGN**, **Replay interativo** pelo histórico de lances e **Modo Desafios (Puzzles)**.

---

## Fase 3 — Arquitetura Planejada para Multiplayer em Rede (Implementação Futura)

Objetivo: permitir que **2 jogadores em aparelhos diferentes** (PC ou celular, na rede local Wi-Fi ou pela internet) joguem a mesma partida em tempo real.

### 1. Arquitetura Técnica
- **Servidor autoritativo leve em Node.js (`server/index.js`)** usando `ws` (WebSocket):
  - Importa diretamente o motor `src/chess_engine.js` (`ChessEngine`) em ES Modules para validar todos os lances no servidor (evitando jogadas ilegais ou dessincronização).
  - Mantém um mapa de salas ativas em memória (`Map<roomCode, RoomState>`), com código curto de 4 dígitos (ex.: `4821`) e suporte a entrada direta por URL (`?sala=4821`).
- **Fluxo da Partida**:
  1. Jogador 1 escolhe **Modo: Online (Rede)** e clica em **Criar Sala** → recebe o código/link e assume as **Brancas**.
  2. Jogador 2 entra com o código → assume as **Pretas** (câmera vira automaticamente para `-Z`).
  3. A cada jogada, o cliente envia `{ type: 'move', fromR, fromC, toR, toC, promotion }`.
  4. O servidor valida no `ChessEngine`, atualiza o relógio oficial e transmite `{ type: 'state_sync', moves, clocks, status }` para ambos os jogadores.

### 2. Protocolo de Mensagens WebSocket (Previsto)
| Mensagem | Direção | Descrição |
| --- | --- | --- |
| `create_room` | Cliente → Servidor | Cria nova sala com cadência de relógio opcional e retorna `roomCode` + `color: 'w'`. |
| `join_room` | Cliente → Servidor | Conecta na sala `roomCode` como `color: 'b'` (ou reconecta via `playerToken`). |
| `move` | Cliente → Servidor | Solicita execução de um lance (validado no `ChessEngine` do servidor). |
| `state_sync` | Servidor → Clientes | Envia lista de lances, status, turno e relógio sincronizado. |
| `rematch_request` / `rematch_accept` | Bidirecional | Solicita e confirma revanche invertendo as cores. |
| `opponent_status` | Servidor → Cliente | Notifica desconexão/reconexão do adversário sem perder a sala. |

### 3. Como funcionará na prática
- **Rede Local (Wi-Fi/LAN):** jogar pelo IP do computador anfitrião (ex.: `http://192.168.x.x:5174`), sem depender de internet.
- **Pela Internet:** expor o servidor com um túnel gratuito (`cloudflared` / `ngrok`) ou hospedar em um serviço Node.js gratuito (Render / Railway / Fly.io).
