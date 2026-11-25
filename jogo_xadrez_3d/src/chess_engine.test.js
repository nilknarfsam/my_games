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
