extends Node2D

var _dragging := false
var _drag_offset := Vector2i.ZERO
var _action_running := false

@onready var _animation_player: AnimationPlayer = $AnimationPlayer

# Both polygons use the 640x640 action-canvas coordinates. The idle region hugs
# the resting figure; the wave region reserves the right/upward arm arc.
var idle_passthrough_polygon := PackedVector2Array([
	Vector2(260, 252), Vector2(380, 252), Vector2(385, 340),
	Vector2(425, 370), Vector2(435, 500), Vector2(392, 518),
	Vector2(397, 598), Vector2(350, 606), Vector2(320, 594),
	Vector2(290, 606), Vector2(243, 598), Vector2(248, 518),
	Vector2(205, 500), Vector2(215, 370), Vector2(255, 340),
])
var wave_passthrough_polygon := PackedVector2Array([
	Vector2(260, 252), Vector2(382, 252), Vector2(450, 226),
	Vector2(520, 252), Vector2(532, 330), Vector2(515, 450),
	Vector2(442, 515), Vector2(392, 518), Vector2(397, 598),
	Vector2(350, 606), Vector2(320, 594), Vector2(290, 606),
	Vector2(243, 598), Vector2(248, 518), Vector2(205, 500),
	Vector2(215, 370), Vector2(255, 340),
])


func _ready() -> void:
	get_viewport().transparent_bg = true
	var window := get_window()
	window.transparent = true
	window.borderless = true
	window.always_on_top = true

	_set_passthrough_polygon(idle_passthrough_polygon, "idle")
	_animation_player.animation_finished.connect(_on_animation_finished)
	_animation_player.play(&"idle_breath")

	print("DesktopPetRig _ready root=", name)
	print("transparency_available=", DisplayServer.has_feature(DisplayServer.FEATURE_WINDOW_TRANSPARENCY))
	print("window.transparent=", window.transparent)
	print("viewport.transparent_bg=", get_viewport().transparent_bg)
	print("borderless=", window.borderless)
	print("always_on_top=", window.always_on_top)
	print("idle_passthrough_polygon_points=", idle_passthrough_polygon.size())
	print("wave_passthrough_polygon_points=", wave_passthrough_polygon.size())
	print("animations=", _animation_player.get_animation_list())


func _input(event: InputEvent) -> void:
	if event is InputEventKey and event.pressed and not event.echo:
		if event.keycode == KEY_ESCAPE:
			get_tree().quit()
			return
		if event.keycode == KEY_SPACE:
			_start_wave()
			return

	if event is InputEventMouseButton and event.button_index == MOUSE_BUTTON_LEFT:
		if event.pressed:
			_dragging = true
			_drag_offset = DisplayServer.mouse_get_position() - get_window().position
		else:
			_dragging = false
		return

	if event is InputEventMouseMotion and _dragging:
		get_window().position = DisplayServer.mouse_get_position() - _drag_offset


func _process(_delta: float) -> void:
	# A mouse-up can occur after the pointer has left the interactive silhouette.
	if _dragging and not Input.is_mouse_button_pressed(MOUSE_BUTTON_LEFT):
		_dragging = false


func _on_animation_finished(animation_name: StringName) -> void:
	if animation_name == &"wave":
		_action_running = false
		_animation_player.play(&"idle_breath", 0.15)
		_set_passthrough_polygon(idle_passthrough_polygon, "idle")


func _start_wave() -> void:
	if _action_running:
		print("wave_request_ignored=true")
		return

	_action_running = true
	_set_passthrough_polygon(wave_passthrough_polygon, "wave")
	# The action starts from frame zero, blends in smoothly, and cannot be toggled
	# or interrupted while its action lock is active.
	_animation_player.play(&"wave", 0.12)


func _set_passthrough_polygon(polygon: PackedVector2Array, mode: String) -> void:
	DisplayServer.window_set_mouse_passthrough(polygon)
	print("passthrough_polygon_mode=", mode, " points=", polygon.size())
