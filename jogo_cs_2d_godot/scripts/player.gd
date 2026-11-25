extends CharacterBody2D
## Jogador autoritativo no servidor; o cliente dono envia apenas WASD, mira, tiro e recarga.

signal eliminated(player_id: int, killer_id: int)
signal fire_requested(shooter_id: int, spawn_pos: Vector2, angle: float, damage: int, from_bot: bool)

const MOVE_SPEED: float = 225.0
const MAX_HP: int = 100
const MAGAZINE_SIZE: int = 15
const FIRE_COOLDOWN_SEC: float = 0.16
const RELOAD_SEC: float = 1.25

@export var entity_id: int = 1
@export var player_name: String = "Jogador"
@export var aim_angle: float = 0.0
@export var hp: int = MAX_HP
@export var ammo: int = MAGAZINE_SIZE
@export var is_reloading: bool = false
@export var reload_progress: float = 0.0
@export var alive: bool = true
@export var team_color: Color = Color(0.22, 0.74, 0.97)

var _input_move: Vector2 = Vector2.ZERO
var _input_aim: float = 0.0
var _input_firing: bool = false
var _fire_cd: float = 0.0
var _reload_timer: float = 0.0

var _rig: Node2D
var _hp_fill: Polygon2D
var _reload_fill: Polygon2D
var _reload_bg: Polygon2D
var _name_label: Label
var _vision_light: PointLight2D


func _ready() -> void:
	_build_visual()
	if is_local_player():
		_setup_vision_light()
	_update_visuals()


func is_local_player() -> bool:
	return entity_id == multiplayer.get_unique_id()


func reset_at(spawn_pos: Vector2) -> void:
	position = spawn_pos
	hp = MAX_HP
	ammo = MAGAZINE_SIZE
	is_reloading = false
	reload_progress = 0.0
	alive = true
	_fire_cd = 0.0
	_reload_timer = 0.0
	visible = true
	$CollisionShape2D.set_deferred("disabled", false)


func apply_damage(amount: int, attacker_id: int) -> void:
	if not multiplayer.is_server() or not alive:
		return
	hp = max(0, hp - amount)
	if hp == 0:
		alive = false
		$CollisionShape2D.set_deferred("disabled", true)
		eliminated.emit(entity_id, attacker_id)


func _physics_process(delta: float) -> void:
	if is_local_player() and alive:
		var move_dir := Vector2(
			Input.get_axis("move_left", "move_right"),
			Input.get_axis("move_up", "move_down")
		)
		if move_dir.length() > 1.0:
			move_dir = move_dir.normalized()

		var mouse_pos := get_global_mouse_position()
		var local_aim := (mouse_pos - global_position).angle()
		var firing := Input.is_action_pressed("shoot")
		_submit_input.rpc_id(1, move_dir, local_aim, firing)

		if Input.is_action_just_pressed("reload"):
			_request_reload.rpc_id(1)

	if multiplayer.is_server() and alive:
		_process_server_turn(delta)

	_update_visuals()


func _process_server_turn(delta: float) -> void:
	aim_angle = _input_aim
	velocity = _input_move * MOVE_SPEED
	move_and_slide()

	if _fire_cd > 0.0:
		_fire_cd = max(0.0, _fire_cd - delta)

	if _reload_timer > 0.0:
		_reload_timer = max(0.0, _reload_timer - delta)
		is_reloading = _reload_timer > 0.0
		reload_progress = 1.0 - (_reload_timer / RELOAD_SEC)
		if _reload_timer == 0.0:
			ammo = MAGAZINE_SIZE
			reload_progress = 0.0

	if _input_firing and not is_reloading and _fire_cd <= 0.0 and ammo > 0:
		ammo -= 1
		_fire_cd = FIRE_COOLDOWN_SEC
		var muzzle := global_position + Vector2.RIGHT.rotated(aim_angle) * 24.0
		fire_requested.emit(entity_id, muzzle, aim_angle, 34, false)


@rpc("any_peer", "call_local", "unreliable_ordered")
func _submit_input(move_dir: Vector2, new_aim: float, firing: bool) -> void:
	if not multiplayer.is_server():
		return
	var sender := multiplayer.get_remote_sender_id()
	if sender != 0 and sender != entity_id:
		return
	_input_move = move_dir.limit_length(1.0)
	_input_aim = new_aim
	_input_firing = firing


@rpc("any_peer", "call_local", "reliable")
func _request_reload() -> void:
	if not multiplayer.is_server() or not alive:
		return
	var sender := multiplayer.get_remote_sender_id()
	if sender != 0 and sender != entity_id:
		return
	if is_reloading or ammo >= MAGAZINE_SIZE:
		return
	is_reloading = true
	_reload_timer = RELOAD_SEC
	reload_progress = 0.0


func _build_visual() -> void:
	_rig = Node2D.new()
	add_child(_rig)

	var barrel := Polygon2D.new()
	barrel.polygon = PackedVector2Array([
		Vector2(0, -3), Vector2(26, -3), Vector2(26, 3), Vector2(0, 3)
	])
	barrel.color = Color(0.82, 0.86, 0.90)
	_rig.add_child(barrel)

	var body_poly := Polygon2D.new()
	body_poly.polygon = _circle_pts(15.0, 16)
	body_poly.color = team_color.darkened(0.45)
	_rig.add_child(body_poly)

	var helmet := Polygon2D.new()
	helmet.polygon = _circle_pts(9.5, 14)
	helmet.color = team_color
	_rig.add_child(helmet)

	var hp_bg := Polygon2D.new()
	hp_bg.polygon = PackedVector2Array([
		Vector2(-16, -26), Vector2(16, -26), Vector2(16, -22), Vector2(-16, -22)
	])
	hp_bg.color = Color(0.06, 0.09, 0.16)
	add_child(hp_bg)

	_hp_fill = Polygon2D.new()
	_hp_fill.polygon = PackedVector2Array([
		Vector2(-16, -26), Vector2(16, -26), Vector2(16, -22), Vector2(-16, -22)
	])
	_hp_fill.color = Color(0.06, 0.72, 0.51)
	add_child(_hp_fill)

	_reload_bg = Polygon2D.new()
	_reload_bg.polygon = PackedVector2Array([
		Vector2(-16, -32), Vector2(16, -32), Vector2(16, -28), Vector2(-16, -28)
	])
	_reload_bg.color = Color(0.06, 0.09, 0.16)
	_reload_bg.visible = false
	add_child(_reload_bg)

	_reload_fill = Polygon2D.new()
	_reload_fill.polygon = PackedVector2Array([
		Vector2(-16, -32), Vector2(16, -32), Vector2(16, -28), Vector2(-16, -28)
	])
	_reload_fill.color = Color(0.98, 0.80, 0.08)
	_reload_fill.visible = false
	add_child(_reload_fill)

	_name_label = Label.new()
	_name_label.text = player_name
	_name_label.position = Vector2(-42, 18)
	_name_label.size = Vector2(84, 18)
	_name_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_name_label.add_theme_font_size_override("font_size", 11)
	add_child(_name_label)


func _setup_vision_light() -> void:
	# Textura procedural radial para luz 2D com sombras reais nas paredes
	var img := Image.create(256, 256, false, Image.FORMAT_RGBA8)
	var center := Vector2(128, 128)
	for y in range(256):
		for x in range(256):
			var dist := Vector2(x, y).distance_to(center) / 128.0
			var alpha := clampf(1.0 - dist, 0.0, 1.0)
			alpha = alpha * alpha
			img.set_pixel(x, y, Color(1.0, 1.0, 1.0, alpha))

	var tex := ImageTexture.create_from_image(img)
	_vision_light = PointLight2D.new()
	_vision_light.texture = tex
	_vision_light.texture_scale = 3.2
	_vision_light.energy = 1.1
	_vision_light.shadow_enabled = true
	_vision_light.shadow_color = Color(0, 0, 0, 0.75)
	add_child(_vision_light)


func _update_visuals() -> void:
	visible = alive
	if _rig != null:
		_rig.rotation = aim_angle
	if _name_label != null:
		_name_label.text = player_name
	if _hp_fill != null:
		var ratio := clampf(float(hp) / float(MAX_HP), 0.0, 1.0)
		_hp_fill.scale.x = ratio
	if _reload_bg != null and _reload_fill != null:
		_reload_bg.visible = is_reloading
		_reload_fill.visible = is_reloading
		_reload_fill.scale.x = clampf(reload_progress, 0.0, 1.0)


static func _circle_pts(radius: float, segments: int) -> PackedVector2Array:
	var pts := PackedVector2Array()
	for i in range(segments):
		var a := TAU * float(i) / float(segments)
		pts.append(Vector2(cos(a), sin(a)) * radius)
	return pts
