export const COLS = 10;
export const ROWS = 20;

export const TETROMINOS = {
  I: {
    color: 0x00e5ff,
    css: '#00e5ff',
    matrix: [
      [0, 0, 0, 0],
      [1, 1, 1, 1],
      [0, 0, 0, 0],
      [0, 0, 0, 0],
    ],
  },
  O: {
    color: 0xffd500,
    css: '#ffd500',
    matrix: [
      [1, 1],
      [1, 1],
    ],
  },
  T: {
    color: 0xb84dff,
    css: '#b84dff',
    matrix: [
      [0, 1, 0],
      [1, 1, 1],
      [0, 0, 0],
    ],
  },
  S: {
    color: 0x39e75f,
    css: '#39e75f',
    matrix: [
      [0, 1, 1],
      [1, 1, 0],
      [0, 0, 0],
    ],
  },
  Z: {
    color: 0xff3b5c,
    css: '#ff3b5c',
    matrix: [
      [1, 1, 0],
      [0, 1, 1],
      [0, 0, 0],
    ],
  },
  J: {
    color: 0x3b82f6,
    css: '#3b82f6',
    matrix: [
      [1, 0, 0],
      [1, 1, 1],
      [0, 0, 0],
    ],
  },
  L: {
    color: 0xff8c24,
    css: '#ff8c24',
    matrix: [
      [0, 0, 1],
      [1, 1, 1],
      [0, 0, 0],
    ],
  },
};

export const PIECE_TYPES = Object.keys(TETROMINOS);

const LINE_SCORES = {
  1: 100,
  2: 300,
  3: 500,
  4: 800,
};

function cloneMatrix(matrix) {
  return matrix.map((row) => [...row]);
}

export function rotateMatrixCW(matrix) {
  const n = matrix.length;
  const result = Array.from({ length: n }, () => Array(n).fill(0));
  for (let r = 0; r < n; r++) {
    for (let c = 0; c < n; c++) {
      result[c][n - 1 - r] = matrix[r][c];
    }
  }
  return result;
}

export function rotateMatrixCCW(matrix) {
  const n = matrix.length;
  const result = Array.from({ length: n }, () => Array(n).fill(0));
  for (let r = 0; r < n; r++) {
    for (let c = 0; c < n; c++) {
      result[n - 1 - c][r] = matrix[r][c];
    }
  }
  return result;
}

/**
 * Motor puro de regras de Tetris (tabuleiro 10x20, 7-bag, wall-kick, ghost e lock delay).
 */
export class TetrisEngine {
  constructor(options = {}) {
    this.cols = options.cols ?? COLS;
    this.rows = options.rows ?? ROWS;
    this.rng = options.rng ?? Math.random;
    this.lockDelayMs = options.lockDelayMs ?? 480;
    this.maxLockResets = options.maxLockResets ?? 10;
    this.reset();
  }

  reset() {
    this.board = Array.from({ length: this.rows }, () => Array(this.cols).fill(null));
    this.bag = [];
    this.score = 0;
    this.lines = 0;
    this.level = 1;
    this.paused = false;
    this.gameOver = false;
    this.holdType = null;
    this.canHold = true;
    this.dropAccumulatorMs = 0;
    this.lockTimerMs = 0;
    this.lockResets = 0;
    this.combo = -1;

    this.nextType = this.#drawFromBag();
    this.activePiece = null;
    this.#spawnNextPiece();
  }

  #drawFromBag() {
    if (this.bag.length === 0) {
      const fresh = [...PIECE_TYPES];
      for (let i = fresh.length - 1; i > 0; i--) {
        const j = Math.floor(this.rng() * (i + 1));
        [fresh[i], fresh[j]] = [fresh[j], fresh[i]];
      }
      this.bag = fresh;
    }
    return this.bag.pop();
  }

  #createPiece(type) {
    const def = TETROMINOS[type];
    const matrix = cloneMatrix(def.matrix);
    const x = Math.floor((this.cols - matrix[0].length) / 2);
    const y = 0;
    return { type, matrix, x, y };
  }

  #spawnNextPiece() {
    const type = this.nextType;
    this.nextType = this.#drawFromBag();
    const piece = this.#createPiece(type);
    this.activePiece = piece;
    this.canHold = true;
    this.lockTimerMs = 0;
    this.lockResets = 0;
    this.dropAccumulatorMs = 0;

    if (!this.isValidPosition(piece.matrix, piece.x, piece.y)) {
      this.gameOver = true;
    }
  }

  getDropIntervalMs() {
    return Math.max(90, 820 - (this.level - 1) * 65);
  }

  isValidPosition(matrix, offsetX, offsetY) {
    for (let r = 0; r < matrix.length; r++) {
      for (let c = 0; c < matrix[r].length; c++) {
        if (!matrix[r][c]) continue;
        const x = offsetX + c;
        const y = offsetY + r;
        if (x < 0 || x >= this.cols || y >= this.rows) {
          return false;
        }
        if (y >= 0 && this.board[y][x] !== null) {
          return false;
        }
      }
    }
    return true;
  }

  isGrounded() {
    if (!this.activePiece) return false;
    const { matrix, x, y } = this.activePiece;
    return !this.isValidPosition(matrix, x, y + 1);
  }

  getGhostY() {
    if (!this.activePiece) return 0;
    const { matrix, x, y } = this.activePiece;
    let ghostY = y;
    while (this.isValidPosition(matrix, x, ghostY + 1)) {
      ghostY++;
    }
    return ghostY;
  }

  #refreshLockDelay() {
    if (this.isGrounded() && this.lockResets < this.maxLockResets) {
      this.lockTimerMs = 0;
      this.lockResets++;
    }
  }

  moveHorizontal(dx) {
    if (this.paused || this.gameOver || !this.activePiece) return false;
    const { matrix, x, y } = this.activePiece;
    if (this.isValidPosition(matrix, x + dx, y)) {
      this.activePiece.x += dx;
      this.#refreshLockDelay();
      return true;
    }
    return false;
  }

  moveLeft() {
    return this.moveHorizontal(-1);
  }

  moveRight() {
    return this.moveHorizontal(1);
  }

  rotate(clockwise = true) {
    if (this.paused || this.gameOver || !this.activePiece) return false;
    if (this.activePiece.type === 'O') return false;

    const rotated = clockwise
      ? rotateMatrixCW(this.activePiece.matrix)
      : rotateMatrixCCW(this.activePiece.matrix);

    const kicks = this.activePiece.type === 'I'
      ? [[0, 0], [-1, 0], [1, 0], [-2, 0], [2, 0], [0, -1], [0, -2]]
      : [[0, 0], [-1, 0], [1, 0], [0, -1], [-1, -1], [1, -1], [-2, 0], [2, 0]];

    for (const [kx, ky] of kicks) {
      const nx = this.activePiece.x + kx;
      const ny = this.activePiece.y + ky;
      if (this.isValidPosition(rotated, nx, ny)) {
        this.activePiece.matrix = rotated;
        this.activePiece.x = nx;
        this.activePiece.y = ny;
        this.#refreshLockDelay();
        return true;
      }
    }
    return false;
  }

  holdPiece() {
    if (this.paused || this.gameOver || !this.activePiece || !this.canHold) {
      return false;
    }
    const currentType = this.activePiece.type;
    if (this.holdType === null) {
      this.holdType = currentType;
      this.#spawnNextPiece();
    } else {
      const swappedType = this.holdType;
      this.holdType = currentType;
      const piece = this.#createPiece(swappedType);
      this.activePiece = piece;
      this.lockTimerMs = 0;
      this.lockResets = 0;
      this.dropAccumulatorMs = 0;
      if (!this.isValidPosition(piece.matrix, piece.x, piece.y)) {
        this.gameOver = true;
      }
    }
    this.canHold = false;
    return true;
  }

  softDrop() {
    if (this.paused || this.gameOver || !this.activePiece) {
      return { moved: false, locked: false, clearedRows: [], levelUp: false, gameOver: this.gameOver };
    }
    const { matrix, x, y } = this.activePiece;
    if (this.isValidPosition(matrix, x, y + 1)) {
      this.activePiece.y += 1;
      this.score += 1;
      this.dropAccumulatorMs = 0;
      this.lockTimerMs = 0;
      return { moved: true, locked: false, clearedRows: [], levelUp: false, gameOver: false };
    }
    const lockResult = this.#lockActivePiece();
    return { moved: false, ...lockResult };
  }

  hardDrop() {
    if (this.paused || this.gameOver || !this.activePiece) {
      return { distance: 0, locked: false, clearedRows: [], levelUp: false, gameOver: this.gameOver };
    }
    const ghostY = this.getGhostY();
    const distance = Math.max(0, ghostY - this.activePiece.y);
    this.activePiece.y = ghostY;
    this.score += distance * 2;
    const lockResult = this.#lockActivePiece();
    return { distance, ...lockResult };
  }

  #lockActivePiece() {
    const { type, matrix, x, y } = this.activePiece;
    const lockedCells = [];

    for (let r = 0; r < matrix.length; r++) {
      for (let c = 0; c < matrix[r].length; c++) {
        if (!matrix[r][c]) continue;
        const bx = x + c;
        const by = y + r;
        if (by >= 0 && by < this.rows && bx >= 0 && bx < this.cols) {
          this.board[by][bx] = type;
          lockedCells.push({ x: bx, y: by, type });
        }
      }
    }

    const clearedRows = [];
    for (let r = 0; r < this.rows; r++) {
      if (this.board[r].every((cell) => cell !== null)) {
        clearedRows.push(r);
      }
    }

    let clearedSnapshot = [];
    if (clearedRows.length > 0) {
      clearedSnapshot = clearedRows.map((rowIdx) => ({
        row: rowIdx,
        cells: [...this.board[rowIdx]],
      }));
      const remaining = this.board.filter((_, idx) => !clearedRows.includes(idx));
      while (remaining.length < this.rows) {
        remaining.unshift(Array(this.cols).fill(null));
      }
      this.board = remaining;

      this.combo++;
      const count = clearedRows.length;
      const base = LINE_SCORES[count] ?? 800;
      const comboBonus = this.combo > 0 ? 50 * this.combo * this.level : 0;
      this.score += base * this.level + comboBonus;
      this.lines += count;
    } else {
      this.combo = -1;
    }

    const previousLevel = this.level;
    this.level = Math.floor(this.lines / 10) + 1;
    const levelUp = this.level > previousLevel;

    this.#spawnNextPiece();

    return {
      locked: true,
      lockedCells,
      clearedRows,
      clearedSnapshot,
      levelUp,
      gameOver: this.gameOver,
    };
  }

  togglePause() {
    if (this.gameOver) return this.paused;
    this.paused = !this.paused;
    return this.paused;
  }

  step(dtMs) {
    if (this.paused || this.gameOver || !this.activePiece) {
      return { steppedDown: false, locked: false, clearedRows: [], levelUp: false, gameOver: this.gameOver };
    }

    if (this.isGrounded()) {
      this.lockTimerMs += dtMs;
      if (this.lockTimerMs >= this.lockDelayMs) {
        const lockResult = this.#lockActivePiece();
        return { steppedDown: false, ...lockResult };
      }
      return { steppedDown: false, locked: false, clearedRows: [], levelUp: false, gameOver: false };
    }

    this.lockTimerMs = 0;
    this.dropAccumulatorMs += dtMs;
    const interval = this.getDropIntervalMs();

    let steppedDown = false;
    while (this.dropAccumulatorMs >= interval) {
      this.dropAccumulatorMs -= interval;
      if (this.isValidPosition(this.activePiece.matrix, this.activePiece.x, this.activePiece.y + 1)) {
        this.activePiece.y += 1;
        steppedDown = true;
        if (this.isGrounded()) {
          this.dropAccumulatorMs = 0;
          break;
        }
      } else {
        break;
      }
    }

    return { steppedDown, locked: false, clearedRows: [], levelUp: false, gameOver: false };
  }
}
