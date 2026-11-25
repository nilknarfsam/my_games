extends Node2D
## Controlador principal: lobby ENet/UDP, spawn multiplayer, bots e HUD tático.

const DEFAULT_PORT: int = 7777
const MAX_CLIENTS: int = 8

const PLAYER_SCENE: PackedScene = preload("res://scenes/player.tscn")
const BOT_SCENE: PackedScene = preload("res://scenes/bot.tscn")
const BULLET_SCENE: PackedScene = preload("res://scenes/bullet.tscn")
const ARENA_SCRIPT = preload("res://scripts/arena.gd")

@onready var arena: Node2D = $Arena
@onready var players_container: Node2D = $PlayersContainer
@onready var bots_container: Node2D = $BotsContainer
@onready var bullets_container: Node2D = $BulletsContainer

@onready var lobby_ui: CanvasLayer = $LobbyUI
@onready var name_input: LineEdit = $LobbyUI/CenterContainer/Panel/VBox/NameInput
@onready var ip_input: LineEdit = $LobbyUI/CenterContainer/Panel/VBox/IpInput
@onready var port_input: LineEdit = $LobbyUI/CenterContainer/Panel/VBox/PortInput
@onready var bots_check: CheckBox = $LobbyUI/CenterContainer/Panel/VBox/BotsCheck
@onready var lobby_status: Label = $LobbyUI/CenterContainer/Panel/VBox/StatusLabel

@onready var hud_ui: CanvasLayer = $HudUI
@onready var hp_label: Label = $HudUI/TopBar/HBox/HpLabel
@onready var ammo_label: Label = $HudUI/TopBar/HBox/AmmoLabel
@onready var round_label: Label = $HudUI/TopBar/HBox/RoundLabel
@onready var banner_label: Label = $HudUI/BannerLabel
@onready var restart_btn: Button = $HudUI/TopBar/HBox/RestartBtn

var _round_number: int = 1
var _round_over: bool = false
var _player_index: int = 0
var _bullet_counter: int = 0


func _ready() -> void:
	_ensure_input_actions()
	_center_world()

	hud_ui.visible = false
	banner_label.visible = false

	multiplayer.peer_connected.connect(_on_peer_connected)
	multiplayer.peer_disconnected.connect(_on_peer_disconnected)
	multiplayer.connected_to_server.connect(_on_connected_to_server)
	multiplayer.connection_failed.connect(_on_connection_failed)
	multiplayer.server_disconnected.connect(_on_server_disconnected)


func _center_world() -> void:
	var offset := Vector2(92, 62)
	arena.position = offset
	players_container.position = offset
	bots_container.position = offset
	bullets_container.position = offset


func _process(_delta: float) -> void:
	if not hud_ui.visible:
		return
	_refresh_local_hud()


func _on_host_pressed() -> void:
	var port := int(port_input.text) if port_input.text.is_valid_int() else DEFAULT_PORT
	var peer := ENetMultiplayerPeer.new()
	var err := peer.create_server(port, MAX_CLIENTS)
	if err != OK:
		lobby_status.text = "Erro ao abrir servidor na porta %d (código %d)." % [port, err]
		return

	multiplayer.multiplayer_peer = peer
	lobby_ui.visible = false
	hud_ui.visible = true
	restart_btn.visible = true

	_spawn_player(1, _safe_name())
	if bots_check.button_pressed:
		_spawn_two_bots()
	_sync_round_banner.rpc("Round 1 iniciado! (Host porta %d)" % port, false)


func _on_join_pressed() -> void:
	var ip := ip_input.text.strip_edges()
	if ip.is_empty():
		ip = "127.0.0.1"
	var port := int(port_input.text) if port_input.text.is_valid_int() else DEFAULT_PORT

	var peer := ENetMultiplayerPeer.new()
	var err := peer.create_client(ip, port)
	if err != OK:
		lobby_status.text = "Erro ao conectar em %s:%d (código %d)." % [ip, port, err]
		return

	multiplayer.multiplayer_peer = peer
	lobby_status.text = "Conectando em %s:%d..." % [ip, port]


func _on_restart_pressed() -> void:
	if not multiplayer.is_server():
		return
	_start_new_round()


func _on_leave_pressed() -> void:
	_disconnect_and_reset()


func _on_peer_connected(peer_id: int) -> void:
	if multiplayer.is_server():
		_spawn_player(peer_id, "Jogador %d" % peer_id)


func _on_peer_disconnected(peer_id: int) -> void:
	if not multiplayer.is_server():
		return
	var node := players_container.get_node_or_null("Player_%d" % peer_id)
	if node != null:
		node.queue_free()


func _on_connected_to_server() -> void:
	lobby_ui.visible = false
	hud_ui.visible = true
	restart_btn.visible = false
	_register_player_name.rpc_id(1, _safe_name())


func _on_connection_failed() -> void:
	multiplayer.multiplayer_peer = null
	lobby_status.text = "Falha ao conectar. Confira o IP e se o Host está aberto."


func _on_server_disconnected() -> void:
	_disconnect_and_reset()
	lobby_status.text = "Desconectado do servidor."


func _disconnect_and_reset() -> void:
	if multiplayer.multiplayer_peer != null:
		multiplayer.multiplayer_peer.close()
		multiplayer.multiplayer_peer = null

	for child in players_container.get_children():
		child.queue_free()
	for child in bots_container.get_children():
		child.queue_free()
	for child in bullets_container.get_children():
		child.queue_free()

	_player_index = 0
	_round_number = 1
	_round_over = false
	hud_ui.visible = false
	lobby_ui.visible = true


@rpc("any_peer", "reliable")
func _register_player_name(new_name: String) -> void:
	if not multiplayer.is_server():
		return
	var sender := multiplayer.get_remote_sender_id()
	var player := players_container.get_node_or_null("Player_%d" % sender)
	if player != null:
		player.set("player_name", new_name.substr(0, 14))


func _spawn_player(peer_id: int, p_name: String) -> void:
	var player := PLAYER_SCENE.instantiate()
	player.name = "Player_%d" % peer_id
	player.set("entity_id", peer_id)
	player.set("player_name", p_name)

	var palette := [
		Color(0.22, 0.74, 0.97),
		Color(0.06, 0.72, 0.51),
		Color(0.98, 0.75, 0.14),
		Color(0.66, 0.33, 0.97),
	]
	player.set("team_color", palette[_player_index % palette.size()])
	var spawn := ARENA_SCRIPT.PLAYER_SPAWNS[_player_index % ARENA_SCRIPT.PLAYER_SPAWNS.size()]
	_player_index += 1

	player.position = spawn
	player.connect("fire_requested", _on_fire_requested)
	player.connect("eliminated", _on_entity_eliminated)
	players_container.add_child(player, true)


func _spawn_two_bots() -> void:
	for i in range(2):
		var bot := BOT_SCENE.instantiate()
		bot.name = "Bot_%d" % (i + 1)
		bot.set("entity_id", -100 - i)
		bot.position = ARENA_SCRIPT.BOT_SPAWNS[i]
		bot.connect("fire_requested", _on_fire_requested)
		bot.connect("eliminated", _on_entity_eliminated)
		bots_container.add_child(bot, true)


func _on_fire_requested(shooter_id: int, spawn_pos: Vector2, angle: float, damage: int, from_bot: bool) -> void:
	if not multiplayer.is_server():
		return
	_bullet_counter += 1
	var bullet := BULLET_SCENE.instantiate()
	bullet.name = "Bullet_%d" % _bullet_counter
	bullet.position = spawn_pos - bullets_container.global_position
	bullet.rotation = angle
	bullet.set("shooter_id", shooter_id)
	bullet.set("damage", damage)
	bullet.set("from_bot", from_bot)
	bullets_container.add_child(bullet, true)


func _on_entity_eliminated(_victim_id: int, _killer_id: int) -> void:
	if not multiplayer.is_server() or _round_over:
		return

	var alive_players := 0
	for p in players_container.get_children():
		if p.get("alive"):
			alive_players += 1

	var alive_bots := 0
	for b in bots_container.get_children():
		if b.get("alive"):
			alive_bots += 1

	if bots_container.get_child_count() > 0:
		if alive_bots == 0:
			_end_round("JOGADORES VENCERAM O ROUND!")
		elif alive_players == 0:
			_end_round("OS 2 OPONENTES VENCERAM!")
	elif players_container.get_child_count() >= 2 and alive_players <= 1:
		_end_round("ROUND FINALIZADO!")


func _end_round(message: String) -> void:
	_round_over = true
	_sync_round_banner.rpc(message, true)
	await get_tree().create_timer(2.6).timeout
	if multiplayer.multiplayer_peer != null and multiplayer.is_server():
		_start_new_round()


func _start_new_round() -> void:
	_round_over = false
	_round_number += 1

	for b in bullets_container.get_children():
		b.queue_free()

	var idx := 0
	for p in players_container.get_children():
		p.reset_at(ARENA_SCRIPT.PLAYER_SPAWNS[idx % ARENA_SCRIPT.PLAYER_SPAWNS.size()])
		idx += 1

	var b_idx := 0
	for bot in bots_container.get_children():
		bot.reset_at(ARENA_SCRIPT.BOT_SPAWNS[b_idx % ARENA_SCRIPT.BOT_SPAWNS.size()])
		b_idx += 1

	_sync_round_banner.rpc("Round %d iniciado!" % _round_number, false)


@rpc("authority", "call_local", "reliable")
func _sync_round_banner(text: String, sticky: bool) -> void:
	round_label.text = "Round %d" % _round_number
	banner_label.text = text
	banner_label.visible = true
	if not sticky:
		await get_tree().create_timer(2.0).timeout
		if banner_label.text == text:
			banner_label.visible = false


func _refresh_local_hud() -> void:
	var local_id := multiplayer.get_unique_id()
	var player := players_container.get_node_or_null("Player_%d" % local_id)
	if player == null:
		return

	hp_label.text = "HP: %d" % int(player.get("hp"))
	if player.get("is_reloading"):
		ammo_label.text = "Recarregando..."
	else:
		ammo_label.text = "Munição: %d/%d" % [int(player.get("ammo")), 15]


func _safe_name() -> String:
	var cleaned := name_input.text.strip_edges()
	return "Jogador" if cleaned.is_empty() else cleaned.substr(0, 14)


static func _ensure_input_actions() -> void:
	var key_map := {
		"move_up": [KEY_W, KEY_UP],
		"move_down": [KEY_S, KEY_DOWN],
		"move_left": [KEY_A, KEY_LEFT],
		"move_right": [KEY_D, KEY_RIGHT],
		"reload": [KEY_R],
	}
	for action in key_map.keys():
		if not InputMap.has_action(action):
			InputMap.add_action(action)
			for keycode in key_map[action]:
				var ev := InputEventKey.new()
				ev.keycode = keycode
				InputMap.action_add_event(action, ev)

	if not InputMap.has_action("shoot"):
		InputMap.add_action("shoot")
		var mouse_ev := InputEventMouseButton.new()
		mouse_ev.button_index = MOUSE_BUTTON_LEFT
		InputMap.action_add_event("shoot", mouse_ev)
