import * as THREE from 'three';
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js';
import { RoundedBoxGeometry } from 'three/examples/jsm/geometries/RoundedBoxGeometry.js';
import './style.css';
import { ChessEngine, chooseAIMove, FILES, RANKS } from './chess_engine.js';
import { identifyOpening } from './openings.js';
import { createChessPieceMesh } from './piece_meshes.js';
import { ChessSound } from './sound.js';

const SAVE_KEY = 'xadrez_3d_autosave_v1';
const STATS_KEY = 'xadrez_3d_stats_v1';

const PIECE_UNICODE = {
  w: { k: '♔', q: '♕', r: '♖', b: '♗', n: '♘', p: '♙' },
  b: { k: '♚', q: '♛', r: '♜', b: '♝', n: '♞', p: '♟' },
};

let engine = new ChessEngine();
const sound = new ChessSound();

// State
let gameMode = 'ai-b';
let aiDifficulty = 'medium';
let timeControlVal = '0|0';
let timeBaseSec = 0;
let timeIncSec = 0;
let clocks = { w: 0, b: 0 };
let timeoutWinner = null;
let selectedSquare = null;
let legalMovesForSelected = [];
let hintMove = null;
let pendingPromotion = null;
let aiTimeout = null;
let aiRequestId = 0;
let aiThinking = false;
let cameraSide = 'w';
let activeAnimations = [];
let gameStatsRecorded = false;
let stats = loadStats();

// Web Worker for non-blocking AI search
const aiWorker =
  typeof Worker !== 'undefined'
    ? new Worker(new URL('./ai_worker.js', import.meta.url), { type: 'module' })
    : null;
const pendingWorkerCallbacks = new Map();

if (aiWorker) {
  aiWorker.onmessage = (event) => {
    const { requestId, move } = event.data;
    const cb = pendingWorkerCallbacks.get(requestId);
    if (cb) {
      pendingWorkerCallbacks.delete(requestId);
      cb(move);
    }
  };
}

// --- DOM Elements ---
const appEl = document.getElementById('app');
const canvasEl = document.getElementById('scene');
const btnMobileDrawer = document.getElementById('btn-mobile-drawer');
const btnMobileClose = document.getElementById('btn-mobile-close');
const turnDot = document.getElementById('turn-dot');
const turnText = document.getElementById('turn-text');
const evalLabel = document.getElementById('eval-label');
const evalFill = document.getElementById('eval-fill');
const openingText = document.getElementById('opening-text');
const statusText = document.getElementById('status-text');
const statsText = document.getElementById('stats-text');
const clocksPanel = document.getElementById('clocks-panel');
const clockWhiteBox = document.getElementById('clock-white-box');
const clockBlackBox = document.getElementById('clock-black-box');
const clockWhiteEl = document.getElementById('clock-white');
const clockBlackEl = document.getElementById('clock-black');
const modeSelect = document.getElementById('mode-select');
const difficultyField = document.getElementById('difficulty-field');
const difficultySelect = document.getElementById('difficulty-select');
const timeSelect = document.getElementById('time-select');
const capWhiteEl = document.getElementById('cap-white');
const capBlackEl = document.getElementById('cap-black');
const moveHistoryEl = document.getElementById('move-history');
const castleActionsEl = document.getElementById('castle-actions');
const btnCastleK = document.getElementById('btn-castle-k');
const btnCastleQ = document.getElementById('btn-castle-q');
const btnHint = document.getElementById('btn-hint');
const btnNew = document.getElementById('btn-new');
const btnUndo = document.getElementById('btn-undo');
const btnFlip = document.getElementById('btn-flip');
const btnMute = document.getElementById('btn-mute');
const promoModal = document.getElementById('promo-modal');
const gameOverModal = document.getElementById('gameover-modal');
const gameOverTitle = document.getElementById('gameover-title');
const gameOverSubtitle = document.getElementById('gameover-subtitle');
const btnGameOverNew = document.getElementById('btn-gameover-new');

// --- Persistence & Stats ---
function parseTimeControl(value) {
  const [b, inc] = String(value || '0|0').split('|').map(Number);
  return { baseSec: Number.isFinite(b) ? b : 0, incSec: Number.isFinite(inc) ? inc : 0 };
}

function loadStats() {
  try {
    const raw = localStorage.getItem(STATS_KEY);
    if (raw) {
      const parsed = JSON.parse(raw);
      return {
        wins: Number(parsed.wins) || 0,
        draws: Number(parsed.draws) || 0,
        losses: Number(parsed.losses) || 0,
      };
    }
  } catch {
    // Ignore storage errors
  }
  return { wins: 0, draws: 0, losses: 0 };
}

function saveStats() {
  try {
    localStorage.setItem(STATS_KEY, JSON.stringify(stats));
  } catch {
    // Ignore storage errors
  }
}

function recordResultIfNeeded() {
  if (gameStatsRecorded || gameMode === 'pvp' || !isAnyGameOver()) return;
  gameStatsRecorded = true;
  const humanColor = gameMode === 'ai-b' ? 'w' : 'b';
  const winner = timeoutWinner ?? engine.winner;
  if (!winner) {
    stats.draws += 1;
  } else if (winner === humanColor) {
    stats.wins += 1;
  } else {
    stats.losses += 1;
  }
  saveStats();
}

function saveGameState() {
  try {
    localStorage.setItem(
      SAVE_KEY,
      JSON.stringify({
        gameMode,
        aiDifficulty,
        timeControlVal,
        clocks,
        timeoutWinner,
        moves: engine.exportMoves(),
      }),
    );
  } catch {
    // Ignore storage errors
  }
}

function tryRestoreSavedGame() {
  try {
    const raw = localStorage.getItem(SAVE_KEY);
    if (!raw) return false;
    const saved = JSON.parse(raw);
    if (!saved || !Array.isArray(saved.moves)) return false;

    gameMode = ['ai-b', 'ai-w', 'pvp'].includes(saved.gameMode) ? saved.gameMode : 'ai-b';
    aiDifficulty = ['easy', 'medium', 'hard'].includes(saved.aiDifficulty)
      ? saved.aiDifficulty
      : 'medium';
    timeControlVal = typeof saved.timeControlVal === 'string' ? saved.timeControlVal : '0|0';
    const parsedTc = parseTimeControl(timeControlVal);
    timeBaseSec = parsedTc.baseSec;
    timeIncSec = parsedTc.incSec;

    modeSelect.value = gameMode;
    difficultySelect.value = aiDifficulty;
    timeSelect.value = timeControlVal;

    engine = ChessEngine.fromMoves(saved.moves);
    clocks =
      saved.clocks && Number.isFinite(saved.clocks.w) && Number.isFinite(saved.clocks.b)
        ? { w: saved.clocks.w, b: saved.clocks.b }
        : { w: timeBaseSec, b: timeBaseSec };
    timeoutWinner = saved.timeoutWinner ?? null;
    gameStatsRecorded = isAnyGameOver();
    return true;
  } catch {
    return false;
  }
}

// --- Three.js Setup ---
const renderer = new THREE.WebGLRenderer({
  canvas: canvasEl,
  antialias: true,
  powerPreference: 'high-performance',
});
renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
renderer.setSize(window.innerWidth, window.innerHeight);
renderer.shadowMap.enabled = true;
renderer.shadowMap.type = THREE.PCFSoftShadowMap;
renderer.toneMapping = THREE.ACESFilmicToneMapping;
renderer.toneMappingExposure = 1.12;

const scene = new THREE.Scene();
scene.background = new THREE.Color(0x080c16);
scene.fog = new THREE.FogExp2(0x080c16, 0.018);

const camera = new THREE.PerspectiveCamera(42, window.innerWidth / window.innerHeight, 0.1, 100);
camera.position.set(0, 9.5, 10.5);

const controls = new OrbitControls(camera, renderer.domElement);
controls.enableDamping = true;
controls.dampingFactor = 0.08;
controls.enablePan = false;
controls.minDistance = 7;
controls.maxDistance = 30;
controls.minPolarAngle = 0.25;
controls.maxPolarAngle = Math.PI * 0.45;
controls.target.set(0, 0.2, 0);

// --- Lighting ---
const hemi = new THREE.HemisphereLight(0xfef3c7, 0x1e293b, 0.9);
scene.add(hemi);

const dirLight = new THREE.DirectionalLight(0xfffbeb, 1.9);
dirLight.position.set(6, 14, 8);
dirLight.castShadow = true;
dirLight.shadow.mapSize.set(2048, 2048);
dirLight.shadow.camera.near = 2;
dirLight.shadow.camera.far = 35;
dirLight.shadow.camera.left = -7;
dirLight.shadow.camera.right = 7;
dirLight.shadow.camera.top = 7;
dirLight.shadow.camera.bottom = -7;
dirLight.shadow.bias = -0.0005;
scene.add(dirLight);

const rimLight = new THREE.PointLight(0x38bdf8, 18, 26);
rimLight.position.set(-7, 5, -7);
scene.add(rimLight);

function squareToWorld(r, c) {
  return { x: c - 3.5, z: r - 3.5 };
}

// --- 3D Board Construction ---
const squareMeshes = Array.from({ length: 8 }, () => Array(8).fill(null));
const squareBaseColors = Array.from({ length: 8 }, () => Array(8).fill(0));
const indicatorMeshes = [];
const piecesGroup = new THREE.Group();
scene.add(piecesGroup);

function buildBoard() {
  const tableGeo = new THREE.PlaneGeometry(50, 50);
  const tableMat = new THREE.MeshStandardMaterial({
    color: 0x0b1120,
    roughness: 0.78,
    metalness: 0.15,
  });
  const table = new THREE.Mesh(tableGeo, tableMat);
  table.rotation.x = -Math.PI / 2;
  table.position.y = -0.46;
  table.receiveShadow = true;
  scene.add(table);

  const frameGeo = new RoundedBoxGeometry(9.2, 0.45, 9.2, 3, 0.08);
  const frameMat = new THREE.MeshStandardMaterial({
    color: 0x3a2417,
    roughness: 0.48,
    metalness: 0.12,
  });
  const frame = new THREE.Mesh(frameGeo, frameMat);
  frame.position.y = -0.23;
  frame.receiveShadow = true;
  frame.castShadow = true;
  scene.add(frame);

  const sqGeo = new THREE.BoxGeometry(1, 0.12, 1);
  for (let r = 0; r < 8; r++) {
    for (let c = 0; c < 8; c++) {
      const isLight = (r + c) % 2 === 0;
      const baseColor = isLight ? 0xe7dcc6 : 0x5c4030;
      squareBaseColors[r][c] = baseColor;

      const mat = new THREE.MeshStandardMaterial({
        color: baseColor,
        roughness: 0.42,
        metalness: 0.08,
      });
      const sq = new THREE.Mesh(sqGeo, mat);
      const { x, z } = squareToWorld(r, c);
      sq.position.set(x, -0.02, z);
      sq.receiveShadow = true;
      sq.userData = { square: { r, c } };
      scene.add(sq);
      squareMeshes[r][c] = sq;
    }
  }

  const addCoordLabel = (text, x, z) => {
    const cvs = document.createElement('canvas');
    cvs.width = 64;
    cvs.height = 64;
    const ctx = cvs.getContext('2d');
    ctx.fillStyle = '#d6c7b2';
    ctx.font = 'bold 34px Segoe UI, sans-serif';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.fillText(text, 32, 32);

    const tex = new THREE.CanvasTexture(cvs);
    const mat = new THREE.MeshBasicMaterial({ map: tex, transparent: true });
    const plane = new THREE.Mesh(new THREE.PlaneGeometry(0.4, 0.4), mat);
    plane.rotation.x = -Math.PI / 2;
    plane.position.set(x, 0.01, z);
    scene.add(plane);
  };

  for (let c = 0; c < 8; c++) {
    addCoordLabel(FILES[c].toUpperCase(), c - 3.5, 4.3);
  }
  for (let r = 0; r < 8; r++) {
    addCoordLabel(RANKS[r], -4.3, r - 3.5);
  }
}

buildBoard();

// --- Piece Mesh Management ---
const boardPieceMeshes = Array.from({ length: 8 }, () => Array(8).fill(null));

function rebuildPieceMeshes(skipSquares = []) {
  while (piecesGroup.children.length > 0) {
    piecesGroup.remove(piecesGroup.children[0]);
  }
  for (let r = 0; r < 8; r++) {
    for (let c = 0; c < 8; c++) {
      boardPieceMeshes[r][c] = null;
      const p = engine.board[r][c];
      if (!p) continue;

      const mesh = createChessPieceMesh(p.type, p.color);
      const { x, z } = squareToWorld(r, c);
      mesh.position.set(x, 0.04, z);
      mesh.userData = { square: { r, c } };
      mesh.traverse((child) => {
        if (child.isMesh) {
          child.userData = { square: { r, c } };
        }
      });
      if (skipSquares.some((s) => s.r === r && s.c === c)) {
        mesh.visible = false;
      }
      piecesGroup.add(mesh);
      boardPieceMeshes[r][c] = mesh;
    }
  }
}

function clearIndicators() {
  while (indicatorMeshes.length > 0) {
    const m = indicatorMeshes.pop();
    scene.remove(m);
    m.geometry.dispose();
    m.material.dispose();
  }
}

function spawnRingMarker(r, c, color, innerR, outerR, userData = {}) {
  const { x, z } = squareToWorld(r, c);
  const geo = new THREE.RingGeometry(innerR, outerR, 28);
  const mat = new THREE.MeshBasicMaterial({
    color,
    transparent: true,
    opacity: 0.88,
    side: THREE.DoubleSide,
  });
  const marker = new THREE.Mesh(geo, mat);
  marker.rotation.x = -Math.PI / 2;
  marker.position.set(x, 0.053, z);
  marker.userData = { square: { r, c }, ...userData };
  scene.add(marker);
  indicatorMeshes.push(marker);
}

function updateBoardHighlights() {
  clearIndicators();

  const lastRecord = engine.moveLog[engine.moveLog.length - 1];
  const kingInCheck =
    engine.status === 'check' || engine.status === 'checkmate'
      ? engine.findKing(engine.turn)
      : null;

  for (let r = 0; r < 8; r++) {
    for (let c = 0; c < 8; c++) {
      const sq = squareMeshes[r][c];
      sq.material.color.setHex(squareBaseColors[r][c]);
      sq.material.emissive.setHex(0x000000);
      sq.material.emissiveIntensity = 0;

      if (
        lastRecord &&
        ((lastRecord.move.fromR === r && lastRecord.move.fromC === c) ||
          (lastRecord.move.toR === r && lastRecord.move.toC === c))
      ) {
        sq.material.emissive.setHex(0xfacc15);
        sq.material.emissiveIntensity = 0.25;
      }

      if (
        hintMove &&
        ((hintMove.fromR === r && hintMove.fromC === c) ||
          (hintMove.toR === r && hintMove.toC === c))
      ) {
        sq.material.emissive.setHex(0x10b981);
        sq.material.emissiveIntensity = 0.55;
      }

      if (selectedSquare && selectedSquare.r === r && selectedSquare.c === c) {
        sq.material.emissive.setHex(0x38bdf8);
        sq.material.emissiveIntensity = 0.5;
      }

      if (kingInCheck && kingInCheck.r === r && kingInCheck.c === c) {
        sq.material.emissive.setHex(0xf43f5e);
        sq.material.emissiveIntensity = 0.7;
      }
    }
  }

  for (const move of legalMovesForSelected) {
    if (move.castle) {
      spawnRingMarker(move.toR, move.toC, 0xfbbf24, 0.2, 0.42, { castleMove: move });
      const rookCol = move.castle === 'K' ? 7 : 0;
      spawnRingMarker(move.toR, rookCol, 0xfbbf24, 0.34, 0.45, { castleMove: move });
      continue;
    }

    const { x, z } = squareToWorld(move.toR, move.toC);
    const isCapture = Boolean(move.capture || move.isEnPassant);
    const geo = isCapture
      ? new THREE.RingGeometry(0.32, 0.44, 24)
      : new THREE.CircleGeometry(0.18, 24);
    const mat = new THREE.MeshBasicMaterial({
      color: isCapture ? 0xf43f5e : 0x38bdf8,
      transparent: true,
      opacity: 0.82,
      side: THREE.DoubleSide,
    });
    const marker = new THREE.Mesh(geo, mat);
    marker.rotation.x = -Math.PI / 2;
    marker.position.set(x, 0.052, z);
    marker.userData = { square: { r: move.toR, c: move.toC } };
    scene.add(marker);
    indicatorMeshes.push(marker);
  }

  if (selectedSquare) {
    const selPiece = engine.board[selectedSquare.r][selectedSquare.c];
    if (selPiece?.type === 'r') {
      const castles = engine.getAvailableCastles(selPiece.color);
      const homeRow = selPiece.color === 'w' ? 7 : 0;
      if (selectedSquare.r === homeRow && selectedSquare.c === 7 && castles.kingSide) {
        spawnRingMarker(homeRow, 4, 0xfbbf24, 0.34, 0.45, { castleMove: castles.kingSide });
      } else if (selectedSquare.r === homeRow && selectedSquare.c === 0 && castles.queenSide) {
        spawnRingMarker(homeRow, 4, 0xfbbf24, 0.34, 0.45, { castleMove: castles.queenSide });
      }
    }
  }
}

function formatClock(seconds) {
  const s = Math.max(0, Math.ceil(seconds));
  const mins = Math.floor(s / 60);
  const rem = s % 60;
  return `${String(mins).padStart(2, '0')}:${String(rem).padStart(2, '0')}`;
}

function isAnyGameOver() {
  return Boolean(timeoutWinner) || engine.isGameOver();
}

function updateClocksUI() {
  if (timeBaseSec <= 0) {
    clocksPanel.classList.add('hidden');
    return;
  }
  clocksPanel.classList.remove('hidden');
  clockWhiteEl.textContent = formatClock(clocks.w);
  clockBlackEl.textContent = formatClock(clocks.b);

  clockWhiteBox.classList.toggle('active', !isAnyGameOver() && engine.turn === 'w');
  clockBlackBox.classList.toggle('active', !isAnyGameOver() && engine.turn === 'b');
  clockWhiteBox.classList.toggle('low', clocks.w > 0 && clocks.w <= 20);
  clockBlackBox.classList.toggle('low', clocks.b > 0 && clocks.b <= 20);
}

function updateEvaluationBar() {
  const cp = engine.evaluateBoard();
  if (engine.status === 'checkmate') {
    evalLabel.textContent = engine.winner === 'w' ? '+Mate' : '-Mate';
    evalFill.style.width = engine.winner === 'w' ? '100%' : '0%';
    return;
  }
  const pawns = cp / 100;
  evalLabel.textContent = `${pawns > 0 ? '+' : ''}${pawns.toFixed(1)}`;
  const clamped = Math.max(-10, Math.min(10, pawns));
  const pct = 50 + (clamped / 10) * 46;
  evalFill.style.width = `${pct.toFixed(1)}%`;
}

function updateHUD() {
  const isWhiteTurn = engine.turn === 'w';
  turnDot.className = `dot ${isWhiteTurn ? 'dot-white' : 'dot-black'}`;
  turnText.textContent = isWhiteTurn ? 'Brancas' : 'Pretas';

  updateEvaluationBar();
  updateClocksUI();

  openingText.textContent = identifyOpening(engine.moveLog);
  statsText.textContent = `Placar vs IA — V: ${stats.wins} · E: ${stats.draws} · D: ${stats.losses}`;
  statsText.style.display = gameMode === 'pvp' ? 'none' : 'block';

  statusText.className = 'status-sub';
  if (timeoutWinner) {
    statusText.textContent = `Tempo esgotado! Vitória das ${timeoutWinner === 'w' ? 'Brancas' : 'Pretas'}.`;
    statusText.classList.add('check');
  } else if (engine.status === 'checkmate') {
    statusText.textContent = `Xeque-Mate! Vitória das ${engine.winner === 'w' ? 'Brancas' : 'Pretas'}.`;
    statusText.classList.add('check');
  } else if (engine.status === 'stalemate') {
    statusText.textContent = 'Empate por afogamento.';
  } else if (engine.status === 'draw_repetition') {
    statusText.textContent = 'Empate por repetição tripla.';
  } else if (engine.status === 'draw_insufficient') {
    statusText.textContent = 'Empate por material insuficiente.';
  } else if (engine.status === 'draw_50') {
    statusText.textContent = 'Empate pela regra dos 50 lances.';
  } else if (engine.status === 'check') {
    statusText.textContent = `XEQUE nas ${isWhiteTurn ? 'Brancas' : 'Pretas'}!`;
    statusText.classList.add('check');
  } else if (aiThinking || isAITurn()) {
    statusText.textContent = 'IA calculando em segundo plano...';
  } else {
    statusText.textContent = selectedSquare ? 'Escolha a casa de destino' : 'Selecione uma peça para jogar';
  }

  const canHumanAct = !isAnyGameOver() && !isAITurn() && !aiThinking && activeAnimations.length === 0;
  const castles = canHumanAct ? engine.getAvailableCastles(engine.turn) : { kingSide: null, queenSide: null };
  btnCastleK.classList.toggle('hidden', !castles.kingSide);
  btnCastleQ.classList.toggle('hidden', !castles.queenSide);
  castleActionsEl.classList.toggle('hidden', !castles.kingSide && !castles.queenSide);

  capWhiteEl.textContent =
    engine.captured.w.length > 0
      ? engine.captured.w.map((t) => PIECE_UNICODE.b[t]).join(' ')
      : '—';
  capBlackEl.textContent =
    engine.captured.b.length > 0
      ? engine.captured.b.map((t) => PIECE_UNICODE.w[t]).join(' ')
      : '—';

  moveHistoryEl.innerHTML = '';
  for (let i = 0; i < engine.moveLog.length; i += 2) {
    const li = document.createElement('li');
    const wSan = engine.moveLog[i]?.san ?? '';
    const bSan = engine.moveLog[i + 1]?.san ?? '';
    li.textContent = `${wSan}   ${bSan}`;
    moveHistoryEl.appendChild(li);
  }
  moveHistoryEl.scrollTop = moveHistoryEl.scrollHeight;

  btnUndo.disabled = engine.history.length === 0 || activeAnimations.length > 0;
  btnHint.disabled = !canHumanAct;
  btnMute.textContent = sound.muted ? 'Som: Mudo (M)' : 'Som: Ligado (M)';
  difficultyField.style.display = gameMode === 'pvp' ? 'none' : 'flex';

  if (isAnyGameOver()) {
    recordResultIfNeeded();
    statsText.textContent = `Placar vs IA — V: ${stats.wins} · E: ${stats.draws} · D: ${stats.losses}`;
    if (timeoutWinner) {
      gameOverTitle.textContent = 'Tempo Esgotado!';
      gameOverSubtitle.textContent = `As ${timeoutWinner === 'w' ? 'Brancas' : 'Pretas'} venceram no relógio!`;
    } else if (engine.status === 'checkmate') {
      gameOverTitle.textContent = 'Xeque-Mate!';
      gameOverSubtitle.textContent = `As ${engine.winner === 'w' ? 'Brancas' : 'Pretas'} venceram!`;
    } else {
      gameOverTitle.textContent = 'Empate!';
      gameOverSubtitle.textContent = statusText.textContent;
    }
    gameOverModal.classList.remove('hidden');
  } else {
    gameOverModal.classList.add('hidden');
  }
}

function isAITurn() {
  if (gameMode === 'ai-b') return engine.turn === 'b';
  if (gameMode === 'ai-w') return engine.turn === 'w';
  return false;
}

function setCameraSide(side) {
  cameraSide = side;
  const aspect = window.innerWidth / Math.max(1, window.innerHeight);
  const portraitScale = aspect < 1 ? Math.min(2.15, 0.9 / Math.max(aspect, 0.42)) : 1;
  const zDist = 10.5 * portraitScale;
  const yHeight = 9.5 * portraitScale;
  camera.position.set(0, yHeight, side === 'w' ? zDist : -zDist);
  controls.target.set(0, 0.2, 0);
  controls.update();
}

function enqueuePieceAnimation(type, color, fromR, fromC, toR, toC, arcHeight = 0.45) {
  const fromPos = squareToWorld(fromR, fromC);
  const toPos = squareToWorld(toR, toC);
  const animMesh = createChessPieceMesh(type, color);
  animMesh.position.set(fromPos.x, 0.04, fromPos.z);
  scene.add(animMesh);
  activeAnimations.push({
    mesh: animMesh,
    startX: fromPos.x,
    startZ: fromPos.z,
    endX: toPos.x,
    endZ: toPos.z,
    arcHeight,
    progress: 0,
    duration: 0.24,
    targetSquare: { r: toR, c: toC },
  });
}

function performMoveWithAnimation(fromR, fromC, toR, toC, promotion = 'q') {
  if (isAnyGameOver()) return false;
  const movingMesh = boardPieceMeshes[fromR][fromC];
  const record = engine.makeMove(fromR, fromC, toR, toC, promotion);
  if (!record) return false;

  if (timeBaseSec > 0 && timeIncSec > 0 && engine.moveLog.length > 1) {
    clocks[record.piece.color] += timeIncSec;
  }

  selectedSquare = null;
  legalMovesForSelected = [];
  hintMove = null;

  if (record.status === 'checkmate' || record.status === 'stalemate' || record.status === 'draw_repetition') {
    sound.gameOver();
  } else if (record.status === 'check') {
    sound.check();
  } else if (record.move.castle) {
    sound.castle();
  } else if (record.captured) {
    sound.capture();
  } else {
    sound.move();
  }

  const skipSquares = [{ r: toR, c: toC }];
  if (record.move.castle === 'K') skipSquares.push({ r: toR, c: 5 });
  else if (record.move.castle === 'Q') skipSquares.push({ r: toR, c: 3 });

  rebuildPieceMeshes(skipSquares);
  updateBoardHighlights();
  updateHUD();
  saveGameState();

  if (movingMesh) {
    enqueuePieceAnimation(record.piece.type, record.piece.color, fromR, fromC, toR, toC, 0.45);
    if (record.move.castle === 'K') {
      enqueuePieceAnimation('r', record.piece.color, toR, 7, toR, 5, 0.25);
    } else if (record.move.castle === 'Q') {
      enqueuePieceAnimation('r', record.piece.color, toR, 0, toR, 3, 0.25);
    }
  } else {
    scheduleAIIfNeeded();
  }

  return true;
}

function requestAIMoveAsync(difficulty, useBook, callback) {
  const reqId = ++aiRequestId;
  aiThinking = true;
  updateHUD();

  if (aiWorker) {
    pendingWorkerCallbacks.set(reqId, (move) => {
      if (reqId !== aiRequestId) return;
      aiThinking = false;
      callback(move);
    });
    aiWorker.postMessage({
      requestId: reqId,
      moves: engine.exportMoves(),
      difficulty,
      useBook,
    });
    return;
  }

  const move = chooseAIMove(engine, difficulty, Math.random, { useBook });
  if (reqId === aiRequestId) {
    aiThinking = false;
    callback(move);
  }
}

function cancelPendingAI() {
  clearTimeout(aiTimeout);
  aiRequestId++;
  aiThinking = false;
  pendingWorkerCallbacks.clear();
}

function scheduleAIIfNeeded() {
  clearTimeout(aiTimeout);
  if (!isAITurn() || isAnyGameOver() || aiThinking) {
    return;
  }
  updateHUD();
  aiTimeout = setTimeout(() => {
    if (!isAITurn() || isAnyGameOver()) return;
    requestAIMoveAsync(aiDifficulty, aiDifficulty !== 'easy', (move) => {
      if (isAnyGameOver() || !isAITurn()) {
        updateHUD();
        return;
      }
      if (move) {
        performMoveWithAnimation(move.fromR, move.fromC, move.toR, move.toC, move.promotion ?? 'q');
      } else {
        updateHUD();
      }
    });
  }, 140);
}

// --- Mouse Raycasting ---
const raycaster = new THREE.Raycaster();
const pointer = new THREE.Vector2();
let pointerDownPos = null;

canvasEl.addEventListener('pointerdown', (e) => {
  pointerDownPos = { x: e.clientX, y: e.clientY };
});

canvasEl.addEventListener('pointerup', (e) => {
  if (!pointerDownPos) return;
  const dist = Math.hypot(e.clientX - pointerDownPos.x, e.clientY - pointerDownPos.y);
  pointerDownPos = null;
  const tapTolerance = e.pointerType === 'touch' ? 14 : 6;
  if (dist > tapTolerance) return;
  if (activeAnimations.length > 0 || pendingPromotion || isAITurn() || aiThinking || isAnyGameOver()) {
    return;
  }

  const rect = canvasEl.getBoundingClientRect();
  pointer.x = ((e.clientX - rect.left) / rect.width) * 2 - 1;
  pointer.y = -((e.clientY - rect.top) / rect.height) * 2 + 1;

  raycaster.setFromCamera(pointer, camera);
  const targets = [...indicatorMeshes, ...piecesGroup.children, ...squareMeshes.flat()];
  const hits = raycaster.intersectObjects(targets, true);
  if (hits.length === 0) {
    selectedSquare = null;
    legalMovesForSelected = [];
    updateBoardHighlights();
    updateHUD();
    return;
  }

  let castleMove = null;
  let sq = null;
  for (const hit of hits) {
    if (hit.object.userData?.castleMove) {
      castleMove = hit.object.userData.castleMove;
      break;
    }
    if (!sq && hit.object.userData?.square) {
      sq = hit.object.userData.square;
    }
  }

  if (castleMove) {
    performMoveWithAnimation(castleMove.fromR, castleMove.fromC, castleMove.toR, castleMove.toC);
    return;
  }
  if (!sq) return;

  handleSquareClick(sq.r, sq.c);
});

function handleSquareClick(r, c) {
  if (selectedSquare) {
    const selPiece = engine.board[selectedSquare.r][selectedSquare.c];
    const clickedPiece = engine.board[r][c];

    if (selPiece && clickedPiece && selPiece.color === clickedPiece.color) {
      const castles = engine.getAvailableCastles(selPiece.color);
      const homeRow = selPiece.color === 'w' ? 7 : 0;
      if (selPiece.type === 'k' && clickedPiece.type === 'r' && r === homeRow) {
        if (c === 7 && castles.kingSide) {
          performMoveWithAnimation(homeRow, 4, homeRow, 6);
          return;
        }
        if (c === 0 && castles.queenSide) {
          performMoveWithAnimation(homeRow, 4, homeRow, 2);
          return;
        }
      }
      if (selPiece.type === 'r' && clickedPiece.type === 'k' && r === homeRow && c === 4) {
        if (selectedSquare.c === 7 && castles.kingSide) {
          performMoveWithAnimation(homeRow, 4, homeRow, 6);
          return;
        }
        if (selectedSquare.c === 0 && castles.queenSide) {
          performMoveWithAnimation(homeRow, 4, homeRow, 2);
          return;
        }
      }
    }

    const matchingMoves = legalMovesForSelected.filter((m) => m.toR === r && m.toC === c);
    if (matchingMoves.length > 0) {
      const needsPromotion = matchingMoves.some((m) => m.promotion);
      if (needsPromotion) {
        pendingPromotion = {
          fromR: selectedSquare.r,
          fromC: selectedSquare.c,
          toR: r,
          toC: c,
        };
        promoModal.classList.remove('hidden');
        return;
      }
      performMoveWithAnimation(selectedSquare.r, selectedSquare.c, r, c);
      return;
    }
  }

  const clickedPiece = engine.board[r][c];
  if (clickedPiece && clickedPiece.color === engine.turn) {
    if (selectedSquare && selectedSquare.r === r && selectedSquare.c === c) {
      selectedSquare = null;
      legalMovesForSelected = [];
    } else {
      selectedSquare = { r, c };
      legalMovesForSelected = engine.getLegalMovesForSquare(r, c);
    }
  } else {
    selectedSquare = null;
    legalMovesForSelected = [];
  }

  updateBoardHighlights();
  updateHUD();
}

// --- UI Events ---
document.querySelectorAll('.promo-btn').forEach((btn) => {
  btn.addEventListener('click', () => {
    if (!pendingPromotion) return;
    const { fromR, fromC, toR, toC } = pendingPromotion;
    const promo = btn.dataset.piece;
    pendingPromotion = null;
    promoModal.classList.add('hidden');
    performMoveWithAnimation(fromR, fromC, toR, toC, promo);
  });
});

function clearAnimations() {
  while (activeAnimations.length > 0) {
    const anim = activeAnimations.pop();
    scene.remove(anim.mesh);
  }
}

function startNewGame() {
  appEl.classList.remove('mobile-drawer-open');
  cancelPendingAI();
  clearAnimations();
  engine.reset();
  timeoutWinner = null;
  gameStatsRecorded = false;
  const parsed = parseTimeControl(timeControlVal);
  timeBaseSec = parsed.baseSec;
  timeIncSec = parsed.incSec;
  clocks = { w: timeBaseSec, b: timeBaseSec };
  selectedSquare = null;
  legalMovesForSelected = [];
  hintMove = null;
  pendingPromotion = null;
  promoModal.classList.add('hidden');
  setCameraSide(gameMode === 'ai-w' ? 'b' : 'w');
  rebuildPieceMeshes();
  updateBoardHighlights();
  updateHUD();
  saveGameState();
  scheduleAIIfNeeded();
}

function undoMove() {
  if (activeAnimations.length > 0 || engine.history.length === 0) return;
  cancelPendingAI();
  timeoutWinner = null;
  if (gameMode !== 'pvp') {
    engine.undo();
    if (isAITurn() && engine.history.length > 0) {
      engine.undo();
    }
  } else {
    engine.undo();
  }
  selectedSquare = null;
  legalMovesForSelected = [];
  hintMove = null;
  rebuildPieceMeshes();
  updateBoardHighlights();
  updateHUD();
  saveGameState();
}

function triggerHint() {
  if (isAnyGameOver() || isAITurn() || aiThinking || activeAnimations.length > 0) return;
  requestAIMoveAsync('medium', true, (best) => {
    if (best && !isAITurn() && !isAnyGameOver()) {
      hintMove = best;
      updateBoardHighlights();
    }
    updateHUD();
  });
}

function executeCastleButton(side) {
  if (isAnyGameOver() || isAITurn() || aiThinking || activeAnimations.length > 0) return;
  const castles = engine.getAvailableCastles(engine.turn);
  const move = side === 'K' ? castles.kingSide : castles.queenSide;
  if (move) {
    performMoveWithAnimation(move.fromR, move.fromC, move.toR, move.toC);
  }
}

modeSelect.addEventListener('change', () => {
  gameMode = modeSelect.value;
  startNewGame();
});

difficultySelect.addEventListener('change', () => {
  aiDifficulty = difficultySelect.value;
  saveGameState();
});

timeSelect.addEventListener('change', () => {
  timeControlVal = timeSelect.value;
  startNewGame();
});

btnCastleK.addEventListener('click', () => executeCastleButton('K'));
btnCastleQ.addEventListener('click', () => executeCastleButton('Q'));
btnHint.addEventListener('click', triggerHint);
btnNew.addEventListener('click', startNewGame);
btnGameOverNew.addEventListener('click', startNewGame);
btnUndo.addEventListener('click', undoMove);
btnFlip.addEventListener('click', () => {
  setCameraSide(cameraSide === 'w' ? 'b' : 'w');
});
btnMute.addEventListener('click', () => {
  sound.toggleMute();
  updateHUD();
});

btnMobileDrawer?.addEventListener('click', () => {
  appEl.classList.add('mobile-drawer-open');
});

btnMobileClose?.addEventListener('click', () => {
  appEl.classList.remove('mobile-drawer-open');
});

window.addEventListener('keydown', (e) => {
  if (e.code === 'KeyU') undoMove();
  else if (e.code === 'KeyH') triggerHint();
  else if (e.code === 'KeyC') setCameraSide(cameraSide === 'w' ? 'b' : 'w');
  else if (e.code === 'KeyM') {
    sound.toggleMute();
    updateHUD();
  }
});

window.addEventListener('resize', () => {
  camera.aspect = window.innerWidth / window.innerHeight;
  camera.updateProjectionMatrix();
  renderer.setSize(window.innerWidth, window.innerHeight);
  setCameraSide(cameraSide);
});

// --- Initialization (Restore saved match or start fresh) ---
if (tryRestoreSavedGame()) {
  setCameraSide(gameMode === 'ai-w' ? 'b' : 'w');
  rebuildPieceMeshes();
  updateBoardHighlights();
  updateHUD();
  scheduleAIIfNeeded();
} else {
  startNewGame();
}

let lastTime = performance.now();
function animate(now) {
  requestAnimationFrame(animate);
  const dtSec = Math.min(0.1, (now - lastTime) / 1000);
  lastTime = now;

  if (timeBaseSec > 0 && !isAnyGameOver() && engine.moveLog.length > 0 && !pendingPromotion) {
    clocks[engine.turn] = Math.max(0, clocks[engine.turn] - dtSec);
    if (clocks[engine.turn] <= 0) {
      timeoutWinner = engine.turn === 'w' ? 'b' : 'w';
      cancelPendingAI();
      sound.gameOver();
      updateHUD();
      saveGameState();
    } else {
      updateClocksUI();
    }
  }

  if (activeAnimations.length > 0) {
    let finishedAll = true;
    for (const anim of activeAnimations) {
      if (anim.progress >= 1) continue;
      anim.progress = Math.min(1, anim.progress + dtSec / anim.duration);
      const t = anim.progress;
      const eased = 1 - Math.pow(1 - t, 3);
      anim.mesh.position.x = anim.startX + (anim.endX - anim.startX) * eased;
      anim.mesh.position.z = anim.startZ + (anim.endZ - anim.startZ) * eased;
      anim.mesh.position.y = 0.04 + Math.sin(t * Math.PI) * anim.arcHeight;
      if (t < 1) finishedAll = false;
    }

    if (finishedAll) {
      for (const anim of activeAnimations) {
        scene.remove(anim.mesh);
        const { r, c } = anim.targetSquare;
        if (boardPieceMeshes[r][c]) {
          boardPieceMeshes[r][c].visible = true;
        }
      }
      activeAnimations = [];
      updateHUD();
      scheduleAIIfNeeded();
    }
  }

  controls.update();
  renderer.render(scene, camera);
}

requestAnimationFrame(animate);
