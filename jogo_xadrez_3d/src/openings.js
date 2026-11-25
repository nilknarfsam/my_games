/**
 * Livro de aberturas compacto e identificação de abertura por sequência SAN.
 * Cada entrada mapeia a sequência de lances em SAN (separada por espaço) para
 * { name, replies }: respostas recomendadas em SAN quando for a vez da IA.
 */
const OPENING_BOOK = [
  { seq: '', name: 'Posição Inicial', replies: ['e4', 'd4', 'c4', 'Nf3'] },
  { seq: 'e4', name: 'Abertura do Peão do Rei', replies: ['e5', 'c5', 'e6', 'c6'] },
  { seq: 'd4', name: 'Abertura do Peão da Dama', replies: ['d5', 'Nf6', 'e6'] },
  { seq: 'c4', name: 'Abertura Inglesa', replies: ['e5', 'Nf6', 'c5'] },
  { seq: 'Nf3', name: 'Abertura Réti', replies: ['d5', 'Nf6', 'c5'] },

  { seq: 'e4 e5', name: 'Abertura Aberta', replies: ['Nf3', 'Bc4'] },
  { seq: 'e4 e5 Nf3', name: 'Abertura do Cavalo do Rei', replies: ['Nc6', 'Nf6'] },
  { seq: 'e4 e5 Nf3 Nc6', name: 'Jogo Aberto (2...Cc6)', replies: ['Bb5', 'Bc4', 'd4'] },
  { seq: 'e4 e5 Nf3 Nc6 Bb5', name: 'Abertura Espanhola (Ruy Lopez)', replies: ['a6', 'Nf6'] },
  { seq: 'e4 e5 Nf3 Nc6 Bb5 a6', name: 'Espanhola — Defesa Morphy', replies: ['Ba4'] },
  { seq: 'e4 e5 Nf3 Nc6 Bc4', name: 'Abertura Italiana', replies: ['Bc5', 'Nf6'] },
  { seq: 'e4 e5 Nf3 Nc6 Bc4 Bc5', name: 'Italiana — Giuoco Piano', replies: ['c3', 'd3', 'O-O'] },
  { seq: 'e4 e5 Nf3 Nc6 Bc4 Nf6', name: 'Defesa dos Dois Cavalos', replies: ['d3', 'Ng5', 'O-O'] },
  { seq: 'e4 e5 Nf3 Nc6 d4', name: 'Abertura Escocesa', replies: ['exd4'] },
  { seq: 'e4 e5 Nf3 Nf6', name: 'Defesa Petrov', replies: ['Nxe5', 'd4'] },

  { seq: 'e4 c5', name: 'Defesa Siciliana', replies: ['Nf3', 'Nc3', 'c3'] },
  { seq: 'e4 c5 Nf3', name: 'Siciliana Aberta', replies: ['d6', 'Nc6', 'e6'] },
  { seq: 'e4 c5 Nf3 d6 d4 cxd4 Nxd4', name: 'Siciliana — Variante Principal', replies: ['Nf6'] },
  { seq: 'e4 c5 Nf3 Nc6 d4 cxd4 Nxd4', name: 'Siciliana Clássica', replies: ['Nf6', 'e5'] },

  { seq: 'e4 e6', name: 'Defesa Francesa', replies: ['d4'] },
  { seq: 'e4 e6 d4 d5', name: 'Defesa Francesa (2...d5)', replies: ['Nc3', 'Nd2', 'e5'] },
  { seq: 'e4 c6', name: 'Defesa Caro-Kann', replies: ['d4'] },
  { seq: 'e4 c6 d4 d5', name: 'Caro-Kann (2...d5)', replies: ['Nc3', 'Nd2', 'e5'] },

  { seq: 'd4 d5', name: 'Jogo Fechado (1...d5)', replies: ['c4', 'Nf3'] },
  { seq: 'd4 d5 c4', name: 'Gambito da Dama', replies: ['e6', 'c6', 'dxc4'] },
  { seq: 'd4 d5 c4 e6', name: 'Gambito da Dama Recusado', replies: ['Nc3', 'Nf3'] },
  { seq: 'd4 d5 c4 c6', name: 'Defesa Eslava', replies: ['Nf3', 'Nc3'] },

  { seq: 'd4 Nf6', name: 'Defesa Índia', replies: ['c4', 'Nf3'] },
  { seq: 'd4 Nf6 c4', name: 'Sistema Índio (2.c4)', replies: ['e6', 'g6'] },
  { seq: 'd4 Nf6 c4 g6', name: 'Defesa Índia do Rei / Grünfeld', replies: ['Nc3'] },
  { seq: 'd4 Nf6 c4 g6 Nc3 Bg7', name: 'Defesa Índia do Rei', replies: ['e4', 'Nf3'] },
  { seq: 'd4 Nf6 c4 e6', name: 'Índia — 2...e6', replies: ['Nc3', 'Nf3'] },
  { seq: 'd4 Nf6 c4 e6 Nc3 Bb4', name: 'Defesa Nimzo-Índia', replies: ['e3', 'Qc2', 'Nf3'] },
];

const OPENING_MAP = new Map(OPENING_BOOK.map((entry) => [entry.seq, entry]));

/**
 * Identifica o nome da abertura mais específica encontrada no histórico de lances.
 * @param {Array<{san: string}>} moveLog
 * @returns {string}
 */
export function identifyOpening(moveLog) {
  if (!moveLog || moveLog.length === 0) return 'Posição Inicial';
  const sans = moveLog.map((m) => m.san.replace(/[+#]$/, ''));
  let detected = sans[0] ? 'Abertura Personalizada' : 'Posição Inicial';
  for (let len = 1; len <= sans.length; len++) {
    const key = sans.slice(0, len).join(' ');
    const match = OPENING_MAP.get(key);
    if (match) detected = match.name;
  }
  return detected;
}

/**
 * Seleciona um lance do livro de aberturas se a posição atual estiver catalogada.
 */
export function pickBookMove(engine, rng = Math.random) {
  const key = engine.moveLog.map((m) => m.san.replace(/[+#]$/, '')).join(' ');
  const entry = OPENING_MAP.get(key);
  if (!entry || entry.replies.length === 0) return null;

  const legal = engine.getAllLegalMoves(engine.turn);
  const candidates = [];

  for (const targetSan of entry.replies) {
    for (const move of legal) {
      const rec = engine.makeMove(move.fromR, move.fromC, move.toR, move.toC, move.promotion ?? 'q');
      if (!rec) continue;
      const cleanSan = rec.san.replace(/[+#]$/, '');
      engine.undo();
      if (cleanSan === targetSan) {
        candidates.push(move);
        break;
      }
    }
  }

  if (candidates.length === 0) return null;
  return candidates[Math.floor(rng() * candidates.length)];
}
