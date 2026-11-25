import * as THREE from 'three';
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js';
import { RoundedBoxGeometry } from 'three/examples/jsm/geometries/RoundedBoxGeometry.js';
import './style.css';
import { COLS, ROWS, TETROMINOS, PIECE_TYPES, TetrisEngine } from './tetris_engine.js';
import { SoundEngine } from './sound.js';

const HIGHSCORE_KEY = 'tetris_3d_highscore_v1';

const CAMERA_PRESETS = [
  { name: '3D Clássica', pos: [4.8, 2.4, 27.5], target: [0, -0.4, 0] },
  { name: 'Frontal', pos: [0, 0.2, 28.5], target: [0, -0.2, 0] },
  { name: 'Dinâmica', pos: [-8.5, 4.6, 25.0], target: [0, -0.5, 0] },
];

const engine = new TetrisEngine();
const sound = new SoundEngine();

let highScore = Number(localStorage.getItem(HIGHSCORE_KEY) || 0);
let cameraPresetIdx = 0;
let shakeIntensity = 0;
let toastTimer = null;

// --- DOM Elements ---
const canvasEl = document.getElementById('scene');
const scoreEl = document.getElementById('score');
const highScoreEl = document.getElementById('highscore');
const linesEl = document.getElementById('lines');
const levelEl = document.getElementById('level');
const nextCanvas = document.getElementById('next-canvas');
const holdCanvas = document.getElementById('hold-canvas');
const btnPause = document.getElementById('btn-pause');
const btnCamera = document.getElementById('btn-camera');
const btnMute = document.getElementById('btn-mute');
const btnRestart = document.getElementById('btn-restart');
const overlayEl = document.getElementById('overlay');
const overlayTitle = document.getElementById('overlay-title');
const overlaySubtitle = document.getElementById('overlay-subtitle');
const overlayBtn = document.getElementById('overlay-btn');
const toastEl = document.getElementById('toast');

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
renderer.toneMappingExposure = 1.15;

const scene = new THREE.Scene();
scene.background = new THREE.Color(0x070b14);
scene.fog = new THREE.FogExp2(0x070b14, 0.015);

const camera = new THREE.PerspectiveCamera(44, window.innerWidth / window.innerHeight, 0.1, 120);
camera.position.set(...CAMERA_PRESETS[0].pos);

const controls = new OrbitControls(camera, renderer.domElement);
controls.enableDamping = true;
controls.dampingFactor = 0.08;
controls.enablePan = false;
controls.minDistance = 17;
controls.maxDistance = 42;
controls.minPolarAngle = Math.PI * 0.22;
controls.maxPolarAngle = Math.PI * 0.68;
controls.minAzimuthAngle = -Math.PI * 0.35;
controls.maxAzimuthAngle = Math.PI * 0.35;
controls.target.set(...CAMERA_PRESETS[0].target);

// --- Lighting ---
const hemiLight = new THREE.HemisphereLight(0xdbeafe, 0x0f172a, 0.85);
scene.add(hemiLight);

const keyLight = new THREE.DirectionalLight(0xffffff, 1.8);
keyLight.position.set(10, 18, 22);
keyLight.castShadow = true;
keyLight.shadow.mapSize.set(1024, 1024);
keyLight.shadow.camera.near = 5;
keyLight.shadow.camera.far = 55;
keyLight.shadow.camera.left = -12;
keyLight.shadow.camera.right = 12;
keyLight.shadow.camera.top = 15;
keyLight.shadow.camera.bottom = -15;
scene.add(keyLight);

const cyanRim = new THREE.PointLight(0x38bdf8, 28, 35);
cyanRim.position.set(-10, 6, 8);
scene.add(cyanRim);

const purpleRim = new THREE.PointLight(0xa855f7, 24, 35);
purpleRim.position.set(11, -5, 10);
scene.add(purpleRim);

// --- Coordinate helpers ---
function gridToWorld(col, row) {
  const x = col - (COLS - 1) / 2;
  const y = (ROWS - 1 - row) - (ROWS - 1) / 2;
  return { x, y, z: 0 };
}

// --- 3D Board Frame & Stage ---
const boardGroup = new THREE.Group();
scene.add(boardGroup);

function buildStage() {
  // Pedestal floor
  const floorGeo = new THREE.PlaneGeometry(70, 70);
  const floorMat = new THREE.MeshStandardMaterial({
    color: 0x09101f,
    roughness: 0.7,
    metalness: 0.2,
  });
  const floor = new THREE.Mesh(floorGeo, floorMat);
  floor.rotation.x = -Math.PI / 2;
  floor.position.y = -ROWS / 2 - 0.85;
  floor.receiveShadow = true;
  scene.add(floor);

  // Glowing pedestal base directly under the well
  const baseGeo = new RoundedBoxGeometry(COLS + 1.4, 0.8, 2.8, 3, 0.12);
  const baseMat = new THREE.MeshStandardMaterial({
    color: 0x1e293b,
    roughness: 0.35,
    metalness: 0.65,
  });
  const baseMesh = new THREE.Mesh(baseGeo, baseMat);
  baseMesh.position.set(0, -ROWS / 2 - 0.42, 0);
  baseMesh.receiveShadow = true;
  baseMesh.castShadow = true;
  boardGroup.add(baseMesh);

  // Back plate (translucent smoked glass)
  const backGeo = new THREE.BoxGeometry(COLS + 0.16, ROWS + 0.16, 0.16);
  const backMat = new THREE.MeshStandardMaterial({
    color: 0x0b1222,
    roughness: 0.3,
    metalness: 0.35,
    transparent: true,
    opacity: 0.86,
  });
  const backMesh = new THREE.Mesh(backGeo, backMat);
  backMesh.position.set(0, 0, -0.62);
  backMesh.receiveShadow = true;
  boardGroup.add(backMesh);

  // Side rails
  const railGeo = new RoundedBoxGeometry(0.32, ROWS + 0.4, 1.3, 2, 0.08);
  const railMat = new THREE.MeshStandardMaterial({
    color: 0x334155,
    emissive: 0x0c4a6e,
    emissiveIntensity: 0.35,
    roughness: 0.28,
    metalness: 0.75,
  });

  const leftRail = new THREE.Mesh(railGeo, railMat);
  leftRail.position.set(-COLS / 2 - 0.22, 0, 0);
  leftRail.castShadow = true;
  boardGroup.add(leftRail);

  const rightRail = new THREE.Mesh(railGeo, railMat);
  rightRail.position.set(COLS / 2 + 0.22, 0, 0);
  rightRail.castShadow = true;
  boardGroup.add(rightRail);

  // Subtle internal 3D grid lines on the back wall
  const gridPoints = [];
  for (let c = 0; c <= COLS; c++) {
    const x = c - COLS / 2;
    gridPoints.push(new THREE.Vector3(x, -ROWS / 2, -0.52), new THREE.Vector3(x, ROWS / 2, -0.52));
  }
  for (let r = 0; r <= ROWS; r++) {
    const y = r - ROWS / 2;
    gridPoints.push(new THREE.Vector3(-COLS / 2, y, -0.52), new THREE.Vector3(COLS / 2, y, -0.52));
  }
  const gridGeo = new THREE.BufferGeometry().setFromPoints(gridPoints);
  const gridMat = new THREE.LineBasicMaterial({
    color: 0x38bdf8,
    transparent: true,
    opacity: 0.13,
  });
  boardGroup.add(new THREE.LineSegments(gridGeo, gridMat));
}

buildStage();

// --- Shared Block Geometries & Materials ---
const cubeGeometry = new RoundedBoxGeometry(0.92, 0.92, 0.92, 3, 0.1);
const cubeEdgeGeo = new THREE.EdgesGeometry(new THREE.BoxGeometry(0.93, 0.93, 0.93));
const particleGeo = new THREE.BoxGeometry(0.24, 0.24, 0.24);

const blockMaterials = {};
const ghostMaterials = {};
const edgeMaterials = {};

for (const type of PIECE_TYPES) {
  const color = TETROMINOS[type].color;
  blockMaterials[type] = new THREE.MeshStandardMaterial({
    color,
    emissive: color,
    emissiveIntensity: 0.14,
    roughness: 0.22,
    metalness: 0.2,
  });
  ghostMaterials[type] = new THREE.MeshBasicMaterial({
    color,
    transparent: true,
    opacity: 0.16,
    depthWrite: false,
  });
  edgeMaterials[type] = new THREE.LineBasicMaterial({
    color,
    transparent: true,
    opacity: 0.65,
  });
}

// Pre-allocated mesh pool for board cells + active piece + ghost piece
const lockedMeshes = Array.from({ length: ROWS }, () =>
  Array.from({ length: COLS }, () => {
    const mesh = new THREE.Mesh(cubeGeometry, blockMaterials.I);
    mesh.castShadow = true;
    mesh.receiveShadow = true;
    mesh.visible = false;
    boardGroup.add(mesh);
    return mesh;
  }),
);

const activeMeshes = Array.from({ length: 4 }, () => {
  const mesh = new THREE.Mesh(cubeGeometry, blockMaterials.I);
  mesh.castShadow = true;
  mesh.receiveShadow = true;
  mesh.visible = false;
  boardGroup.add(mesh);
  return mesh;
});

const ghostMeshes = Array.from({ length: 4 }, () => {
  const mesh = new THREE.Mesh(cubeGeometry, ghostMaterials.I);
  const edges = new THREE.LineSegments(cubeEdgeGeo, edgeMaterials.I);
  mesh.add(edges);
  mesh.visible = false;
  boardGroup.add(mesh);
  return { mesh, edges };
});

// --- 3D Line-Clear Particles ---
const particles = [];

function spawnLineParticles(clearedSnapshot) {
  for (const rowInfo of clearedSnapshot) {
    rowInfo.cells.forEach((type, col) => {
      if (!type) return;
      const { x, y } = gridToWorld(col, rowInfo.row);
      const color = TETROMINOS[type].color;
      for (let i = 0; i < 3; i++) {
        const mat = new THREE.MeshBasicMaterial({
          color,
          transparent: true,
          opacity: 1,
        });
        const p = new THREE.Mesh(particleGeo, mat);
        p.position.set(
          x + (Math.random() - 0.5) * 0.5,
          y + (Math.random() - 0.5) * 0.5,
          (Math.random() - 0.5) * 0.5,
        );
        boardGroup.add(p);
        particles.push({
          mesh: p,
          vx: (Math.random() - 0.5) * 7,
          vy: Math.random() * 4 + 1.5,
          vz: (Math.random() - 0.5) * 7 + 1.5,
          rx: (Math.random() - 0.5) * 10,
          ry: (Math.random() - 0.5) * 10,
          life: 0.75 + Math.random() * 0.25,
          maxLife: 1.0,
        });
      }
    });
  }
}

function updateParticles(dtSec) {
  for (let i = particles.length - 1; i >= 0; i--) {
    const p = particles[i];
    p.life -= dtSec;
    if (p.life <= 0) {
      boardGroup.remove(p.mesh);
      p.mesh.material.dispose();
      particles.splice(i, 1);
      continue;
    }
    p.vy -= 14 * dtSec;
    p.mesh.position.x += p.vx * dtSec;
    p.mesh.position.y += p.vy * dtSec;
    p.mesh.position.z += p.vz * dtSec;
    p.mesh.rotation.x += p.rx * dtSec;
    p.mesh.rotation.y += p.ry * dtSec;
    const ratio = p.life / p.maxLife;
    p.mesh.scale.setScalar(Math.max(0.1, ratio));
    p.mesh.material.opacity = ratio;
  }
}

// --- HUD & 2D Mini-Previews ---
function drawMiniPiece(canvas, type) {
  const ctx = canvas.getContext('2d');
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  if (!type) return;

  const { matrix, css } = TETROMINOS[type];
  let minR = matrix.length,
    maxR = -1,
    minC = matrix[0].length,
    maxC = -1;

  for (let r = 0; r < matrix.length; r++) {
    for (let c = 0; c < matrix[r].length; c++) {
      if (matrix[r][c]) {
        minR = Math.min(minR, r);
        maxR = Math.max(maxR, r);
        minC = Math.min(minC, c);
        maxC = Math.max(maxC, c);
      }
    }
  }

  const pieceW = maxC - minC + 1;
  const pieceH = maxR - minR + 1;
  const cell = 18;
  const offsetX = (canvas.width - pieceW * cell) / 2;
  const offsetY = (canvas.height - pieceH * cell) / 2;

  for (let r = minR; r <= maxR; r++) {
    for (let c = minC; c <= maxC; c++) {
      if (!matrix[r][c]) continue;
      const px = offsetX + (c - minC) * cell;
      const py = offsetY + (r - minR) * cell;
      ctx.fillStyle = css;
      ctx.beginPath();
      ctx.roundRect(px + 1, py + 1, cell - 2, cell - 2, 4);
      ctx.fill();

      ctx.fillStyle = 'rgba(255,255,255,0.28)';
      ctx.fillRect(px + 3, py + 3, cell - 6, 3);
    }
  }
}

function showToast(message) {
  toastEl.textContent = message;
  toastEl.classList.remove('hidden');
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => {
    toastEl.classList.add('hidden');
  }, 1400);
}

function syncHUD() {
  if (engine.score > highScore) {
    highScore = engine.score;
    localStorage.setItem(HIGHSCORE_KEY, String(highScore));
  }
  scoreEl.textContent = engine.score.toLocaleString('pt-BR');
  highScoreEl.textContent = highScore.toLocaleString('pt-BR');
  linesEl.textContent = String(engine.lines);
  levelEl.textContent = String(engine.level);

  drawMiniPiece(nextCanvas, engine.nextType);
  drawMiniPiece(holdCanvas, engine.holdType);

  btnPause.textContent = engine.paused ? 'Continuar (P)' : 'Pausar (P)';
  btnMute.textContent = sound.muted ? 'Som: Mudo (M)' : 'Som: Ligado (M)';
  btnCamera.textContent = `Câmera: ${CAMERA_PRESETS[cameraPresetIdx].name} (C)`;

  if (engine.gameOver) {
    overlayTitle.textContent = 'Fim de Jogo';
    overlaySubtitle.textContent = `Pontuação final: ${engine.score.toLocaleString('pt-BR')} pontos`;
    overlayBtn.textContent = 'Jogar Novamente';
    overlayEl.classList.remove('hidden');
  } else if (engine.paused) {
    overlayTitle.textContent = 'Pausado';
    overlaySubtitle.textContent = 'Pressione P para voltar ao jogo';
    overlayBtn.textContent = 'Continuar';
    overlayEl.classList.remove('hidden');
  } else {
    overlayEl.classList.add('hidden');
  }
}

function syncSceneFromEngine() {
  for (let r = 0; r < ROWS; r++) {
    for (let c = 0; c < COLS; c++) {
      const cell = engine.board[r][c];
      const mesh = lockedMeshes[r][c];
      if (cell) {
        const { x, y, z } = gridToWorld(c, r);
        mesh.position.set(x, y, z);
        mesh.material = blockMaterials[cell];
        mesh.visible = true;
      } else {
        mesh.visible = false;
      }
    }
  }

  activeMeshes.forEach((m) => (m.visible = false));
  ghostMeshes.forEach((g) => (g.mesh.visible = false));

  if (engine.activePiece && !engine.gameOver) {
    const { type, matrix, x: px, y: py } = engine.activePiece;
    const ghostY = engine.getGhostY();
    let idx = 0;

    for (let r = 0; r < matrix.length; r++) {
      for (let c = 0; c < matrix[r].length; c++) {
        if (!matrix[r][c]) continue;
        if (idx >= 4) break;

        const worldPos = gridToWorld(px + c, py + r);
        const activeMesh = activeMeshes[idx];
        activeMesh.position.set(worldPos.x, worldPos.y, worldPos.z);
        activeMesh.material = blockMaterials[type];
        activeMesh.visible = true;

        const ghostPos = gridToWorld(px + c, ghostY + r);
        const ghostEntry = ghostMeshes[idx];
        ghostEntry.mesh.position.set(ghostPos.x, ghostPos.y, ghostPos.z);
        ghostEntry.mesh.material = ghostMaterials[type];
        ghostEntry.edges.material = edgeMaterials[type];
        ghostEntry.mesh.visible = ghostY !== py;

        idx++;
      }
    }
  }
}

// --- Feedback Handler ---
function handleStepEvents(result) {
  if (!result) return;
  if (result.clearedRows && result.clearedRows.length > 0) {
    spawnLineParticles(result.clearedSnapshot);
    sound.clear(result.clearedRows.length);
    const labels = {
      1: 'Linha +1!',
      2: 'Dupla!',
      3: 'Tripla!',
      4: 'TETRIS 3D!',
    };
    showToast(labels[result.clearedRows.length] || `${result.clearedRows.length} Linhas!`);
    if (result.clearedRows.length === 4) {
      shakeIntensity = Math.max(shakeIntensity, 0.25);
    }
  }
  if (result.levelUp) {
    sound.levelUp();
    showToast(`Nível ${engine.level}!`);
  }
  if (result.gameOver) {
    sound.gameOver();
  }
}

// --- Camera & Controls ---
function cycleCameraPreset() {
  cameraPresetIdx = (cameraPresetIdx + 1) % CAMERA_PRESETS.length;
  const preset = CAMERA_PRESETS[cameraPresetIdx];
  camera.position.set(...preset.pos);
  controls.target.set(...preset.target);
  controls.update();
  syncHUD();
  showToast(`Câmera: ${preset.name}`);
}

function restartGame() {
  engine.reset();
  syncSceneFromEngine();
  syncHUD();
  showToast('Novo Jogo');
}

btnPause.addEventListener('click', () => {
  engine.togglePause();
  syncHUD();
});
btnCamera.addEventListener('click', cycleCameraPreset);
btnMute.addEventListener('click', () => {
  sound.toggleMute();
  syncHUD();
});
btnRestart.addEventListener('click', restartGame);
overlayBtn.addEventListener('click', () => {
  if (engine.gameOver) {
    restartGame();
  } else {
    engine.togglePause();
    syncHUD();
  }
});

// Keyboard handling with smooth horizontal DAS/ARR repeat
const heldHorizontal = { left: false, right: false, dir: 0, timerMs: 0 };
const DAS_MS = 160;
const ARR_MS = 48;

window.addEventListener('keydown', (e) => {
  const code = e.code;

  if (['ArrowLeft', 'ArrowRight', 'ArrowUp', 'ArrowDown', 'Space'].includes(code)) {
    e.preventDefault();
  }

  if (code === 'KeyP') {
    engine.togglePause();
    syncHUD();
    return;
  }
  if (code === 'KeyR') {
    restartGame();
    return;
  }
  if (code === 'KeyM') {
    sound.toggleMute();
    syncHUD();
    return;
  }
  if (code === 'KeyC') {
    cycleCameraPreset();
    return;
  }

  if (engine.paused || engine.gameOver) return;

  if (code === 'ArrowLeft' || code === 'KeyA') {
    if (!e.repeat) {
      if (engine.moveLeft()) sound.move();
      heldHorizontal.left = true;
      heldHorizontal.dir = -1;
      heldHorizontal.timerMs = -DAS_MS;
    }
  } else if (code === 'ArrowRight' || code === 'KeyD') {
    if (!e.repeat) {
      if (engine.moveRight()) sound.move();
      heldHorizontal.right = true;
      heldHorizontal.dir = 1;
      heldHorizontal.timerMs = -DAS_MS;
    }
  } else if (code === 'ArrowUp' || code === 'KeyW' || code === 'KeyX') {
    if (engine.rotate(true)) sound.rotate();
  } else if (code === 'KeyZ') {
    if (engine.rotate(false)) sound.rotate();
  } else if (code === 'ArrowDown' || code === 'KeyS') {
    const res = engine.softDrop();
    if (res.moved) sound.softDrop();
    handleStepEvents(res);
  } else if (code === 'Space') {
    if (!e.repeat) {
      const res = engine.hardDrop();
      sound.hardDrop();
      shakeIntensity = Math.max(shakeIntensity, 0.1);
      handleStepEvents(res);
    }
  } else if (code === 'ShiftLeft' || code === 'ShiftRight' || code === 'KeyE') {
    if (!e.repeat && engine.holdPiece()) {
      sound.hold();
    }
  }

  syncSceneFromEngine();
  syncHUD();
});

window.addEventListener('keyup', (e) => {
  if (e.code === 'ArrowLeft' || e.code === 'KeyA') {
    heldHorizontal.left = false;
    heldHorizontal.dir = heldHorizontal.right ? 1 : 0;
  } else if (e.code === 'ArrowRight' || e.code === 'KeyD') {
    heldHorizontal.right = false;
    heldHorizontal.dir = heldHorizontal.left ? -1 : 0;
  }
});

window.addEventListener('resize', () => {
  camera.aspect = window.innerWidth / window.innerHeight;
  camera.updateProjectionMatrix();
  renderer.setSize(window.innerWidth, window.innerHeight);
});

// --- Main Loop ---
let lastTime = performance.now();
syncSceneFromEngine();
syncHUD();

function animate(now) {
  requestAnimationFrame(animate);
  const dtMs = Math.min(100, now - lastTime);
  const dtSec = dtMs / 1000;
  lastTime = now;

  if (!engine.paused && !engine.gameOver) {
    if (heldHorizontal.dir !== 0) {
      heldHorizontal.timerMs += dtMs;
      while (heldHorizontal.timerMs >= ARR_MS) {
        heldHorizontal.timerMs -= ARR_MS;
        const moved = heldHorizontal.dir < 0 ? engine.moveLeft() : engine.moveRight();
        if (moved) sound.move();
      }
    }

    const stepResult = engine.step(dtMs);
    handleStepEvents(stepResult);
    syncSceneFromEngine();
    syncHUD();
  }

  updateParticles(dtSec);

  if (shakeIntensity > 0.001) {
    boardGroup.position.x = (Math.random() - 0.5) * shakeIntensity;
    boardGroup.position.y = (Math.random() - 0.5) * shakeIntensity;
    shakeIntensity *= 0.84;
  } else {
    boardGroup.position.set(0, 0, 0);
    shakeIntensity = 0;
  }

  controls.update();
  renderer.render(scene, camera);
}

requestAnimationFrame(animate);
