# Mapa de Melhorias — Xadrez 3D

Plano evolutivo do projeto **Xadrez 3D** (`jogo_xadrez_3d/`), organizado em fases incrementais via **Pull Requests**.

## Fase 1 — Roque Intuitivo, Relógio e Assistência (Nesta PR)
- [x] **Roque intuitivo de 3 formas**: clicar `Rei → casa destino (g1/c1)`, clicar `Rei → Torre (h1/a1)` (ou `Torre → Rei`), ou usar os botões contextuais `Roque Curto (O-O)` / `Roque Longo (O-O-O)` na HUD.
- [x] **Indicador visual dourado exclusivo** para casas de roque e Torre participante + **animação simultânea 3D** de Rei e Torre.
- [x] **Relógio de Xadrez** configurável (`Sem Limite`, `Blitz 5 min`, `Rápido 10 min`) com destaque do turno e derrota por tempo esgotado.
- [x] **Barra de Avaliação da Posição** em tempo real (`+0.0`, `+2.5`, `+Mate`) + botão **Dica (`H`)** destacando o melhor lance sugerido no tabuleiro 3D.
- [x] **Empate por Repetição Tripla** (`draw_repetition`) no motor `ChessEngine` com restauração completa no `undo()`.

## Fase 2 — IA Avançada e Personalização Visual (Próximas PRs)
- [ ] **IA mais forte e rápida**: *Quiescence Search* (evitar efeito horizonte em trocas) + *Transposition Table* (hashing Zobrist) + livro de aberturas simples.
- [ ] **Temas de Tabuleiro 3D**: seletor de materiais na HUD (*Madeira Clássica*, *Mármore Azul*, *Ardósia Neon*).
- [ ] **Cemitério 3D de peças capturadas**: miniaturas 3D posicionadas ao lado do tabuleiro em vez de apenas ícones Unicode.
- [ ] **Importar / Exportar FEN e PGN**: copiar e colar posições ou partidas completas para análise externa.

## Fase 3 — Multiplayer Online
- [ ] **Partidas em Rede (WebSocket / WebRTC)**: criação de sala com código compartilhável, sincronização de lances e relógio autoritativo.
