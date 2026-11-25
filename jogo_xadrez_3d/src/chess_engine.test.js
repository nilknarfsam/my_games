import test from 'node:test';
import assert from 'node:assert/strict';
import { ChessEngine, chooseAIMove } from './chess_engine.js';

test('initializes standard 32 pieces and 20 opening moves for white', () => {
  const engine = new ChessEngine();
  assert.equal(engine.turn, 'w');
  assert.equal(engine.status, 'playing');
  const moves = engine.getAllLegalMoves('w');
  assert.equal(moves.length, 20);
});

test('executes Fool Mate checkmate in 4 plies', () => {
  const engine = new ChessEngine();
  assert.ok(engine.makeMove(6, 5, 5, 5)); // f3
  assert.ok(engine.makeMove(1, 4, 3, 4)); // e5
  assert.ok(engine.makeMove(6, 6, 4, 6)); // g4
  const mate = engine.makeMove(0, 3, 4, 7); // Qh4#
  assert.ok(mate);
  assert.equal(mate.san, 'Qh4#');
  assert.equal(engine.status, 'checkmate');
  assert.equal(engine.winner, 'b');
});

test('supports kingside castling when path is clear and safe', () => {
  const engine = new ChessEngine();
  // Clear f1, g1 and move pawn so bishop/knight aren't blocking
  engine.board[7][5] = null;
  engine.board[7][6] = null;
  const moves = engine.getLegalMovesForSquare(7, 4);
  const castle = moves.find((m) => m.castle === 'K');
  assert.ok(castle);

  const res = engine.makeMove(7, 4, 7, 6);
  assert.equal(res.san, 'O-O');
  assert.equal(engine.board[7][6]?.type, 'k');
  assert.equal(engine.board[7][5]?.type, 'r');
});

test('supports en passant capture and undo restores board cleanly', () => {
  const engine = new ChessEngine();
  assert.ok(engine.makeMove(6, 4, 4, 4)); // e4
  assert.ok(engine.makeMove(1, 0, 2, 0)); // a6
  assert.ok(engine.makeMove(4, 4, 3, 4)); // e5
  assert.ok(engine.makeMove(1, 3, 3, 3)); // d5
  const ep = engine.makeMove(3, 4, 2, 3); // exd6 e.p.
  assert.ok(ep);
  assert.equal(engine.board[3][3], null);
  assert.equal(engine.board[2][3]?.type, 'p');

  assert.equal(engine.undo(), true);
  assert.equal(engine.board[3][3]?.color, 'b');
  assert.equal(engine.board[3][4]?.color, 'w');
});

test('supports pawn promotion to queen or knight', () => {
  const engine = new ChessEngine();
  engine.board = Array.from({ length: 8 }, () => Array(8).fill(null));
  engine.board[0][7] = { type: 'k', color: 'b' };
  engine.board[7][4] = { type: 'k', color: 'w' };
  engine.board[1][0] = { type: 'p', color: 'w' };
  engine.turn = 'w';

  const promo = engine.makeMove(1, 0, 0, 0, 'n');
  assert.ok(promo);
  assert.equal(engine.board[0][0]?.type, 'n');
  assert.equal(promo.san.includes('=N'), true);
});

test('AI finds forced mate in 1 when available', () => {
  const engine = new ChessEngine();
  engine.board = Array.from({ length: 8 }, () => Array(8).fill(null));
  engine.board[0][7] = { type: 'k', color: 'b' };
  engine.board[2][6] = { type: 'k', color: 'w' };
  engine.board[2][0] = { type: 'q', color: 'w' };
  engine.turn = 'w';

  const best = chooseAIMove(engine, 'medium', () => 0);
  assert.ok(best);
  const res = engine.makeMove(best.fromR, best.fromC, best.toR, best.toC, best.promotion ?? 'q');
  assert.equal(res.status, 'checkmate');
});

test('supports queenside castling and getAvailableCastles helper', () => {
  const engine = new ChessEngine();
  engine.board[7][1] = null;
  engine.board[7][2] = null;
  engine.board[7][3] = null;

  const castles = engine.getAvailableCastles('w');
  assert.equal(castles.kingSide, null);
  assert.ok(castles.queenSide);

  const res = engine.makeMove(7, 4, 7, 2);
  assert.equal(res.san, 'O-O-O');
  assert.equal(engine.board[7][2]?.type, 'k');
  assert.equal(engine.board[7][3]?.type, 'r');
});

test('blocks castling through an attacked square', () => {
  const engine = new ChessEngine();
  engine.board[7][5] = null;
  engine.board[7][6] = null;
  engine.board[6][5] = null; // remove f2 pawn
  engine.board[2][5] = { type: 'r', color: 'b' }; // black rook attacks f1

  const castles = engine.getAvailableCastles('w');
  assert.equal(castles.kingSide, null);
});

test('detects threefold repetition draw and undo restores status', () => {
  const engine = new ChessEngine();
  const cycle = () => {
    assert.ok(engine.makeMove(7, 6, 5, 5)); // Nf3
    assert.ok(engine.makeMove(0, 6, 2, 5)); // Nf6
    assert.ok(engine.makeMove(5, 5, 7, 6)); // Ng1
    assert.ok(engine.makeMove(2, 5, 0, 6)); // Ng8
  };

  cycle();
  assert.equal(engine.status, 'playing');
  cycle();
  assert.equal(engine.status, 'draw_repetition');
  assert.equal(engine.isGameOver(), true);

  assert.equal(engine.undo(), true);
  assert.equal(engine.status, 'playing');
  assert.equal(engine.isGameOver(), false);
});
