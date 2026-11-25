import * as THREE from 'three';

function createLathe(points, segments = 24) {
  const vecs = points.map(([x, y]) => new THREE.Vector2(x, y));
  return new THREE.LatheGeometry(vecs, segments);
}

const WHITE_MAT = new THREE.MeshStandardMaterial({
  color: 0xf4eee4,
  roughness: 0.28,
  metalness: 0.08,
});

const BLACK_MAT = new THREE.MeshStandardMaterial({
  color: 0x262f42,
  roughness: 0.25,
  metalness: 0.24,
});

function createPawnMesh(mat) {
  const group = new THREE.Group();
  const bodyGeo = createLathe([
    [0.0, 0.0],
    [0.34, 0.0],
    [0.34, 0.08],
    [0.27, 0.14],
    [0.22, 0.22],
    [0.14, 0.45],
    [0.11, 0.62],
    [0.19, 0.66],
    [0.12, 0.7],
    [0.0, 0.7],
  ]);
  const body = new THREE.Mesh(bodyGeo, mat);
  body.castShadow = true;
  body.receiveShadow = true;
  group.add(body);

  const head = new THREE.Mesh(new THREE.SphereGeometry(0.18, 20, 16), mat);
  head.position.y = 0.86;
  head.castShadow = true;
  head.receiveShadow = true;
  group.add(head);

  return group;
}

function createRookMesh(mat) {
  const group = new THREE.Group();
  const bodyGeo = createLathe([
    [0.0, 0.0],
    [0.38, 0.0],
    [0.38, 0.1],
    [0.3, 0.18],
    [0.24, 0.25],
    [0.2, 0.72],
    [0.28, 0.8],
    [0.28, 0.96],
    [0.2, 0.96],
    [0.2, 0.88],
    [0.0, 0.88],
  ]);
  const body = new THREE.Mesh(bodyGeo, mat);
  body.castShadow = true;
  body.receiveShadow = true;
  group.add(body);

  // 4 crenellations on top
  const merlonGeo = new THREE.BoxGeometry(0.14, 0.14, 0.14);
  for (let i = 0; i < 4; i++) {
    const angle = (i * Math.PI) / 2 + Math.PI / 4;
    const m = new THREE.Mesh(merlonGeo, mat);
    m.position.set(Math.cos(angle) * 0.21, 1.03, Math.sin(angle) * 0.21);
    m.rotation.y = -angle;
    m.castShadow = true;
    group.add(m);
  }
  return group;
}

function createKnightMesh(mat, color) {
  const group = new THREE.Group();
  const baseGeo = createLathe([
    [0.0, 0.0],
    [0.38, 0.0],
    [0.38, 0.1],
    [0.29, 0.18],
    [0.25, 0.28],
    [0.0, 0.28],
  ]);
  const base = new THREE.Mesh(baseGeo, mat);
  base.castShadow = true;
  base.receiveShadow = true;
  group.add(base);

  const shape = new THREE.Shape();
  shape.moveTo(-0.18, 0.26);
  shape.lineTo(0.2, 0.26);
  shape.quadraticCurveTo(0.24, 0.56, 0.1, 0.82);
  shape.lineTo(0.18, 0.96);
  shape.lineTo(0.06, 1.12);
  shape.lineTo(-0.02, 1.02);
  shape.lineTo(-0.24, 0.92);
  shape.quadraticCurveTo(-0.3, 0.82, -0.2, 0.74);
  shape.lineTo(-0.04, 0.72);
  shape.quadraticCurveTo(-0.14, 0.5, -0.18, 0.26);

  const extrudeGeo = new THREE.ExtrudeGeometry(shape, {
    depth: 0.22,
    bevelEnabled: true,
    bevelSegments: 3,
    steps: 1,
    bevelSize: 0.04,
    bevelThickness: 0.04,
  });
  extrudeGeo.center();

  const horse = new THREE.Mesh(extrudeGeo, mat);
  horse.position.y = 0.7;
  // Face toward the opponent: white faces -Z, black faces +Z
  horse.rotation.y = color === 'w' ? -Math.PI / 2 : Math.PI / 2;
  horse.castShadow = true;
  horse.receiveShadow = true;
  group.add(horse);

  return group;
}

function createBishopMesh(mat) {
  const group = new THREE.Group();
  const bodyGeo = createLathe([
    [0.0, 0.0],
    [0.38, 0.0],
    [0.38, 0.1],
    [0.29, 0.17],
    [0.22, 0.26],
    [0.15, 0.65],
    [0.22, 0.71],
    [0.14, 0.76],
    [0.2, 0.96],
    [0.12, 1.14],
    [0.0, 1.2],
  ]);
  const body = new THREE.Mesh(bodyGeo, mat);
  body.castShadow = true;
  body.receiveShadow = true;
  group.add(body);

  const finial = new THREE.Mesh(new THREE.SphereGeometry(0.075, 16, 12), mat);
  finial.position.y = 1.25;
  finial.castShadow = true;
  group.add(finial);

  return group;
}

function createQueenMesh(mat) {
  const group = new THREE.Group();
  const bodyGeo = createLathe([
    [0.0, 0.0],
    [0.41, 0.0],
    [0.41, 0.1],
    [0.32, 0.18],
    [0.24, 0.28],
    [0.16, 0.8],
    [0.25, 0.87],
    [0.17, 0.93],
    [0.26, 1.16],
    [0.18, 1.22],
    [0.0, 1.26],
  ]);
  const body = new THREE.Mesh(bodyGeo, mat);
  body.castShadow = true;
  body.receiveShadow = true;
  group.add(body);

  const crownBallGeo = new THREE.SphereGeometry(0.055, 12, 10);
  for (let i = 0; i < 6; i++) {
    const angle = (i * Math.PI * 2) / 6;
    const tip = new THREE.Mesh(crownBallGeo, mat);
    tip.position.set(Math.cos(angle) * 0.21, 1.23, Math.sin(angle) * 0.21);
    tip.castShadow = true;
    group.add(tip);
  }

  const topGem = new THREE.Mesh(new THREE.SphereGeometry(0.085, 16, 12), mat);
  topGem.position.y = 1.33;
  topGem.castShadow = true;
  group.add(topGem);

  return group;
}

function createKingMesh(mat) {
  const group = new THREE.Group();
  const bodyGeo = createLathe([
    [0.0, 0.0],
    [0.42, 0.0],
    [0.42, 0.11],
    [0.33, 0.19],
    [0.25, 0.3],
    [0.17, 0.88],
    [0.27, 0.96],
    [0.18, 1.02],
    [0.25, 1.25],
    [0.0, 1.3],
  ]);
  const body = new THREE.Mesh(bodyGeo, mat);
  body.castShadow = true;
  body.receiveShadow = true;
  group.add(body);

  // Cross on top
  const vBar = new THREE.Mesh(new THREE.BoxGeometry(0.08, 0.28, 0.08), mat);
  vBar.position.y = 1.44;
  vBar.castShadow = true;
  group.add(vBar);

  const hBar = new THREE.Mesh(new THREE.BoxGeometry(0.22, 0.08, 0.08), mat);
  hBar.position.y = 1.48;
  hBar.castShadow = true;
  group.add(hBar);

  return group;
}

export function createChessPieceMesh(type, color) {
  const mat = color === 'w' ? WHITE_MAT : BLACK_MAT;
  switch (type) {
    case 'p':
      return createPawnMesh(mat);
    case 'r':
      return createRookMesh(mat);
    case 'n':
      return createKnightMesh(mat, color);
    case 'b':
      return createBishopMesh(mat);
    case 'q':
      return createQueenMesh(mat);
    case 'k':
      return createKingMesh(mat);
    default:
      return createPawnMesh(mat);
  }
}
