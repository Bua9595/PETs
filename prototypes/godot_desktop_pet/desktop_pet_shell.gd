extends Node2D

var _dragging := false
var _drag_offset := Vector2i.ZERO
@onready var _pet_silhouette: Polygon2D = $PetSilhouette


func _ready() -> void:
	get_viewport().transparent_bg = true
	var window := get_window()
	window.transparent = true
	window.borderless = true
	window.always_on_top = true
	# The declarative Polygon2D is both the visible figure and the input region.
	DisplayServer.window_set_mouse_passthrough(_pet_silhouette.polygon)
	print("DesktopPetShell _ready root=", name)
	print("transparency_available=", DisplayServer.has_feature(DisplayServer.FEATURE_WINDOW_TRANSPARENCY))
	print("window.transparent=", window.transparent)
	print("viewport.transparent_bg=", get_viewport().transparent_bg)
	print("borderless=", window.borderless)
	print("always_on_top=", window.always_on_top)
	print("passthrough_polygon_points=", _pet_silhouette.polygon.size())


func _input(event: InputEvent) -> void:
	if event is InputEventKey and event.pressed and not event.echo and event.keycode == KEY_ESCAPE:
		get_tree().quit()
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
	# Mouse-up can happen after the pointer leaves the clickable silhouette.
	if _dragging and not Input.is_mouse_button_pressed(MOUSE_BUTTON_LEFT):
		_dragging = false
