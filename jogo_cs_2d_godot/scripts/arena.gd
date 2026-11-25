extends Node2D
## Arena tática pequena com paredes, caixas de cobertura e oclusores de luz 2D.

const MAP_WIDTH: float = 840.0
const MAP_HEIGHT: float = 580.0
const WALL_THICKNESS: float = 20.0

const OBSTACLE_SPECS: Array[Dictionary] = [
	# Paredes externas
	{"rect": Rect2(0, 0, MAP_WIDTH, WALL_THICKNESS), "kind": "wall"},
	{"rect": Rect2(0, MAP_HEIGHT - WALL_THICKNESS, MAP_WIDTH, WALL_THICKNESS), "kind": "wall"},
	{"rect": Rect2(0, 0, WALL_THICKNESS, MAP_HEIGHT), "kind": "wall"},
	{"rect": Rect2(MAP_WIDTH - WALL_THICKNESS, 0, WALL_THICKNESS, MAP_HEIGHT), "kind": "wall"},
	# Caixas centrais
	{"rect": Rect2(365, 240, 110, 100), "kind": "crate"},
	# Muros laterais
	{"rect": Rect2(160, 150, 110, 34), "kind": "wall"},
	{"rect": Rect2(160, 396, 110, 34), "kind": "wall"},
	{"rect": Rect2(570, 150, 110, 34), "kind": "wall"},
	{"rect": Rect2(570, 396, 110, 34), "kind": "wall"},
	# Caixas de cobertura nos flancos
	{"rect": Rect2(275, 105, 48, 48), "kind": "crate"},
	{"rect": Rect2(517, 427, 48, 48), "kind": "crate"},
]

const PLAYER_SPAWNS: Array[Vector2] = [
	Vector2(90, 490),
	Vector2(750, 90),
	Vector2(90, 90),
	Vector2(750, 490),
]

const BOT_SPAWNS: Array[Vector2] = [
	Vector2(740, 95),
	Vector2(720, 485),
]


func _ready() -> void:
	_build_floor()
	_build_obstacles()


func _build_floor() -> void:
	var floor_poly := Polygon2D.new()
	floor_poly.polygon = PackedVector2Array([
		Vector2(0, 0),
		Vector2(MAP_WIDTH, 0),
		Vector2(MAP_WIDTH, MAP_HEIGHT),
		Vector2(0, MAP_HEIGHT),
	])
	floor_poly.color = Color(0.10, 0.14, 0.20)
	floor_poly.z_index = -10
	add_child(floor_poly)

	for gx in range(42, int(MAP_WIDTH), 42):
		var line := Line2D.new()
		line.points = PackedVector2Array([Vector2(gx, 0), Vector2(gx, MAP_HEIGHT)])
		line.width = 1.0
		line.default_color = Color(0.14, 0.19, 0.27)
		line.z_index = -9
		add_child(line)

	for gy in range(42, int(MAP_HEIGHT), 42):
		var line := Line2D.new()
		line.points = PackedVector2Array([Vector2(0, gy), Vector2(MAP_WIDTH, gy)])
		line.width = 1.0
		line.default_color = Color(0.14, 0.19, 0.27)
		line.z_index = -9
		add_child(line)


func _build_obstacles() -> void:
	for spec in OBSTACLE_SPECS:
		var rect: Rect2 = spec["rect"]
		var kind: String = spec["kind"]

		var body := StaticBody2D.new()
		body.collision_layer = 1
		body.collision_mask = 0
		body.position = rect.position + rect.size * 0.5

		var shape := CollisionShape2D.new()
		var box := RectangleShape2D.new()
		box.size = rect.size
		shape.shape = box
		body.add_child(shape)

		var half := rect.size * 0.5
		var poly_pts := PackedVector2Array([
			Vector2(-half.x, -half.y),
			Vector2(half.x, -half.y),
			Vector2(half.x, half.y),
			Vector2(-half.x, half.y),
		])

		var poly := Polygon2D.new()
		poly.polygon = poly_pts
		poly.color = Color(0.28, 0.33, 0.41) if kind == "wall" else Color(0.57, 0.25, 0.05)
		body.add_child(poly)

		var border := Line2D.new()
		border.points = PackedVector2Array([
			poly_pts[0], poly_pts[1], poly_pts[2], poly_pts[3], poly_pts[0]
		])
		border.width = 2.0
		border.default_color = Color(0.39, 0.45, 0.55) if kind == "wall" else Color(0.85, 0.47, 0.02)
		body.add_child(border)

		# Oclusor 2D para sombras reais da lanterna/visão do jogador
		var occluder := LightOccluder2D.new()
		var occ_poly := OccluderPolygon2D.new()
		occ_poly.polygon = poly_pts
		occluder.occluder = occ_poly
		body.add_child(occluder)

		add_child(body)
