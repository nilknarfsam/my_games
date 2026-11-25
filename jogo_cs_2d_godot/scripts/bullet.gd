extends Area2D
## Projétil replicado via MultiplayerSpawner; colisões resolvidas no servidor.

const SPEED: float = 780.0
const MAX_LIFETIME: float = 1.5

@export var shooter_id: int = 0
@export var damage: int = 25
@export var from_bot: bool = false

var velocity: Vector2 = Vector2.ZERO
var _life: float = MAX_LIFETIME
var _visual: Polygon2D


func _ready() -> void:
	_build_visual()
	velocity = Vector2.RIGHT.rotated(rotation) * SPEED
	if multiplayer.is_server():
		body_entered.connect(_on_body_entered)


func _physics_process(delta: float) -> void:
	if not multiplayer.is_server():
		return
	position += velocity * delta
	_life -= delta
	if _life <= 0.0:
		queue_free()


func _build_visual() -> void:
	_visual = Polygon2D.new()
	_visual.polygon = PackedVector2Array([
		Vector2(-6, -2.5),
		Vector2(6, -2.5),
		Vector2(8, 0),
		Vector2(6, 2.5),
		Vector2(-6, 2.5),
	])
	_visual.color = Color(0.98, 0.44, 0.52) if from_bot else Color(0.99, 0.94, 0.54)
	add_child(_visual)


func _on_body_entered(body: Node) -> void:
	if not multiplayer.is_server():
		return
	if body is StaticBody2D:
		queue_free()
		return
	if body.has_method("apply_damage"):
		if body.get("entity_id") == shooter_id:
			return
		body.apply_damage(damage, shooter_id)
		queue_free()
