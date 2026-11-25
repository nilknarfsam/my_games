extends CharacterBody2D
## Bot oponente controlado pelo servidor com linha de visão real via raycast.

signal eliminated(bot_id: int, killer_id: int)
signal fire_requested(shooter_id: int, spawn_pos: Vector2, angle: float, damage: int, from_bot: bool)

const MOVE_SPEED: float = 145.0
const MAX_HP: int = 100
const FIRE_COOLDOWN_SEC: float = 0.52
const MAGAZINE_SIZE: int = 10
const RELOAD_SEC: float = 1.4

@export var entity_id: int = -1
@export var aim_angle: float = PI
@export var hp: int = MAX_HP
@export var alive: bool = true

var _ammo: int = MAGAZINE_SIZE
var _fire_cd: float = 0.6
var _reload_timer: float = 0.0
var _strafe_dir: float = 1.0
var _strafe_timer: float = 1.0
var _patrol_target: Vector2 = Vector2(420, 290)
var _rng := RandomNumberGenerator.new()

var _rig: Node2D
var _hp_fill: Polygon2D


func _ready() -> void:
	_rng.randomize()
	_build_visual()
	_update_visuals()


func reset_at(spawn_pos: Vector2) -> void:
	position = spawn_pos
	hp = MAX_HP
	alive = true
	_ammo = MAGAZINE_SIZE
	_fire_cd = 0.6
	_reload_timer = 0.0
	_patrol_target = Vector2(_rng.randf_range(90, 750), _rng.randf_range(90, 490))
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
	_update_visuals()
	if not multiplayer.is_server() or not alive:
		return

	if _reload_timer > 0.0:
		_reload_timer = max(0.0, _reload_timer - delta)
		if _reload_timer == 0.0:
			_ammo = MAGAZINE_SIZE
	if _fire_cd > 0.0:
		_fire_cd = max(0.0, _fire_cd - delta)

	var target := _find_visible_player()
	if target != null:
		var to_target: Vector2 = target.global_position - global_position
		aim_angle = to_target.angle()
		var dist := to_target.length()

		_strafe_timer -= delta
		if _strafe_timer <= 0.0:
			_strafe_timer = _rng.randf_range(0.6, 1.3)
			_strafe_dir = -1.0 if _rng.randf() < 0.5 else 1.0

		var perp := Vector2(-sin(aim_angle), cos(aim_angle)) * _strafe_dir
		var move_vec := perp * 0.75
		if dist > 240.0:
			move_vec += to_target.normalized() * 0.55
		elif dist < 130.0:
			move_vec -= to_target.normalized() * 0.55
		velocity = move_vec.normalized() * MOVE_SPEED
		move_and_slide()

		if _reload_timer <= 0.0 and _fire_cd <= 0.0:
			if _ammo > 0:
				_ammo -= 1
				_fire_cd = FIRE_COOLDOWN_SEC + _rng.randf_range(0.0, 0.2)
				var spread := _rng.randf_range(-0.11, 0.11)
				var shot_angle := aim_angle + spread
				var muzzle := global_position + Vector2.RIGHT.rotated(shot_angle) * 24.0
				fire_requested.emit(entity_id, muzzle, shot_angle, 18, true)
			else:
				_reload_timer = RELOAD_SEC
	else:
		var to_patrol := _patrol_target - global_position
		if to_patrol.length() < 24.0:
			_patrol_target = Vector2(_rng.randf_range(90, 750), _rng.randf_range(90, 490))
			to_patrol = _patrol_target - global_position
		aim_angle = to_patrol.angle()
		velocity = to_patrol.normalized() * (MOVE_SPEED * 0.7)
		var prev := global_position
		move_and_slide()
		if global_position.distance_to(prev) < 0.3:
			_patrol_target = Vector2(_rng.randf_range(90, 750), _rng.randf_range(90, 490))


func _find_visible_player() -> Node2D:
	var players_node := get_parent().get_parent().get_node_or_null("PlayersContainer")
	if players_node == null:
		return null

	var space := get_world_2d().direct_space_state
	var best: Node2D = null
	var best_dist := INF
	for p in players_node.get_children():
		if not p.get("alive"):
			continue
		var query := PhysicsRayQueryParameters2D.create(global_position, p.global_position, 1)
		var hit := space.intersect_ray(query)
		if hit.is_empty():
			var d := global_position.distance_to(p.global_position)
			if d < best_dist:
				best_dist = d
				best = p
	return best


func _build_visual() -> void:
	_rig = Node2D.new()
	add_child(_rig)

	var barrel := Polygon2D.new()
	barrel.polygon = PackedVector2Array([
		Vector2(0, -3), Vector2(26, -3), Vector2(26, 3), Vector2(0, 3)
	])
	barrel.color = Color(0.80, 0.84, 0.88)
	_rig.add_child(barrel)

	var body_poly := Polygon2D.new()
	body_poly.polygon = _circle_pts(15.0, 16)
	body_poly.color = Color(0.60, 0.11, 0.11)
	_rig.add_child(body_poly)

	var helmet := Polygon2D.new()
	helmet.polygon = _circle_pts(9.5, 14)
	helmet.color = Color(0.94, 0.27, 0.27)
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
	_hp_fill.color = Color(0.94, 0.27, 0.27)
	add_child(_hp_fill)


func _update_visuals() -> void:
	visible = alive
	if _rig != null:
		_rig.rotation = aim_angle
	if _hp_fill != null:
		var ratio := clampf(float(hp) / float(MAX_HP), 0.0, 1.0)
		_hp_fill.scale.x = ratio


static func _circle_pts(radius: float, segments: int) -> PackedVector2Array:
	var pts := PackedVector2Array()
	for i in range(segments):
		var a := TAU * float(i) / float(segments)
		pts.append(Vector2(cos(a), sin(a)) * radius)
	return pts
