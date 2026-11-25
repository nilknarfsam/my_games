import * as THREE from 'three';
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js';
import { RoundedBoxGeometry } from 'three/examples/jsm/geometries/RoundedBoxGeometry.js';
import './style.css';
import { ChessEngine, chooseAIMove, FILES, RANKS } from './chess_engine.js';
import { createChessPieceMesh } from './piece_meshes.js';
import { ChessSound } from './sound.js';

const PIECE_UNICODE = {
  w: { k: '♔', q: '♕', r: '♖', b: '♗', n: '♘', p: '♙' },
  b: { k: '♚', q: '♛', r: '♜', b: '♝', n: '♞', p: '♟' },
};

const engine = new ChessEngine();
const sound = new ChessSound();

// State
let gameMode = 'ai-b'; // 'ai-b' (human white vs AI black), 'ai-w', 'pvp'
let aiDifficulty = 'medium';
let selectedSquare = null;
let legalMovesForSelected = [];
let pendingPromotion = null;
let aiTimeout = null;
let cameraSide = 'w';
let activeAnimation = null;

// --- DOM Elements ---
const canvasEl = document.getElementById('scene');
const turnDot = document.getElementById('turn-dot');
const turnText = document.getElementById('turn-text');
const statusText = document.getElementById('status-text');
const modeSelect = document.getElementById('mode-select');
const difficultyField = document.getElementById('difficulty-field');
const difficultySelect = document.getElementById('difficulty-select');
const capWhiteEl = document.getElementById('cap-white');
const capBlackEl = document.getElementById('cap-black');
const moveHistoryEl = document.getElementById('move-history');
const btnNew = document.getElementById('btn-new');
const btnUndo = document.getElementById('btn-undo');
const btnFlip = document.getElementById('btn-flip');
const btnMute = document.getElementById('btn-mute');
const promoModal = document.getElementById('promo-modal');
const gameOverModal = document.getElementById('gameover-modal');
const gameOverTitle = document.getElementById('gameover-title');
const gameOverSubtitle = document.getElementById('gameover-subtitle');
const btnGameOverNew = document.getElementById('btn-gameover-new');

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
controls.maxDistance = 20;
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

// --- Coordinate helpers ---
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
  // Pedestal floor
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

  // Wooden frame
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

  // 64 Squares
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

  // Coordinate labels on border
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

function rebuildPieceMeshes(skipTarget = null) {
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
      if (skipTarget && skipTarget.r === r && skipTarget.c === c) {
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

function updateBoardHighlights() {
  clearIndicators();

  const lastRecord = engine.moveLog[engine.moveLog.length - 1];
  const kingInCheck = engine.status === 'check' || engine.status === 'checkmate'
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
    const { x, z } = squareToWorld(move.toR, move.toC);
    const isCapture = Boolean(move.capture || move.isEnPassant);
    const geo = isCapture
      ? new THREE.RingGeometry(0.32, 0.44, 24)
      : new THREE.CircleGeometry(0.18, 24);
    const mat = new THREE.MeshBasicMaterial({
      color: isCapture ? 0xf43f5e : 0x38bdf8,
      transparent: true,
      opacity: 0.8,
      side: THREE.DoubleSide,
    });
    const marker = new THREE.Mesh(geo, mat);
    marker.rotation.x = -Math.PI / 2;
    marker.position.set(x, 0.052, z);
    marker.userData = { square: { r: move.toR, c: move.toC } };
    scene.add(marker);
    indicatorMeshes.push(marker);
  }
}

function updateHUD() {
  const isWhiteTurn = engine.turn === 'w';
  turnDot.className = `dot ${isWhiteTurn ? 'dot-white' : 'dot-black'}`;
  turnText.textContent = isWhiteTurn ? 'Brancas' : 'Pretas';

  statusText.className = 'status-sub';
  if (engine.status === 'checkmate') {
    statusText.textContent = `Xeque-Mate! Vitória das ${engine.winner === 'w' ? 'Brancas' : 'Pretas'}.`;
    statusText.classList.add('check');
  } else if (engine.status === 'stalemate') {
    statusText.textContent = 'Empate por afogamento.';
  } else if (engine.status === 'draw_insufficient') {
    statusText.textContent = 'Empate por material insuficiente.';
  } else if (engine.status === 'draw_50') {
    statusText.textContent = 'Empate pela regra dos 50 lances.';
  } else if (engine.status === 'check') {
    statusText.textContent = `XEQUE nas ${isWhiteTurn ? 'Brancas' : 'Pretas'}!`;
    statusText.classList.add('check');
  } else if (isAITurn()) {
    statusText.textContent = 'IA pensando no melhor lance...';
  } else {
    statusText.textContent = selectedSquare ? 'Escolha a casa de destino' : 'Selecione uma peça para jogar';
  }

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

  btnUndo.disabled = engine.history.length === 0 || Boolean(activeAnimation);
  btnMute.textContent = sound.muted ? 'Som: Mudo (M)' : 'Som: Ligado (M)';
  difficultyField.style.display = gameMode === 'pvp' ? 'none' : 'flex';

  const isGameOver = ['checkmate', 'stalemate', 'draw_50', 'draw_insufficient'].includes(
    engine.status,
  );
  if (isGameOver) {
    if (engine.status === 'checkmate') {
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
  if (side === 'w') {
    camera.position.set(0, 9.5, 10.5);
  } else {
    camera.position.set(0, 9.5, -10.5);
  }
  controls.target.set(0, 0.2, 0);
  controls.update();
}

function performMoveWithAnimation(fromR, fromC, toR, toC, promotion = 'q') {
  const movingMesh = boardPieceMeshes[fromR][fromC];
  const fromPos = squareToWorld(fromR, fromC);
  const toPos = squareToWorld(toR, toC);

  const record = engine.makeMove(fromR, fromC, toR, toC, promotion);
  if (!record) return false;

  selectedSquare = null;
  legalMovesForSelected = [];

  if (record.status === 'checkmate' || record.status === 'stalemate') {
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

  rebuildPieceMeshes({ r: toR, c: toC });
  updateBoardHighlights();
  updateHUD();

  if (movingMesh) {
    const animMesh = createChessPieceMesh(record.piece.type, record.piece.color);
    animMesh.position.set(fromPos.x, 0.04, fromPos.z);
    scene.add(animMesh);
    activeAnimation = {
      mesh: animMesh,
      startX: fromPos.x,
      startZ: fromPos.z,
      endX: toPos.x,
      endZ: toPos.z,
      progress: 0,
      duration: 0.22,
      targetSquare: { r: toR, c: toC },
    };
  } else {
    scheduleAIIfNeeded();
  }

  return true;
}

function scheduleAIIfNeeded() {
  clearTimeout(aiTimeout);
  if (
    !isAITurn() ||
    ['checkmate', 'stalemate', 'draw_50', 'draw_insufficient'].includes(engine.status)
  ) {
    return;
  }
  updateHUD();
  aiTimeout = setTimeout(() => {
    const move = chooseAIMove(engine, aiDifficulty);
    if (move) {
      performMoveWithAnimation(move.fromR, move.fromC, move.toR, move.toC, move.promotion ?? 'q');
    }
  }, 240);
}

// --- Mouse Raycasting (Distinguishes click vs OrbitControls drag) ---
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
  if (dist > 6) return; // User was orbiting camera
  if (activeAnimation || pendingPromotion || isAITurn()) return;

  const rect = canvasEl.getBoundingClientRect();
  pointer.x = ((e.clientX - rect.left) / rect.width) * 2 - 1;
  pointer.y = -((e.clientY - rect.top) / rect.height) * 2 + 1;

  raycaster.setFromCamera(pointer, camera);
  const targets = [
    ...indicatorMeshes,
    ...piecesGroup.children,
    ...squareMeshes.flat(),
  ];
  const hits = raycaster.intersectObjects(targets, true);
  if (hits.length === 0) {
    selectedSquare = null;
    legalMovesForSelected = [];
    updateBoardHighlights();
    updateHUD();
    return;
  }

  let sq = null;
  for (const hit of hits) {
    if (hit.object.userData?.square) {
      sq = hit.object.userData.square;
      break;
    }
  }
  if (!sq) return;

  handleSquareClick(sq.r, sq.c);
});

function handleSquareClick(r, c) {
  if (selectedSquare) {
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

function startNewGame() {
  clearTimeout(aiTimeout);
  if (activeAnimation) {
    scene.remove(activeAnimation.mesh);
    activeAnimation = null;
  }
  engine.reset();
  selectedSquare = null;
  legalMovesForSelected = [];
  pendingPromotion = null;
  promoModal.classList.add('hidden');
  setCameraSide(gameMode === 'ai-w' ? 'b' : 'w');
  rebuildPieceMeshes();
  updateBoardHighlights();
  updateHUD();
  scheduleAIIfNeeded();
}

function undoMove() {
  if (activeAnimation || engine.history.length === 0) return;
  clearTimeout(aiTimeout);
  if (gameMode !== 'pvp') {
    // Undo both AI reply and human move if possible
    engine.undo();
    if (isAITurn() && engine.history.length > 0) {
      engine.undo();
    }
  } else {
    engine.undo();
  }
  selectedSquare = null;
  legalMovesForSelected = [];
  rebuildPieceMeshes();
  updateBoardHighlights();
  updateHUD();
}

modeSelect.addEventListener('change', () => {
  gameMode = modeSelect.value;
  startNewGame();
});

difficultySelect.addEventListener('change', () => {
  aiDifficulty = difficultySelect.value;
});

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

window.addEventListener('keydown', (e) => {
  if (e.code === 'KeyU') undoMove();
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
});

// --- Main Render Loop ---
startNewGame();

let lastTime = performance.now();
function animate(now) {
  requestAnimationFrame(animate);
  const dtSec = Math.min(0.1, (now - lastTime) / 1000);
  lastTime = now;

  if (activeAnimation) {
    activeAnimation.progress += dtSec / activeAnimation.duration;
    const t = Math.min(1, activeAnimation.progress);
    const eased = 1 - Math.pow(1 - t, 3);
    activeAnimation.mesh.position.x =
      activeAnimation.startX + (activeAnimation.endX - activeAnimation.startX) * eased;
    activeAnimation.mesh.position.z =
      activeAnimation.startZ + (activeAnimation.endZ - activeAnimation.startZ) * eased;
    activeAnimation.mesh.position.y = 0.04 + Math.sin(t * Math.PI) * 0.45;

    if (t >= 1) {
      scene.remove(activeAnimation.mesh);
      const { r, c } = activeAnimation.targetSquare;
      if (boardPieceMeshes[r][c]) {
        boardPieceMeshes[r][c].visible = true;
      }
      activeAnimation = null;
      updateHUD();
      scheduleAIIfNeeded();
    }
  }

  controls.update();
  renderer.render(scene, camera);
}

requestAnimationFrame(animate);
