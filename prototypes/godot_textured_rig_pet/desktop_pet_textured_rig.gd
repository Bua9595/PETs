extends Node2D

const MANIFEST_PATH := "res://assets/rig_manifest.json"
const WAVE_BURST_COOLDOWN_MS := 600

var _dragging := false
var _drag_offset := Vector2i.ZERO
var _action_running := false
var _wave_burst_locked := false
var _wave_finished := false
var _last_space_request_msec := 0
var _wave_start_count := 0
var _manifest: Dictionary = {}
var _bones_by_name: Dictionary = {}
var _parts_by_id: Dictionary = {}
var _idle_bounds := PackedVector2Array()
var _wave_bounds := PackedVector2Array()
var _left_pupil_base_position := Vector2.ZERO
var _right_pupil_base_position := Vector2.ZERO
var _max_pupil_offset := Vector2(5, 3)
var _max_head_tilt := 0.07
var _cursor_radius := 180.0

@onready var _pet_root: Node2D = $PetRoot
@onready var _rig: Node2D = $PetRoot/Rig
@onready var _skeleton: Skeleton2D = $PetRoot/Rig/Skeleton2D
@onready var _animation_player: AnimationPlayer = $AnimationPlayer
@onready var _head_bone: Bone2D = $PetRoot/Rig/Skeleton2D/TorsoBone/HeadBone


func _ready() -> void:
	get_viewport().transparent_bg = true
	var window := get_window()
	window.transparent = true
	window.borderless = true
	window.always_on_top = true

	_manifest = _load_manifest()
	_apply_manifest_layout()
	_index_bones(_skeleton)
	_load_manifest_parts()
	_load_action_bounds()
	_configure_cursor_look()
	_set_passthrough_polygon(_idle_bounds, "idle")
	_animation_player.animation_finished.connect(_on_animation_finished)
	_animation_player.play(&"idle_breath")

	print("DesktopPetTexturedRig _ready root=", name)
	print("transparency_available=", DisplayServer.has_feature(DisplayServer.FEATURE_WINDOW_TRANSPARENCY))
	print("window.transparent=", window.transparent)
	print("viewport.transparent_bg=", get_viewport().transparent_bg)
	print("borderless=", window.borderless)
	print("always_on_top=", window.always_on_top)
	print("manifest_parts_loaded=", _parts_by_id.size())
	print("idle_bounds_points=", _idle_bounds.size())
	print("wave_bounds_points=", _wave_bounds.size())
	print("wave_burst_cooldown_ms=", WAVE_BURST_COOLDOWN_MS)


func _process(delta: float) -> void:
	if _dragging and not Input.is_mouse_button_pressed(MOUSE_BUTTON_LEFT):
		_dragging = false
	if _wave_finished:
		_try_release_wave_burst_lock()
	if not _dragging:
		look_at_cursor(delta)


func _input(event: InputEvent) -> void:
	if event is InputEventKey and event.pressed and not event.echo:
		if event.keycode == KEY_ESCAPE:
			get_tree().quit()
			return
		if event.keycode == KEY_SPACE:
			request_wave_from_keypress()
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


func request_wave_from_keypress() -> void:
	_last_space_request_msec = Time.get_ticks_msec()
	if _wave_burst_locked:
		print("wave_request_ignored=true")
		return
	_wave_burst_locked = true
	_wave_finished = false
	_action_running = true
	_wave_start_count += 1
	_set_passthrough_polygon(_wave_bounds, "wave")
	print("wave_started_count=", _wave_start_count)
	_animation_player.play(&"wave", 0.12)


func look_at_cursor(delta: float) -> void:
	var left_pupil := _parts_by_id.get("left_pupil") as Sprite2D
	var right_pupil := _parts_by_id.get("right_pupil") as Sprite2D
	if left_pupil == null or right_pupil == null:
		return
	var cursor_in_window := Vector2(DisplayServer.mouse_get_position() - get_window().position)
	var direction := cursor_in_window - _head_bone.global_position
	var normalized_look := direction.limit_length(_cursor_radius) / _cursor_radius
	_apply_look_direction(normalized_look, delta)


func _apply_look_direction(normalized_look: Vector2, delta: float) -> void:
	var left_pupil := _parts_by_id.get("left_pupil") as Sprite2D
	var right_pupil := _parts_by_id.get("right_pupil") as Sprite2D
	if left_pupil == null or right_pupil == null:
		return
	var desired_pupil_offset := Vector2(normalized_look.x * _max_pupil_offset.x, normalized_look.y * _max_pupil_offset.y)
	var smoothing: float = minf(delta * 10.0, 1.0)
	left_pupil.position = left_pupil.position.lerp(_left_pupil_base_position + desired_pupil_offset, smoothing)
	right_pupil.position = right_pupil.position.lerp(_right_pupil_base_position + desired_pupil_offset, smoothing)
	var desired_tilt: float = clampf(normalized_look.x * _max_head_tilt, -_max_head_tilt, _max_head_tilt)
	_head_bone.rotation = lerp_angle(_head_bone.rotation, desired_tilt, min(delta * 6.0, 1.0))


func _on_animation_finished(animation_name: StringName) -> void:
	if animation_name == &"wave":
		_action_running = false
		_wave_finished = true
		_animation_player.play(&"idle_breath", 0.15)
		_set_passthrough_polygon(_idle_bounds, "idle")


func _try_release_wave_burst_lock() -> void:
	if Time.get_ticks_msec() - _last_space_request_msec < WAVE_BURST_COOLDOWN_MS:
		return
	_wave_finished = false
	_wave_burst_locked = false
	print("wave_burst_lock_released=true")


func _load_manifest() -> Dictionary:
	var json := JSON.new()
	var parse_error := json.parse(FileAccess.get_file_as_string(MANIFEST_PATH))
	if parse_error != OK or not json.data is Dictionary:
		push_error("Unable to parse rig manifest: %s" % MANIFEST_PATH)
		return {}
	return json.data as Dictionary


func _apply_manifest_layout() -> void:
	_pet_root.position = _vector2_from_value(_manifest.get("pet_root", [360, 670]))
	_rig.position = _vector2_from_value(_manifest.get("rig_offset", [0, 0]))


func _index_bones(node: Node) -> void:
	if node is Bone2D:
		_bones_by_name[node.name] = node
	for child in node.get_children():
		_index_bones(child)


func _load_manifest_parts() -> void:
	var manifest_parts := _manifest.get("parts", []) as Array
	var missing_assets := 0
	for part_value in manifest_parts:
		var part := part_value as Dictionary
		var part_id := String(part.get("part_id", ""))
		var bone_name := String(part.get("parent_bone", ""))
		var asset_path := String(part.get("asset_path", ""))
		var parent_bone := _bones_by_name.get(bone_name) as Bone2D
		if parent_bone == null or not FileAccess.file_exists(asset_path):
			missing_assets += 1
			push_error("Missing manifest rig part: %s" % part_id)
			continue
		var texture := _load_svg_texture(asset_path)
		if texture == null:
			missing_assets += 1
			push_error("Failed to load manifest rig part: %s" % part_id)
			continue
		var sprite := Sprite2D.new()
		sprite.name = part_id
		sprite.texture = texture
		sprite.centered = false
		sprite.position = _vector2_from_value(part.get("local_position", [0, 0])) - _vector2_from_value(part.get("pivot", [0, 0]))
		sprite.z_index = int(part.get("z_index", 0))
		sprite.visible = bool(part.get("visible", true))
		parent_bone.add_child(sprite)
		_parts_by_id[part_id] = sprite
	if missing_assets > 0:
		push_error("manifest_assets_missing=%d" % missing_assets)
	else:
		print("manifest_assets_missing=0")


func _load_svg_texture(asset_path: String) -> Texture2D:
	var svg_source := FileAccess.get_file_as_string(asset_path)
	if svg_source.is_empty():
		return null
	var image := Image.new()
	var load_error: Error = image.load_svg_from_string(svg_source, 1.0)
	if load_error != OK:
		push_error("Unable to decode SVG asset: %s" % asset_path)
		return null
	return ImageTexture.create_from_image(image)


func _load_action_bounds() -> void:
	var action_bounds := _manifest.get("action_bounds", {}) as Dictionary
	_idle_bounds = _packed_vectors_from_value(action_bounds.get("idle_bounds", []))
	_wave_bounds = _packed_vectors_from_value(action_bounds.get("wave_bounds", []))
	if _idle_bounds.size() < 3 or _wave_bounds.size() < 3:
		push_error("Rig manifest action bounds are invalid")


func _configure_cursor_look() -> void:
	var cursor_look := _manifest.get("cursor_look", {}) as Dictionary
	_max_pupil_offset = _vector2_from_value(cursor_look.get("max_pupil_offset", [5, 3]))
	_max_head_tilt = float(cursor_look.get("max_head_tilt_radians", 0.07))
	_cursor_radius = float(cursor_look.get("cursor_radius", 180.0))
	var left_pupil := _parts_by_id.get("left_pupil") as Sprite2D
	var right_pupil := _parts_by_id.get("right_pupil") as Sprite2D
	if left_pupil != null:
		_left_pupil_base_position = left_pupil.position
	if right_pupil != null:
		_right_pupil_base_position = right_pupil.position


func _set_passthrough_polygon(polygon: PackedVector2Array, mode: String) -> void:
	DisplayServer.window_set_mouse_passthrough(polygon)
	print("passthrough_mode=", mode, " points=", polygon.size())


func _vector2_from_value(value: Variant) -> Vector2:
	var values := value as Array
	if values.size() != 2:
		return Vector2.ZERO
	return Vector2(float(values[0]), float(values[1]))


func _packed_vectors_from_value(value: Variant) -> PackedVector2Array:
	var vectors := PackedVector2Array()
	for vector_value in value as Array:
		vectors.append(_vector2_from_value(vector_value))
	return vectors
