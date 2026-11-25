# Mapa de Melhorias — Xadrez 3D

Plano evolutivo do projeto **Xadrez 3D** (`jogo_xadrez_3d/`), organizado em fases incrementais via **Pull Requests**.

## Fase 1 — Roque Intuitivo, Relógio e Assistência (PR #1 — Concluída)
- [x] **Roque intuitivo de 3 formas**: clicar `Rei → casa destino (g1/c1)`, clicar `Rei → Torre (h1/a1)` (ou `Torre → Rei`), ou usar os botões contextuais `Roque Curto (O-O)` / `Roque Longo (O-O-O)` na HUD.
- [x] **Indicador visual dourado exclusivo** para casas de roque e Torre participante + **animação simultânea 3D** de Rei e Torre.
- [x] **Relógio de Xadrez** configurável (`Sem Limite`, `Blitz 5 min`, `Rápido 10 min`) com destaque do turno e derrota por tempo esgotado.
- [x] **Barra de Avaliação da Posição** em tempo real (`+0.0`, `+2.5`, `+Mate`) + botão **Dica (`H`)** destacando o melhor lance sugerido no tabuleiro 3D.
- [x] **Empate por Repetição Tripla** (`draw_repetition`) no motor `ChessEngine` com restauração completa no `undo()`.

## Fase 2A — Motor & IA Turbinada (PR #3 — Nesta PR)
- [x] **Web Worker dedicado (`src/ai_worker.js`)**: cálculo da IA fora da thread principal mantendo a câmera 3D fluida a 60 FPS.
- [x] **Quiescence Search + Transposition Table (Zobrist Hashing)**: evita erros de horizonte em capturas e acelera a busca Alpha-Beta.
- [x] **Livro de Aberturas (`src/openings.js`)**: variedade nas respostas da IA e identificação em tempo real do nome da abertura na HUD.
- [x] **Incremento Fischer (`3+2`, `5+3`) + Auto-Save e Placar (`localStorage`)**: salva partida em andamento e contabiliza `Vitórias / Empates / Derrotas` contra a IA.

## Fase 2B — Visual 3D & Ergonomia (Próxima PR)
- [ ] **Temas de Tabuleiro 3D**: seletor de materiais na HUD (*Madeira Clássica*, *Mármore Real*, *Ardósia Minimalista*, *Cyber Neon*).
- [ ] **Cemitério 3D de peças capturadas**: miniaturas 3D posicionadas ao lado do tabuleiro em vez de apenas ícones Unicode.
- [ ] **Partículas de captura/xeque-mate**, *Drag & Drop 3D* e giro automático opcional de câmera no modo 2 Jogadores.

## Fase 2C — Análise & Desafios (Próxima PR)
- [ ] **Importar / Exportar FEN e PGN** e **Replay interativo** pelo histórico de lances.
- [ ] **Modo Desafios (Puzzles Táticos)**: pacote curado de Mate em 1 e Mate em 2.

## Fase 3 — Multiplayer Online
- [ ] **Partidas em Rede (WebSocket / WebRTC)**: criação de sala com código compartilhável, sincronização de lances e relógio autoritativo.
