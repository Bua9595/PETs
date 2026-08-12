extends Node2D

const DEFAULT_MANIFEST_PATH := "res://assets/rig_manifest.json"
const SHARED_LOADER_RELATIVE_PATH := "../../godot/pet_manifest_loader.gd"
const WAVE_BURST_COOLDOWN_MS := 600
const CHASE_SPEED_PX_PER_SECOND := 300.0
const CHASE_ARRIVAL_RADIUS_PX := 8.0

enum PetState { IDLE, WAVE, CHASE, DRAG }

var _dragging := false
var _drag_offset := Vector2i.ZERO
var _action_running := false
var _wave_burst_locked := false
var _wave_finished := false
var _last_space_request_msec := 0
var _wave_start_count := 0
var _manifest: Dictionary = {}
var _manifest_path := DEFAULT_MANIFEST_PATH
var _bones_by_name: Dictionary = {}
var _parts_by_id: Dictionary = {}
var _idle_bounds := PackedVector2Array()
var _wave_bounds := PackedVector2Array()
var _left_pupil_base_position := Vector2.ZERO
var _right_pupil_base_position := Vector2.ZERO
var _max_pupil_offset := Vector2(4, 3)
var _max_head_tilt := 0.07
var _cursor_radius := 180.0
var _state := PetState.IDLE
var _chase_target_global := Vector2.ZERO

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

	_manifest_path = _manifest_path_from_arguments()
	var rig_result := _load_rig_from_manifest(_manifest_path)
	_manifest = rig_result.get("manifest", {}) as Dictionary
	_parts_by_id = rig_result.get("parts_by_id", {}) as Dictionary
	_bones_by_name = rig_result.get("bones_by_name", {}) as Dictionary
	_apply_manifest_layout()
	_build_manifest_animations()
	_load_action_bounds()
	_configure_cursor_look()
	_set_wave_parts_visible(false)
	_set_passthrough_polygon(_idle_bounds, "idle")
	_animation_player.animation_finished.connect(_on_animation_finished)
	_animation_player.play(&"idle_breath")

	print("DesktopPetTexturedRig _ready root=", name)
	print("manifest_path=", _manifest_path)
	print("transparency_available=", DisplayServer.has_feature(DisplayServer.FEATURE_WINDOW_TRANSPARENCY))
	print("window.transparent=", window.transparent)
	print("viewport.transparent_bg=", get_viewport().transparent_bg)
	print("borderless=", window.borderless)
	print("always_on_top=", window.always_on_top)
	print("manifest_parts_loaded=", _parts_by_id.size())
	print("idle_bounds_points=", _idle_bounds.size())
	print("wave_bounds_points=", _wave_bounds.size())
	print("wave_burst_cooldown_ms=", WAVE_BURST_COOLDOWN_MS)
	if "--run-production-checks" in OS.get_cmdline_user_args():
		_run_production_checks.call_deferred()


func _process(delta: float) -> void:
	_recover_drag_if_button_released(Input.is_mouse_button_pressed(MOUSE_BUTTON_LEFT))
	if _wave_finished:
		_try_release_wave_burst_lock()
	if _state == PetState.CHASE:
		_advance_chase(delta)
	if not _dragging:
		look_at_cursor(delta)


func _input(event: InputEvent) -> void:
	if event is InputEventKey and event.pressed and not event.echo:
		if _is_exit_key_event(event):
			get_tree().quit()
			return
		if event.keycode == KEY_C:
			request_chase_from_keypress()
			return
		if event.keycode == KEY_SPACE:
			request_wave_from_keypress()
			return

	if event is InputEventMouseButton and event.button_index == MOUSE_BUTTON_LEFT:
		if event.pressed:
			_begin_drag()
		else:
			_finish_drag()
		return

	if event is InputEventMouseMotion and _dragging:
		get_window().position = DisplayServer.mouse_get_position() - _drag_offset


func request_wave_from_keypress() -> void:
	if _state != PetState.IDLE:
		return
	_last_space_request_msec = Time.get_ticks_msec()
	if _wave_burst_locked:
		print("wave_request_ignored=true")
		return
	_wave_burst_locked = true
	_wave_finished = false
	_action_running = true
	_state = PetState.WAVE
	_wave_start_count += 1
	_set_wave_parts_visible(true)
	_set_passthrough_polygon(_wave_bounds, "wave")
	print("wave_started_count=", _wave_start_count)
	_animation_player.play(&"wave", 0.12)


func request_chase_from_keypress() -> void:
	if _state != PetState.IDLE:
		return
	if _wave_finished:
		_try_release_wave_burst_lock()
	_chase_target_global = Vector2(DisplayServer.mouse_get_position())
	_state = PetState.CHASE
	_set_passthrough_polygon(_idle_bounds, "idle")
	_animation_player.play(&"idle_breath", 0.12)
	print("chase_started=true target=", _chase_target_global)


func _cancel_chase() -> void:
	if _state != PetState.CHASE:
		return
	_state = PetState.DRAG
	_animation_player.play(&"idle_breath", 0.12)
	_set_passthrough_polygon(_idle_bounds, "idle")
	print("chase_cancelled_for_drag=true")


func _begin_drag() -> void:
	if _state == PetState.WAVE:
		_cleanup_wave(true)
	elif _state == PetState.CHASE:
		_cancel_chase()
	_dragging = true
	_state = PetState.DRAG
	_drag_offset = DisplayServer.mouse_get_position() - get_window().position


func _finish_drag() -> void:
	if not _dragging and _state != PetState.DRAG:
		return
	_dragging = false
	_state = PetState.IDLE
	_restore_idle_visuals(0.12, false)


func _recover_drag_if_button_released(left_button_pressed: bool) -> void:
	if _state == PetState.DRAG and _dragging and not left_button_pressed:
		_finish_drag()


func _is_exit_key_event(event: InputEventKey) -> bool:
	return event.pressed and not event.echo and event.keycode == KEY_ESCAPE


func _advance_chase(delta: float) -> void:
	var visible_center := _bounds_center(_idle_bounds)
	var desired_window_position := _chase_target_global - visible_center
	var clamped_target := _clamp_window_position(desired_window_position, _idle_bounds)
	var current := Vector2(get_window().position)
	var offset := clamped_target - current
	if offset.length() <= CHASE_ARRIVAL_RADIUS_PX:
		get_window().position = Vector2i(clamped_target.round())
		_complete_chase()
		print("chase_arrived=true")
		return
	var step := minf(CHASE_SPEED_PX_PER_SECOND * maxf(delta, 0.0), offset.length())
	get_window().position = Vector2i((current + offset.normalized() * step).round())


func _complete_chase() -> void:
	_state = PetState.IDLE
	_restore_idle_visuals(0.12, false)


func _bounds_center(bounds: PackedVector2Array) -> Vector2:
	if bounds.is_empty():
		return Vector2.ZERO
	var min_point := bounds[0]
	var max_point := bounds[0]
	for point in bounds:
		min_point = min_point.min(point)
		max_point = max_point.max(point)
	return (min_point + max_point) * 0.5


func _clamp_window_position(desired: Vector2, visible_bounds: PackedVector2Array) -> Vector2:
	if visible_bounds.is_empty():
		return desired
	var min_point := visible_bounds[0]
	var max_point := visible_bounds[0]
	for point in visible_bounds:
		min_point = min_point.min(point)
		max_point = max_point.max(point)
	var screen := DisplayServer.window_get_current_screen()
	var usable := DisplayServer.screen_get_usable_rect(screen)
	return Vector2(
		clampf(desired.x, float(usable.position.x) - min_point.x, float(usable.end.x) - max_point.x),
		clampf(desired.y, float(usable.position.y) - min_point.y, float(usable.end.y) - max_point.y)
	)


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
	if animation_name == &"wave" and _state == PetState.WAVE:
		_cleanup_wave(false)
		_state = PetState.IDLE
		_try_release_wave_burst_lock()


func _cleanup_wave(cancelled: bool) -> void:
	_action_running = false
	if cancelled:
		_wave_finished = false
		_wave_burst_locked = false
		_restore_idle_visuals(0.0, true)
		return
	_wave_finished = true
	_restore_idle_visuals(0.15, false)


func _restore_idle_visuals(blend_seconds: float, reset_pose: bool) -> void:
	_set_wave_parts_visible(false)
	_set_passthrough_polygon(_idle_bounds, "idle")
	_animation_player.play(&"idle_breath", blend_seconds)
	if reset_pose:
		_animation_player.seek(0.0, true)


func _set_wave_parts_visible(wave_visible: bool) -> void:
	var normal_arm := _parts_by_id.get("right_arm_render_surface") as Sprite2D
	if normal_arm != null:
		normal_arm.visible = not wave_visible
	for part_id in ["wave_right_upper_arm", "wave_right_lower_arm", "wave_right_hand"]:
		var wave_part := _parts_by_id.get(part_id) as Sprite2D
		if wave_part != null:
			wave_part.visible = wave_visible


func _try_release_wave_burst_lock() -> void:
	if Time.get_ticks_msec() - _last_space_request_msec < WAVE_BURST_COOLDOWN_MS:
		return
	_wave_finished = false
	_wave_burst_locked = false
	print("wave_burst_lock_released=true")


func _wave_parts_match(expected_wave_visible: bool) -> bool:
	var normal_arm := _parts_by_id.get("right_arm_render_surface") as Sprite2D
	if normal_arm == null or normal_arm.visible == expected_wave_visible:
		return false
	for part_id in ["wave_right_upper_arm", "wave_right_lower_arm", "wave_right_hand"]:
		var wave_part := _parts_by_id.get(part_id) as Sprite2D
		if wave_part == null or wave_part.visible != expected_wave_visible:
			return false
	return true


func _state_is_idle_clean() -> bool:
	return (
		_state == PetState.IDLE
		and not _dragging
		and not _action_running
		and _wave_parts_match(false)
		and _animation_player.current_animation == &"idle_breath"
	)


func _manifest_path_from_arguments() -> String:
	for argument in OS.get_cmdline_user_args():
		if argument.begins_with("--pet-manifest="):
			var candidate := argument.trim_prefix("--pet-manifest=")
			if candidate.is_absolute_path() or candidate.begins_with("res://"):
				return candidate
			return ProjectSettings.globalize_path("res://").path_join(candidate).simplify_path()
	return DEFAULT_MANIFEST_PATH


func _load_rig_from_manifest(manifest_path: String) -> Dictionary:
	var project_directory := ProjectSettings.globalize_path("res://")
	var loader_path := project_directory.path_join(SHARED_LOADER_RELATIVE_PATH).simplify_path()
	var loader_source := FileAccess.get_file_as_string(loader_path)
	if loader_source.is_empty():
		push_error("Unable to read shared production pet loader: %s" % loader_path)
		return {}
	var loader_script := GDScript.new()
	loader_script.source_code = loader_source
	if loader_script.reload() != OK:
		push_error("Unable to compile shared production pet loader: %s" % loader_path)
		return {}
	var loader: RefCounted = loader_script.new()
	return loader.call("load_into", manifest_path, _skeleton, _pet_root) as Dictionary


func _apply_manifest_layout() -> void:
	var canvas := _manifest.get("canvas", {}) as Dictionary
	var canvas_size := Vector2i(int(canvas.get("width", 900)), int(canvas.get("height", 760)))
	if canvas_size.x > 0 and canvas_size.y > 0:
		get_window().size = canvas_size
	_pet_root.position = _vector2_from_value(_manifest.get("ground_anchor", _manifest.get("pet_root", [450, 720])))
	_rig.position = _vector2_from_value(_manifest.get("rig_offset", [0, 0]))
	_rig.scale = _vector2_from_value(_manifest.get("rig_scale", [1, 1]))


func _build_manifest_animations() -> void:
	var animation_values := _manifest.get("animations", {}) as Dictionary
	var idle_values := animation_values.get("idle_breath", {}) as Dictionary
	var wave_values := animation_values.get("wave", {}) as Dictionary
	var library := _animation_player.get_animation_library("")
	if library == null:
		library = AnimationLibrary.new()
		_animation_player.add_animation_library("", library)
	for animation_name in [&"RESET", &"idle_breath", &"wave"]:
		if library.has_animation(animation_name):
			library.remove_animation(animation_name)
	library.add_animation(&"RESET", _create_reset_animation())
	library.add_animation(&"idle_breath", _create_idle_animation(idle_values))
	library.add_animation(&"wave", _create_wave_animation(wave_values))


func _create_reset_animation() -> Animation:
	var animation := Animation.new()
	animation.resource_name = "RESET"
	animation.length = 0.0
	for bone_name in ["HeadBone", "LeftUpperArmBone", "RightUpperArmBone", "RightLowerArmBone", "RightHandBone", "TailBone"]:
		var bone := _bones_by_name.get(bone_name) as Bone2D
		if bone == null:
			continue
		var property := "position" if bone_name == "HeadBone" else "rotation_degrees"
		var value: Variant = bone.position if property == "position" else bone.rotation_degrees
		_add_value_track(animation, bone, property, [0.0], [value])
	return animation


func _create_idle_animation(values: Dictionary) -> Animation:
	var animation := Animation.new()
	animation.resource_name = "idle_breath"
	animation.length = float(values.get("duration_seconds", 2.4))
	animation.loop_mode = Animation.LOOP_LINEAR
	var times := [0.0, animation.length * 0.25, animation.length * 0.5, animation.length * 0.75, animation.length]
	var head_lift := float(values.get("head_lift", -6.0))
	_add_value_track(animation, _head_bone, "position", times, [
		_head_bone.position,
		_head_bone.position + Vector2(0, head_lift * 0.65),
		_head_bone.position + Vector2(0, head_lift),
		_head_bone.position + Vector2(0, head_lift * 0.65),
		_head_bone.position,
	])
	var arm_sway := float(values.get("arm_sway_degrees", 1.0))
	for bone_name in ["LeftUpperArmBone", "RightUpperArmBone"]:
		var bone := _bones_by_name.get(bone_name) as Bone2D
		if bone == null:
			continue
		var direction := 1.0 if bone_name.begins_with("Left") else -1.0
		var base := bone.rotation_degrees
		_add_value_track(animation, bone, "rotation_degrees", times, [base, base + direction * arm_sway * 0.65, base + direction * arm_sway, base + direction * arm_sway * 0.65, base])
	var tail := _bones_by_name.get("TailBone") as Bone2D
	if tail != null:
		var tail_sway := float(values.get("tail_sway_degrees", 2.0))
		var tail_base := tail.rotation_degrees
		_add_value_track(animation, tail, "rotation_degrees", times, [tail_base, tail_base + tail_sway, tail_base, tail_base - tail_sway, tail_base])
	return animation


func _create_wave_animation(values: Dictionary) -> Animation:
	var animation := Animation.new()
	animation.resource_name = "wave"
	animation.length = float(values.get("duration_seconds", 2.2))
	animation.loop_mode = Animation.LOOP_NONE
	var side := String(values.get("side", "right")).capitalize()
	var upper := _bones_by_name.get(side + "UpperArmBone") as Bone2D
	var lower := _bones_by_name.get(side + "LowerArmBone") as Bone2D
	var hand := _bones_by_name.get(side + "HandBone") as Bone2D
	var upper_offsets := values.get("upper_arm_degrees", []) as Array
	_add_rotation_sequence(animation, upper, upper_offsets, animation.length)
	_add_rotation_sequence(animation, lower, values.get("lower_arm_degrees", []), animation.length)
	_add_rotation_sequence(animation, hand, values.get("hand_degrees", []), animation.length)
	return animation


func _add_rotation_sequence(animation: Animation, bone: Bone2D, offsets_value: Variant, duration: float) -> void:
	if bone == null or not offsets_value is Array:
		return
	var offsets := offsets_value as Array
	if offsets.size() < 2:
		return
	var times: Array = []
	var rotations: Array = []
	for index in range(offsets.size()):
		times.append(duration * float(index) / float(offsets.size() - 1))
		rotations.append(bone.rotation_degrees + float(offsets[index]))
	_add_value_track(animation, bone, "rotation_degrees", times, rotations)


func _add_value_track(animation: Animation, node: Node, property_name: String, times: Array, values: Array) -> void:
	var track := animation.add_track(Animation.TYPE_VALUE)
	animation.track_set_path(track, NodePath("%s:%s" % [get_path_to(node), property_name]))
	animation.track_set_interpolation_type(track, Animation.INTERPOLATION_CUBIC)
	for index in range(times.size()):
		animation.track_insert_key(track, float(times[index]), values[index])


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


func _run_production_checks() -> void:
	var failures: Array[String] = []
	if _parts_by_id.size() != (_manifest.get("parts", []) as Array).size():
		failures.append("not all manifest parts were loaded")
	if not _bones_by_name.has("TailBone"):
		failures.append("TailBone was not loaded")
	for render_surface_id in ["body_render_surface", "head_render_surface", "right_arm_render_surface"]:
		var render_surface := _parts_by_id.get(render_surface_id) as Sprite2D
		if render_surface == null or not render_surface.visible:
			failures.append("missing visible render surface: %s" % render_surface_id)
	for hidden_source_id in ["torso", "right_shoulder_socket", "right_upper_arm", "right_lower_arm", "right_hand", "left_upper_leg", "left_lower_leg", "left_foot", "right_upper_leg", "right_lower_leg", "right_foot"]:
		var hidden_source := _parts_by_id.get(hidden_source_id) as Sprite2D
		if hidden_source == null or hidden_source.visible:
			failures.append("source part must not be double-rendered: %s" % hidden_source_id)
	for animation_name in [&"idle_breath", &"wave"]:
		if not _animation_player.has_animation(animation_name):
			failures.append("missing animation: %s" % animation_name)
	if _idle_bounds.size() >= 3:
		var idle_min := _idle_bounds[0]
		var idle_max := _idle_bounds[0]
		for point in _idle_bounds:
			idle_min = idle_min.min(point)
			idle_max = idle_max.max(point)
		var usable := DisplayServer.screen_get_usable_rect(DisplayServer.window_get_current_screen())
		var visible_size := idle_max - idle_min
		if usable.size.x >= visible_size.x and usable.size.y >= visible_size.y:
			var clamped_probe := _clamp_window_position(Vector2(-100000, -100000), _idle_bounds)
			if clamped_probe.x + idle_min.x < usable.position.x or clamped_probe.y + idle_min.y < usable.position.y:
				failures.append("chase clamp allows visible bounds off the usable screen")
			if clamped_probe.x + idle_max.x > usable.end.x or clamped_probe.y + idle_max.y > usable.end.y:
				failures.append("chase clamp allows visible bounds past the usable screen")
		else:
			print("chase_clamp_screen_check_skipped=headless_screen_too_small")

	var previous_target := _chase_target_global
	request_chase_from_keypress()
	if _state != PetState.CHASE:
		failures.append("chase did not enter CHASE state")
	previous_target = _chase_target_global
	request_chase_from_keypress()
	if _chase_target_global != previous_target:
		failures.append("second chase request changed the frozen target")
	_cancel_chase()
	_state = PetState.IDLE
	_animation_player.play(&"idle_breath")
	_set_passthrough_polygon(_idle_bounds, "idle")

	var left_pupil := _parts_by_id.get("left_pupil") as Sprite2D
	var right_pupil := _parts_by_id.get("right_pupil") as Sprite2D
	if left_pupil == null or right_pupil == null:
		failures.append("cursor pupils were not loaded")
	else:
		_apply_look_direction(Vector2.RIGHT, 1.0)
		if not is_equal_approx(left_pupil.position.x, _left_pupil_base_position.x + _max_pupil_offset.x):
			failures.append("left pupil did not reach its right bound")
		if not is_equal_approx(right_pupil.position.x, _right_pupil_base_position.x + _max_pupil_offset.x):
			failures.append("right pupil did not reach its right bound")
		_apply_look_direction(Vector2(-2, 2).normalized(), 1.0)
		var left_offset := left_pupil.position - _left_pupil_base_position
		if absf(left_offset.x) > _max_pupil_offset.x or absf(left_offset.y) > _max_pupil_offset.y:
			failures.append("pupil movement exceeded configured bounds")
		_apply_look_direction(Vector2.ZERO, 1.0)

	for _request_index in range(10):
		request_wave_from_keypress()
		await get_tree().create_timer(0.1).timeout
	while _animation_player.current_animation == &"wave":
		await get_tree().process_frame
	await get_tree().process_frame
	if _wave_start_count != 1:
		failures.append("ten-key burst started %d waves instead of one" % _wave_start_count)
	if _animation_player.current_animation != &"idle_breath":
		failures.append("wave did not return to idle_breath")

	await get_tree().create_timer(0.7).timeout
	request_wave_from_keypress()
	if _wave_start_count != 2:
		failures.append("new wave did not start after cooldown")
	while _animation_player.current_animation == &"wave":
		await get_tree().process_frame
	if _animation_player.current_animation != &"idle_breath":
		failures.append("second wave did not return to idle_breath")
	if not _state_is_idle_clean():
		failures.append("regular wave completion did not leave a clean IDLE state")

	_wave_burst_locked = false
	_wave_finished = false
	request_wave_from_keypress()
	_on_animation_finished(&"wave")
	if not _wave_burst_locked or not _wave_finished or _state != PetState.IDLE:
		failures.append("early regular wave finish did not preserve its pending cooldown")
	var wave_count_before_chase := _wave_start_count
	request_chase_from_keypress()
	if _state != PetState.CHASE:
		failures.append("C after wave did not enter CHASE")
	if _wave_burst_locked and not _wave_finished:
		failures.append("chase disabled the pending wave cooldown release")
	_last_space_request_msec = Time.get_ticks_msec() - WAVE_BURST_COOLDOWN_MS
	_process(0.0)
	if _wave_burst_locked or _wave_finished:
		failures.append("wave cooldown did not release while CHASE was active")
	_complete_chase()
	if not _state_is_idle_clean():
		failures.append("CHASE arrival did not return to a clean IDLE state")
	_wave_burst_locked = false
	_wave_finished = false
	request_wave_from_keypress()
	if _wave_start_count != wave_count_before_chase + 1:
		failures.append("Space did not work after WAVE to CHASE sequence")
	var wave_values := (_manifest.get("animations", {}) as Dictionary).get("wave", {}) as Dictionary
	var upper_arm_offsets := wave_values.get("upper_arm_degrees", []) as Array
	var max_pose_index := 0
	var max_pose_magnitude := 0.0
	for index in range(upper_arm_offsets.size()):
		var magnitude := absf(float(upper_arm_offsets[index]))
		if magnitude > max_pose_magnitude:
			max_pose_magnitude = magnitude
			max_pose_index = index
	if upper_arm_offsets.size() > 1:
		var max_pose_time := _animation_player.current_animation_length * float(max_pose_index) / float(upper_arm_offsets.size() - 1)
		_animation_player.seek(max_pose_time, true)
	_begin_drag()
	if _state != PetState.DRAG or not _dragging:
		failures.append("WAVE to DRAG did not enter DRAG")
	if not _wave_parts_match(false) or _action_running or _wave_burst_locked or _wave_finished:
		failures.append("WAVE to DRAG left wave parts or flags active")
	var window_position_before_recovery := get_window().position
	_recover_drag_if_button_released(false)
	if not _state_is_idle_clean():
		failures.append("lost mouse release did not recover DRAG to IDLE")
	if get_window().position != window_position_before_recovery:
		failures.append("lost mouse release recovery moved the window")

	var wave_count_after_drag := _wave_start_count
	request_wave_from_keypress()
	if _wave_start_count != wave_count_after_drag + 1:
		failures.append("Space did not work after WAVE to DRAG recovery")
	_cleanup_wave(true)
	_state = PetState.IDLE
	request_chase_from_keypress()
	if _state != PetState.CHASE:
		failures.append("C did not work after WAVE to DRAG recovery")
	_begin_drag()
	if _state != PetState.DRAG or not _dragging:
		failures.append("CHASE to DRAG did not enter DRAG")
	_recover_drag_if_button_released(false)
	if not _state_is_idle_clean():
		failures.append("CHASE to DRAG did not return cleanly to IDLE")
	var final_wave_count := _wave_start_count
	request_wave_from_keypress()
	if _wave_start_count != final_wave_count + 1:
		failures.append("Space did not work after CHASE to DRAG sequence")
	_cleanup_wave(true)
	_state = PetState.IDLE
	request_chase_from_keypress()
	if _state != PetState.CHASE:
		failures.append("C did not work after CHASE to DRAG sequence")
	_complete_chase()

	for state_value in [PetState.IDLE, PetState.WAVE, PetState.CHASE, PetState.DRAG]:
		_state = state_value
		var escape_event := InputEventKey.new()
		escape_event.keycode = KEY_ESCAPE
		escape_event.pressed = true
		if not _is_exit_key_event(escape_event):
			failures.append("Esc was not accepted from state %s" % state_value)
	_state = PetState.IDLE
	_restore_idle_visuals(0.0, true)

	if failures.is_empty():
		print("production_checks_passed=true")
		get_tree().quit()
		return
	for failure in failures:
		push_error("production_check_failed: %s" % failure)
	get_tree().quit(1)
