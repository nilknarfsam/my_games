export const FILES = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h'];
export const RANKS = ['8', '7', '6', '5', '4', '3', '2', '1'];

export const PIECE_VALUES = {
  p: 100,
  n: 320,
  b: 330,
  r: 500,
  q: 900,
  k: 20000,
};

// Piece-square tables from White's perspective (row 0 = rank 8, row 7 = rank 1)
const PST = {
  p: [
    [0, 0, 0, 0, 0, 0, 0, 0],
    [50, 50, 50, 50, 50, 50, 50, 50],
    [10, 10, 20, 30, 30, 20, 10, 10],
    [5, 5, 10, 27, 27, 10, 5, 5],
    [0, 0, 0, 24, 24, 0, 0, 0],
    [5, -5, -10, 0, 0, -10, -5, 5],
    [5, 10, 10, -22, -22, 10, 10, 5],
    [0, 0, 0, 0, 0, 0, 0, 0],
  ],
  n: [
    [-50, -40, -30, -30, -30, -30, -40, -50],
    [-40, -20, 0, 0, 0, 0, -20, -40],
    [-30, 0, 10, 15, 15, 10, 0, -30],
    [-30, 5, 15, 20, 20, 15, 5, -30],
    [-30, 0, 15, 20, 20, 15, 0, -30],
    [-30, 5, 10, 15, 15, 10, 5, -30],
    [-40, -20, 0, 5, 5, 0, -20, -40],
    [-50, -40, -30, -30, -30, -30, -40, -50],
  ],
  b: [
    [-20, -10, -10, -10, -10, -10, -10, -20],
    [-10, 0, 0, 0, 0, 0, 0, -10],
    [-10, 0, 8, 12, 12, 8, 0, -10],
    [-10, 6, 6, 12, 12, 6, 6, -10],
    [-10, 0, 12, 12, 12, 12, 0, -10],
    [-10, 10, 10, 10, 10, 10, 10, -10],
    [-10, 6, 0, 0, 0, 0, 6, -10],
    [-20, -10, -10, -10, -10, -10, -10, -20],
  ],
  r: [
    [0, 0, 0, 0, 0, 0, 0, 0],
    [6, 12, 12, 12, 12, 12, 12, 6],
    [-5, 0, 0, 0, 0, 0, 0, -5],
    [-5, 0, 0, 0, 0, 0, 0, -5],
    [-5, 0, 0, 0, 0, 0, 0, -5],
    [-5, 0, 0, 0, 0, 0, 0, -5],
    [-5, 0, 0, 0, 0, 0, 0, -5],
    [0, 0, 0, 6, 6, 0, 0, 0],
  ],
  q: [
    [-20, -10, -10, -5, -5, -10, -10, -20],
    [-10, 0, 0, 0, 0, 0, 0, -10],
    [-10, 0, 5, 5, 5, 5, 0, -10],
    [-5, 0, 5, 5, 5, 5, 0, -5],
    [0, 0, 5, 5, 5, 5, 0, -5],
    [-10, 5, 5, 5, 5, 5, 0, -10],
    [-10, 0, 5, 0, 0, 0, 0, -10],
    [-20, -10, -10, -5, -5, -10, -10, -20],
  ],
  k: [
    [-30, -40, -40, -50, -50, -40, -40, -30],
    [-30, -40, -40, -50, -50, -40, -40, -30],
    [-30, -40, -40, -50, -50, -40, -40, -30],
    [-30, -40, -40, -50, -50, -40, -40, -30],
    [-20, -30, -30, -40, -40, -30, -30, -20],
    [-10, -20, -20, -20, -20, -20, -20, -10],
    [20, 20, 0, 0, 0, 0, 20, 20],
    [20, 30, 10, 0, 0, 10, 30, 20],
  ],
};

export function coordsToAlgebraic(r, c) {
  return `${FILES[c]}${RANKS[r]}`;
}

export function oppositeColor(color) {
  return color === 'w' ? 'b' : 'w';
}

function inBounds(r, c) {
  return r >= 0 && r < 8 && c >= 0 && c < 8;
}

function cloneBoard(board) {
  return board.map((row) => row.map((cell) => (cell ? { ...cell } : null)));
}

/**
 * Motor completo de Xadrez: roque, en passant, promoção, xeque, xeque-mate, afogamento e material insuficiente.
 */
export class ChessEngine {
  constructor() {
    this.reset();
  }

  reset() {
    this.board = Array.from({ length: 8 }, () => Array(8).fill(null));
    const backRank = ['r', 'n', 'b', 'q', 'k', 'b', 'n', 'r'];
    for (let c = 0; c < 8; c++) {
      this.board[0][c] = { type: backRank[c], color: 'b' };
      this.board[1][c] = { type: 'p', color: 'b' };
      this.board[6][c] = { type: 'p', color: 'w' };
      this.board[7][c] = { type: backRank[c], color: 'w' };
    }

    this.turn = 'w';
    this.castling = { wK: true, wQ: true, bK: true, bQ: true };
    this.enPassant = null;
    this.halfMoveClock = 0;
    this.fullMoveNumber = 1;
    this.captured = { w: [], b: [] };
    this.moveLog = [];
    this.history = [];
    this.positionCounts = {};
    this.status = 'playing';
    this.winner = null;

    const initialKey = this.#positionKey();
    this.positionCounts[initialKey] = 1;
  }

  isGameOver() {
    return (
      this.status === 'checkmate' ||
      this.status === 'stalemate' ||
      this.status === 'draw_50' ||
      this.status === 'draw_insufficient' ||
      this.status === 'draw_repetition'
    );
  }

  #positionKey() {
    let key = `${this.turn}|`;
    for (let r = 0; r < 8; r++) {
      for (let c = 0; c < 8; c++) {
        const p = this.board[r][c];
        key += p ? `${p.color}${p.type}` : '.';
      }
    }
    const { wK, wQ, bK, bQ } = this.castling;
    key += `|${wK ? 'K' : ''}${wQ ? 'Q' : ''}${bK ? 'k' : ''}${bQ ? 'q' : ''}`;
    if (this.enPassant) {
      key += `|${this.enPassant.r},${this.enPassant.c}`;
    }
    return key;
  }

  cloneState() {
    return {
      board: cloneBoard(this.board),
      turn: this.turn,
      castling: { ...this.castling },
      enPassant: this.enPassant ? { ...this.enPassant } : null,
      halfMoveClock: this.halfMoveClock,
      fullMoveNumber: this.fullMoveNumber,
      captured: { w: [...this.captured.w], b: [...this.captured.b] },
      status: this.status,
      winner: this.winner,
    };
  }

  restoreState(snapshot) {
    this.board = cloneBoard(snapshot.board);
    this.turn = snapshot.turn;
    this.castling = { ...snapshot.castling };
    this.enPassant = snapshot.enPassant ? { ...snapshot.enPassant } : null;
    this.halfMoveClock = snapshot.halfMoveClock;
    this.fullMoveNumber = snapshot.fullMoveNumber;
    this.captured = { w: [...snapshot.captured.w], b: [...snapshot.captured.b] };
    this.status = snapshot.status;
    this.winner = snapshot.winner;
  }

  findKing(color) {
    for (let r = 0; r < 8; r++) {
      for (let c = 0; c < 8; c++) {
        const p = this.board[r][c];
        if (p && p.color === color && p.type === 'k') {
          return { r, c };
        }
      }
    }
    return null;
  }

  isSquareAttacked(targetR, targetC, byColor) {
    // Pawn attacks
    const pawnDir = byColor === 'w' ? 1 : -1;
    for (const dc of [-1, 1]) {
      const pr = targetR + pawnDir;
      const pc = targetC + dc;
      if (inBounds(pr, pc)) {
        const p = this.board[pr][pc];
        if (p && p.color === byColor && p.type === 'p') return true;
      }
    }

    // Knight attacks
    const knightOffsets = [
      [-2, -1], [-2, 1], [-1, -2], [-1, 2],
      [1, -2], [1, 2], [2, -1], [2, 1],
    ];
    for (const [dr, dc] of knightOffsets) {
      const nr = targetR + dr;
      const nc = targetC + dc;
      if (inBounds(nr, nc)) {
        const p = this.board[nr][nc];
        if (p && p.color === byColor && p.type === 'n') return true;
      }
    }

    // King attacks
    for (let dr = -1; dr <= 1; dr++) {
      for (let dc = -1; dc <= 1; dc++) {
        if (dr === 0 && dc === 0) continue;
        const kr = targetR + dr;
        const kc = targetC + dc;
        if (inBounds(kr, kc)) {
          const p = this.board[kr][kc];
          if (p && p.color === byColor && p.type === 'k') return true;
        }
      }
    }

    // Rook / Queen orthogonal rays
    const orthoDirs = [[-1, 0], [1, 0], [0, -1], [0, 1]];
    for (const [dr, dc] of orthoDirs) {
      let r = targetR + dr;
      let c = targetC + dc;
      while (inBounds(r, c)) {
        const p = this.board[r][c];
        if (p) {
          if (p.color === byColor && (p.type === 'r' || p.type === 'q')) return true;
          break;
        }
        r += dr;
        c += dc;
      }
    }

    // Bishop / Queen diagonal rays
    const diagDirs = [[-1, -1], [-1, 1], [1, -1], [1, 1]];
    for (const [dr, dc] of diagDirs) {
      let r = targetR + dr;
      let c = targetC + dc;
      while (inBounds(r, c)) {
        const p = this.board[r][c];
        if (p) {
          if (p.color === byColor && (p.type === 'b' || p.type === 'q')) return true;
          break;
        }
        r += dr;
        c += dc;
      }
    }

    return false;
  }

  isInCheck(color) {
    const king = this.findKing(color);
    if (!king) return false;
    return this.isSquareAttacked(king.r, king.c, oppositeColor(color));
  }

  #pseudoMovesForSquare(r, c) {
    const piece = this.board[r][c];
    if (!piece) return [];
    const { type, color } = piece;
    const moves = [];
    const enemy = oppositeColor(color);

    if (type === 'p') {
      const dir = color === 'w' ? -1 : 1;
      const startRow = color === 'w' ? 6 : 1;
      const promoRow = color === 'w' ? 0 : 7;

      const oneR = r + dir;
      if (inBounds(oneR, c) && !this.board[oneR][c]) {
        if (oneR === promoRow) {
          for (const promo of ['q', 'r', 'b', 'n']) {
            moves.push({ fromR: r, fromC: c, toR: oneR, toC: c, promotion: promo });
          }
        } else {
          moves.push({ fromR: r, fromC: c, toR: oneR, toC: c });
          const twoR = r + dir * 2;
          if (r === startRow && !this.board[twoR][c]) {
            moves.push({ fromR: r, fromC: c, toR: twoR, toC: c, isDoublePawn: true });
          }
        }
      }

      for (const dc of [-1, 1]) {
        const cr = r + dir;
        const cc = c + dc;
        if (!inBounds(cr, cc)) continue;
        const target = this.board[cr][cc];
        if (target && target.color === enemy) {
          if (cr === promoRow) {
            for (const promo of ['q', 'r', 'b', 'n']) {
              moves.push({ fromR: r, fromC: c, toR: cr, toC: cc, capture: true, promotion: promo });
            }
          } else {
            moves.push({ fromR: r, fromC: c, toR: cr, toC: cc, capture: true });
          }
        } else if (this.enPassant && this.enPassant.r === cr && this.enPassant.c === cc) {
          moves.push({ fromR: r, fromC: c, toR: cr, toC: cc, capture: true, isEnPassant: true });
        }
      }
      return moves;
    }

    if (type === 'n') {
      const offsets = [
        [-2, -1], [-2, 1], [-1, -2], [-1, 2],
        [1, -2], [1, 2], [2, -1], [2, 1],
      ];
      for (const [dr, dc] of offsets) {
        const nr = r + dr;
        const nc = c + dc;
        if (!inBounds(nr, nc)) continue;
        const target = this.board[nr][nc];
        if (!target || target.color === enemy) {
          moves.push({ fromR: r, fromC: c, toR: nr, toC: nc, capture: Boolean(target) });
        }
      }
      return moves;
    }

    if (type === 'b' || type === 'r' || type === 'q') {
      const dirs = [];
      if (type === 'b' || type === 'q') dirs.push([-1, -1], [-1, 1], [1, -1], [1, 1]);
      if (type === 'r' || type === 'q') dirs.push([-1, 0], [1, 0], [0, -1], [0, 1]);

      for (const [dr, dc] of dirs) {
        let nr = r + dr;
        let nc = c + dc;
        while (inBounds(nr, nc)) {
          const target = this.board[nr][nc];
          if (!target) {
            moves.push({ fromR: r, fromC: c, toR: nr, toC: nc });
          } else {
            if (target.color === enemy) {
              moves.push({ fromR: r, fromC: c, toR: nr, toC: nc, capture: true });
            }
            break;
          }
          nr += dr;
          nc += dc;
        }
      }
      return moves;
    }

    if (type === 'k') {
      for (let dr = -1; dr <= 1; dr++) {
        for (let dc = -1; dc <= 1; dc++) {
          if (dr === 0 && dc === 0) continue;
          const nr = r + dr;
          const nc = c + dc;
          if (!inBounds(nr, nc)) continue;
          const target = this.board[nr][nc];
          if (!target || target.color === enemy) {
            moves.push({ fromR: r, fromC: c, toR: nr, toC: nc, capture: Boolean(target) });
          }
        }
      }

      // Castling
      const homeRow = color === 'w' ? 7 : 0;
      if (r === homeRow && c === 4 && !this.isInCheck(color)) {
        const canKingSide = color === 'w' ? this.castling.wK : this.castling.bK;
        const canQueenSide = color === 'w' ? this.castling.wQ : this.castling.bQ;

        if (
          canKingSide &&
          !this.board[homeRow][5] &&
          !this.board[homeRow][6] &&
          this.board[homeRow][7]?.type === 'r' &&
          this.board[homeRow][7]?.color === color &&
          !this.isSquareAttacked(homeRow, 5, enemy) &&
          !this.isSquareAttacked(homeRow, 6, enemy)
        ) {
          moves.push({ fromR: r, fromC: c, toR: homeRow, toC: 6, castle: 'K' });
        }

        if (
          canQueenSide &&
          !this.board[homeRow][3] &&
          !this.board[homeRow][2] &&
          !this.board[homeRow][1] &&
          this.board[homeRow][0]?.type === 'r' &&
          this.board[homeRow][0]?.color === color &&
          !this.isSquareAttacked(homeRow, 3, enemy) &&
          !this.isSquareAttacked(homeRow, 2, enemy)
        ) {
          moves.push({ fromR: r, fromC: c, toR: homeRow, toC: 2, castle: 'Q' });
        }
      }
      return moves;
    }

    return moves;
  }

  #applyRawMove(move) {
    const piece = this.board[move.fromR][move.fromC];
    const target = this.board[move.toR][move.toC];
    let capturedPiece = target ? { ...target } : null;

    this.board[move.fromR][move.fromC] = null;

    if (move.isEnPassant) {
      const capR = piece.color === 'w' ? move.toR + 1 : move.toR - 1;
      capturedPiece = { ...this.board[capR][move.toC] };
      this.board[capR][move.toC] = null;
    }

    this.board[move.toR][move.toC] = {
      type: move.promotion ?? piece.type,
      color: piece.color,
    };

    if (move.castle === 'K') {
      const rook = this.board[move.toR][7];
      this.board[move.toR][7] = null;
      this.board[move.toR][5] = rook;
    } else if (move.castle === 'Q') {
      const rook = this.board[move.toR][0];
      this.board[move.toR][0] = null;
      this.board[move.toR][3] = rook;
    }

    // Update castling rights
    if (piece.type === 'k') {
      if (piece.color === 'w') {
        this.castling.wK = false;
        this.castling.wQ = false;
      } else {
        this.castling.bK = false;
        this.castling.bQ = false;
      }
    }
    if (piece.type === 'r') {
      if (move.fromR === 7 && move.fromC === 0) this.castling.wQ = false;
      if (move.fromR === 7 && move.fromC === 7) this.castling.wK = false;
      if (move.fromR === 0 && move.fromC === 0) this.castling.bQ = false;
      if (move.fromR === 0 && move.fromC === 7) this.castling.bK = false;
    }
    if (capturedPiece?.type === 'r') {
      if (move.toR === 7 && move.toC === 0) this.castling.wQ = false;
      if (move.toR === 7 && move.toC === 7) this.castling.wK = false;
      if (move.toR === 0 && move.toC === 0) this.castling.bQ = false;
      if (move.toR === 0 && move.toC === 7) this.castling.bK = false;
    }

    // En passant target
    if (move.isDoublePawn) {
      this.enPassant = {
        r: (move.fromR + move.toR) / 2,
        c: move.fromC,
      };
    } else {
      this.enPassant = null;
    }

    if (piece.type === 'p' || capturedPiece) {
      this.halfMoveClock = 0;
    } else {
      this.halfMoveClock++;
    }

    if (capturedPiece) {
      this.captured[piece.color].push(capturedPiece.type);
    }

    if (this.turn === 'b') {
      this.fullMoveNumber++;
    }
    this.turn = oppositeColor(this.turn);

    return { piece, capturedPiece };
  }

  getLegalMovesForSquare(r, c) {
    const piece = this.board[r][c];
    if (!piece || piece.color !== this.turn) return [];
    const pseudo = this.#pseudoMovesForSquare(r, c);
    const legal = [];
    for (const move of pseudo) {
      const snap = this.cloneState();
      this.#applyRawMove(move);
      if (!this.isInCheck(piece.color)) {
        legal.push(move);
      }
      this.restoreState(snap);
    }
    return legal;
  }

  getAllLegalMoves(color = this.turn) {
    if (color !== this.turn) return [];
    const all = [];
    for (let r = 0; r < 8; r++) {
      for (let c = 0; c < 8; c++) {
        const p = this.board[r][c];
        if (p && p.color === color) {
          all.push(...this.getLegalMovesForSquare(r, c));
        }
      }
    }
    return all;
  }

  #hasInsufficientMaterial() {
    const pieces = { w: [], b: [] };
    for (let r = 0; r < 8; r++) {
      for (let c = 0; c < 8; c++) {
        const p = this.board[r][c];
        if (p && p.type !== 'k') {
          pieces[p.color].push({ type: p.type, sqColor: (r + c) % 2 });
        }
      }
    }
    const w = pieces.w;
    const b = pieces.b;
    if (w.length === 0 && b.length === 0) return true;
    if (w.length === 0 && b.length === 1 && (b[0].type === 'b' || b[0].type === 'n')) return true;
    if (b.length === 0 && w.length === 1 && (w[0].type === 'b' || w[0].type === 'n')) return true;
    if (
      w.length === 1 &&
      b.length === 1 &&
      w[0].type === 'b' &&
      b[0].type === 'b' &&
      w[0].sqColor === b[0].sqColor
    ) {
      return true;
    }
    return false;
  }

  getAvailableCastles(color = this.turn) {
    if (color !== this.turn || this.isGameOver()) {
      return { kingSide: null, queenSide: null };
    }
    const king = this.findKing(color);
    if (!king) return { kingSide: null, queenSide: null };
    const kingMoves = this.getLegalMovesForSquare(king.r, king.c);
    return {
      kingSide: kingMoves.find((m) => m.castle === 'K') ?? null,
      queenSide: kingMoves.find((m) => m.castle === 'Q') ?? null,
    };
  }

  #updateStatus(currentPosKey = null) {
    const legal = this.getAllLegalMoves(this.turn);
    const inCheck = this.isInCheck(this.turn);
    if (legal.length === 0) {
      if (inCheck) {
        this.status = 'checkmate';
        this.winner = oppositeColor(this.turn);
      } else {
        this.status = 'stalemate';
        this.winner = null;
      }
      return;
    }
    if (currentPosKey && (this.positionCounts[currentPosKey] ?? 0) >= 3) {
      this.status = 'draw_repetition';
      this.winner = null;
      return;
    }
    if (this.halfMoveClock >= 100) {
      this.status = 'draw_50';
      this.winner = null;
      return;
    }
    if (this.#hasInsufficientMaterial()) {
      this.status = 'draw_insufficient';
      this.winner = null;
      return;
    }
    this.status = inCheck ? 'check' : 'playing';
    this.winner = null;
  }

  #buildSAN(move, piece, capturedPiece, siblings) {
    if (move.castle === 'K') return 'O-O';
    if (move.castle === 'Q') return 'O-O-O';

    const dest = coordsToAlgebraic(move.toR, move.toC);
    let san = '';

    if (piece.type === 'p') {
      if (capturedPiece) {
        san += `${FILES[move.fromC]}x`;
      }
      san += dest;
      if (move.promotion) {
        san += `=${move.promotion.toUpperCase()}`;
      }
    } else {
      san += piece.type.toUpperCase();
      const ambig = siblings.filter(
        (m) =>
          (m.fromR !== move.fromR || m.fromC !== move.fromC) &&
          m.toR === move.toR &&
          m.toC === move.toC &&
          this.board[m.fromR][m.fromC]?.type === piece.type,
      );
      if (ambig.length > 0) {
        const sameFile = ambig.some((m) => m.fromC === move.fromC);
        const sameRank = ambig.some((m) => m.fromR === move.fromR);
        if (!sameFile) san += FILES[move.fromC];
        else if (!sameRank) san += RANKS[move.fromR];
        else san += coordsToAlgebraic(move.fromR, move.fromC);
      }
      if (capturedPiece) san += 'x';
      san += dest;
    }

    return san;
  }

  makeMove(fromR, fromC, toR, toC, promotion = 'q') {
    if (this.isGameOver()) {
      return null;
    }

    const legal = this.getLegalMovesForSquare(fromR, fromC);
    const chosen = legal.find(
      (m) => m.toR === toR && m.toC === toC && (!m.promotion || m.promotion === promotion),
    );
    if (!chosen) return null;

    const allLegalBefore = this.getAllLegalMoves(this.turn);
    const snap = this.cloneState();
    const movingPiece = { ...this.board[fromR][fromC] };
    const sanBase = this.#buildSAN(
      chosen,
      movingPiece,
      chosen.capture || chosen.isEnPassant ? { type: 'p' } : null,
      allLegalBefore,
    );

    const { capturedPiece } = this.#applyRawMove(chosen);
    const posKey = this.#positionKey();
    this.positionCounts[posKey] = (this.positionCounts[posKey] ?? 0) + 1;
    snap.addedPosKey = posKey;
    this.history.push(snap);

    this.#updateStatus(posKey);

    let san = sanBase;
    if (this.status === 'checkmate') san += '#';
    else if (this.status === 'check') san += '+';

    const record = {
      san,
      move: chosen,
      piece: movingPiece,
      captured: capturedPiece,
      status: this.status,
      winner: this.winner,
    };
    this.moveLog.push(record);
    return record;
  }

  undo() {
    if (this.history.length === 0) return false;
    const prev = this.history.pop();
    if (prev.addedPosKey) {
      const nextCount = (this.positionCounts[prev.addedPosKey] ?? 1) - 1;
      if (nextCount <= 0) delete this.positionCounts[prev.addedPosKey];
      else this.positionCounts[prev.addedPosKey] = nextCount;
    }
    this.restoreState(prev);
    this.moveLog.pop();
    return true;
  }

  evaluateBoard() {
    if (this.status === 'checkmate') {
      return this.winner === 'w' ? 99999 : -99999;
    }
    if (this.isGameOver()) {
      return 0;
    }

    let score = 0;
    for (let r = 0; r < 8; r++) {
      for (let c = 0; c < 8; c++) {
        const p = this.board[r][c];
        if (!p) continue;
        const pstRow = p.color === 'w' ? r : 7 - r;
        const val = PIECE_VALUES[p.type] + PST[p.type][pstRow][c];
        score += p.color === 'w' ? val : -val;
      }
    }
    return score;
  }
}

function orderMoves(engine, moves) {
  return [...moves].sort((a, b) => {
    const scoreA = (a.capture ? 10 : 0) + (a.promotion ? 8 : 0) + (a.castle ? 3 : 0);
    const scoreB = (b.capture ? 10 : 0) + (b.promotion ? 8 : 0) + (b.castle ? 3 : 0);
    if (scoreB !== scoreA) return scoreB - scoreA;
    const targetA = engine.board[a.toR][a.toC];
    const targetB = engine.board[b.toR][b.toC];
    return (targetB ? PIECE_VALUES[targetB.type] : 0) - (targetA ? PIECE_VALUES[targetA.type] : 0);
  });
}

function minimax(engine, depth, alpha, beta, maximizingWhite) {
  if (depth === 0 || engine.isGameOver()) {
    const evalScore = engine.evaluateBoard();
    // Prefer quicker checkmates
    if (evalScore > 90000) return evalScore + depth;
    if (evalScore < -90000) return evalScore - depth;
    return evalScore;
  }

  const moves = orderMoves(engine, engine.getAllLegalMoves(engine.turn));
  if (moves.length === 0) return engine.evaluateBoard();

  if (maximizingWhite) {
    let best = -Infinity;
    for (const m of moves) {
      engine.makeMove(m.fromR, m.fromC, m.toR, m.toC, m.promotion ?? 'q');
      const val = minimax(engine, depth - 1, alpha, beta, false);
      engine.undo();
      if (val > best) best = val;
      if (val > alpha) alpha = val;
      if (beta <= alpha) break;
    }
    return best;
  }

  let best = Infinity;
  for (const m of moves) {
    engine.makeMove(m.fromR, m.fromC, m.toR, m.toC, m.promotion ?? 'q');
    const val = minimax(engine, depth - 1, alpha, beta, true);
    engine.undo();
    if (val < best) best = val;
    if (val < beta) beta = val;
    if (beta <= alpha) break;
  }
  return best;
}

/**
 * Escolhe o melhor lance para o lado atual usando Minimax + Alpha-Beta.
 * @param {ChessEngine} engine
 * @param {'easy'|'medium'|'hard'} difficulty
 */
export function chooseAIMove(engine, difficulty = 'medium', rng = Math.random) {
  const moves = orderMoves(engine, engine.getAllLegalMoves(engine.turn));
  if (moves.length === 0) return null;

  const depth = difficulty === 'easy' ? 1 : difficulty === 'hard' ? 3 : 2;
  const maximizing = engine.turn === 'w';
  const scored = [];

  for (const m of moves) {
    engine.makeMove(m.fromR, m.fromC, m.toR, m.toC, m.promotion ?? 'q');
    const score = minimax(engine, depth - 1, -Infinity, Infinity, !maximizing);
    engine.undo();
    scored.push({ move: m, score });
  }

  scored.sort((a, b) => (maximizing ? b.score - a.score : a.score - b.score));

  if (difficulty === 'easy' && scored.length > 1) {
    const pool = scored.slice(0, Math.min(3, scored.length));
    return pool[Math.floor(rng() * pool.length)].move;
  }

  const bestScore = scored[0].score;
  const tied = scored.filter((item) => item.score === bestScore);
  return tied[Math.floor(rng() * tied.length)].move;
}
