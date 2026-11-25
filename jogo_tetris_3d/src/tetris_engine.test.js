import test from 'node:test';
import assert from 'node:assert/strict';
import { COLS, ROWS, PIECE_TYPES, TetrisEngine } from './tetris_engine.js';

function fixedRngSequence(values) {
  let idx = 0;
  return () => {
    const val = values[idx % values.length];
    idx++;
    return val;
  };
}

test('initializes clean 10x20 board with active and next piece', () => {
  const engine = new TetrisEngine({ rng: fixedRngSequence([0.1, 0.4, 0.7]) });
  assert.equal(engine.board.length, ROWS);
  assert.equal(engine.board[0].length, COLS);
  assert.ok(PIECE_TYPES.includes(engine.activePiece.type));
  assert.ok(PIECE_TYPES.includes(engine.nextType));
  assert.equal(engine.score, 0);
  assert.equal(engine.lines, 0);
  assert.equal(engine.level, 1);
  assert.equal(engine.gameOver, false);
});

test('horizontal movement respects board boundaries', () => {
  const engine = new TetrisEngine({ rng: () => 0.0 });
  for (let i = 0; i < 15; i++) engine.moveLeft();
  const minX = engine.activePiece.x;
  assert.equal(engine.moveLeft(), false);
  assert.equal(engine.activePiece.x, minX);

  for (let i = 0; i < 15; i++) engine.moveRight();
  const maxX = engine.activePiece.x;
  assert.equal(engine.moveRight(), false);
  assert.equal(engine.activePiece.x, maxX);
});

test('rotation with wall kick works near wall', () => {
  const engine = new TetrisEngine({ rng: () => 0.0 });
  // Force an I piece against the left wall in vertical orientation
  engine.activePiece = {
    type: 'I',
    matrix: [
      [0, 1, 0, 0],
      [0, 1, 0, 0],
      [0, 1, 0, 0],
      [0, 1, 0, 0],
    ],
    x: -1,
    y: 4,
  };
  assert.equal(engine.rotate(true), true);
  assert.ok(engine.activePiece.x >= 0);
});

test('hard drop awards 2 points per cell and locks piece', () => {
  const engine = new TetrisEngine({ rng: () => 0.25 });
  engine.activePiece = {
    type: 'O',
    matrix: [
      [1, 1],
      [1, 1],
    ],
    x: 4,
    y: 0,
  };
  const ghostY = engine.getGhostY();
  assert.equal(ghostY, ROWS - 2);
  const result = engine.hardDrop();
  assert.equal(result.locked, true);
  assert.equal(result.distance, ROWS - 2);
  assert.equal(engine.score, (ROWS - 2) * 2);
  assert.equal(engine.board[ROWS - 1][4], 'O');
  assert.equal(engine.board[ROWS - 1][5], 'O');
});

test('clears completed line, shifts rows down, and updates score/level', () => {
  const engine = new TetrisEngine({ rng: () => 0.0 });
  for (let c = 0; c < COLS - 2; c++) {
    engine.board[ROWS - 1][c] = 'J';
  }
  engine.board[ROWS - 2][0] = 'T';

  engine.activePiece = {
    type: 'O',
    matrix: [
      [1, 1],
      [1, 1],
    ],
    x: COLS - 2,
    y: ROWS - 2,
  };

  const result = engine.hardDrop();
  assert.deepEqual(result.clearedRows, [ROWS - 1]);
  assert.equal(engine.lines, 1);
  assert.equal(engine.score, 100);
  // Previous row ROWS - 2 shifted down to ROWS - 1
  assert.equal(engine.board[ROWS - 1][0], 'T');
  assert.equal(engine.board[ROWS - 1][COLS - 1], 'O');
});

test('hold swaps piece once per drop and resets on next spawn', () => {
  const engine = new TetrisEngine({ rng: fixedRngSequence([0.1, 0.2, 0.3, 0.4]) });
  const first = engine.activePiece.type;
  const second = engine.nextType;

  assert.equal(engine.holdPiece(), true);
  assert.equal(engine.holdType, first);
  assert.equal(engine.activePiece.type, second);
  assert.equal(engine.holdPiece(), false);

  engine.hardDrop();
  assert.equal(engine.canHold, true);
  assert.equal(engine.holdPiece(), true);
  assert.equal(engine.activePiece.type, first);
});

test('step advances gravity and triggers game over when spawn is blocked', () => {
  const engine = new TetrisEngine({ rng: () => 0.0, lockDelayMs: 200 });
  const initialY = engine.activePiece.y;
  const stepResult = engine.step(engine.getDropIntervalMs() + 10);
  assert.equal(stepResult.steppedDown, true);
  assert.equal(engine.activePiece.y, initialY + 1);

  // Fill spawn columns in top rows (leaving col 0 empty so lines aren't cleared)
  for (let r = 0; r < 4; r++) {
    for (let c = 1; c < COLS; c++) {
      engine.board[r][c] = 'Z';
    }
  }
  engine.activePiece = {
    type: 'O',
    matrix: [
      [1, 1],
      [1, 1],
    ],
    x: 4,
    y: 0,
  };
  const lock = engine.hardDrop();
  assert.equal(lock.gameOver, true);
  assert.equal(engine.gameOver, true);
});
