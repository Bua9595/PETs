extends Node

const WALK_DURATION_SECONDS := 0.72
const TURN_SPEED_DEGREES := 105.0
const OUTLINE_WIDTH := 0.025
const FRAMING_SAFETY_FACTOR := 1.14
const GROUND_MARGIN_FACTOR := 0.05

const VIEW_ANGLES := {
	"front": 0.0,
	"front_3q_right": 45.0,
	"side_right": 90.0,
	"back_3q_right": 135.0,
	"back": 180.0,
}

const REQUIRED_BONES := [
	"TorsoBone",
	"HeadBone",
	"LeftUpperArmBone",
	"LeftLowerArmBone",
	"LeftHandBone",
	"RightUpperArmBone",
	"RightLowerArmBone",
	"RightHandBone",
	"LeftUpperLegBone",
	"LeftLowerLegBone",
	"LeftFootBone",
	"RightUpperLegBone",
	"RightLowerLegBone",
	"RightFootBone",
	"TailBone",
]

var _model_root: Node3D
var _skeleton: Skeleton3D
var _camera: Camera3D
var _status_label: Label
var _bones: Dictionary = {}
var _part_count: int = 0
var _visible_parts: Array[MeshInstance3D] = []
var _sampled_motion_bounds: Array[AABB] = []
var _character_motion_bounds := AABB()
var _framing_calibrating: bool = true
var _walking: bool = true
var _walk_time: float = 0.0
var _yaw_degrees: float = 0.0
var _dragging: bool = false
var _drag_offset := Vector2i.ZERO

var _toon_shader: Shader
var _outline_material: ShaderMaterial
var _materials: Dictionary = {}


func _ready() -> void:
	_configure_desktop_window()
	_create_shaders()
	_build_world()
	_build_skeleton()
	_build_fox_blockout()
	_build_controls_overlay()
	_set_mouse_passthrough()
	_apply_walk_pose()
	await _calibrate_camera_framing()
	_update_status()
	_print_diagnostics()
	if "--run-poc-checks" in OS.get_cmdline_user_args():
		_run_poc_checks.call_deferred()


func _process(delta: float) -> void:
	if _dragging and not Input.is_mouse_button_pressed(MOUSE_BUTTON_LEFT):
		_dragging = false
	if _framing_calibrating:
		return
	var turn_axis: float = Input.get_axis("ui_left", "ui_right")
	if not is_zero_approx(turn_axis):
		_yaw_degrees = fposmod(_yaw_degrees + turn_axis * TURN_SPEED_DEGREES * delta, 360.0)
	if _walking:
		_walk_time = fmod(_walk_time + delta, WALK_DURATION_SECONDS)
	_apply_walk_pose()
	_model_root.rotation_degrees.y = _yaw_degrees
	_update_status()


func _input(event: InputEvent) -> void:
	if event is InputEventKey and event.pressed and not event.echo:
		match event.keycode:
			KEY_ESCAPE:
				get_tree().quit()
			KEY_SPACE:
				_walking = not _walking
				if not _walking:
					_walk_time = 0.0
					_apply_walk_pose()
			KEY_1:
				_set_orientation("front")
			KEY_2:
				_set_orientation("front_3q_right")
			KEY_3:
				_set_orientation("side_right")
			KEY_4:
				_set_orientation("back_3q_right")
			KEY_5:
				_set_orientation("back")
		return

	if event is InputEventMouseButton and event.button_index == MOUSE_BUTTON_LEFT:
		_dragging = event.pressed
		if event.pressed:
			_drag_offset = DisplayServer.mouse_get_position() - get_window().position
		return

	if event is InputEventMouseMotion and _dragging:
		get_window().position = DisplayServer.mouse_get_position() - _drag_offset


func _configure_desktop_window() -> void:
	get_viewport().transparent_bg = true
	var window := get_window()
	window.transparent = true
	window.borderless = true
	window.always_on_top = true


func _build_world() -> void:
	_model_root = Node3D.new()
	_model_root.name = "PetModel3D"
	add_child(_model_root)

	_camera = Camera3D.new()
	_camera.name = "OrthographicCamera"
	_camera.projection = Camera3D.PROJECTION_ORTHOGONAL
	_camera.size = 5.7
	_camera.position = Vector3(0.0, 2.45, 8.0)
	add_child(_camera)
	_camera.look_at(Vector3(0.0, 2.35, 0.0), Vector3.UP)
	_camera.current = true

	var key_light := DirectionalLight3D.new()
	key_light.name = "ToonKeyLight"
	key_light.rotation_degrees = Vector3(-35.0, -28.0, 0.0)
	key_light.light_energy = 1.15
	key_light.shadow_enabled = false
	add_child(key_light)

	var fill_light := DirectionalLight3D.new()
	fill_light.name = "ToonFillLight"
	fill_light.rotation_degrees = Vector3(25.0, 145.0, 0.0)
	fill_light.light_energy = 0.35
	fill_light.shadow_enabled = false
	add_child(fill_light)


func _build_skeleton() -> void:
	_skeleton = Skeleton3D.new()
	_skeleton.name = "Skeleton3D"
	_model_root.add_child(_skeleton)

	_add_bone("TorsoBone", "", Vector3(0.0, 2.55, 0.0))
	_add_bone("HeadBone", "TorsoBone", Vector3(0.0, 1.15, 0.0))
	_add_bone("LeftUpperArmBone", "TorsoBone", Vector3(-0.68, 0.72, 0.0))
	_add_bone("LeftLowerArmBone", "LeftUpperArmBone", Vector3(0.0, -0.78, 0.0))
	_add_bone("LeftHandBone", "LeftLowerArmBone", Vector3(0.0, -0.66, 0.0))
	_add_bone("RightUpperArmBone", "TorsoBone", Vector3(0.68, 0.72, 0.0))
	_add_bone("RightLowerArmBone", "RightUpperArmBone", Vector3(0.0, -0.78, 0.0))
	_add_bone("RightHandBone", "RightLowerArmBone", Vector3(0.0, -0.66, 0.0))
	_add_bone("LeftUpperLegBone", "TorsoBone", Vector3(-0.32, -0.68, 0.0))
	_add_bone("LeftLowerLegBone", "LeftUpperLegBone", Vector3(0.0, -0.94, 0.0))
	_add_bone("LeftFootBone", "LeftLowerLegBone", Vector3(0.0, -0.86, 0.0))
	_add_bone("RightUpperLegBone", "TorsoBone", Vector3(0.32, -0.68, 0.0))
	_add_bone("RightLowerLegBone", "RightUpperLegBone", Vector3(0.0, -0.94, 0.0))
	_add_bone("RightFootBone", "RightLowerLegBone", Vector3(0.0, -0.86, 0.0))
	_add_bone("TailBone", "TorsoBone", Vector3(0.0, -0.42, -0.34))


func _add_bone(bone_name: String, parent_name: String, rest_position: Vector3) -> void:
	var bone_index: int = _skeleton.get_bone_count()
	_skeleton.add_bone(bone_name)
	_bones[bone_name] = bone_index
	if not parent_name.is_empty():
		_skeleton.set_bone_parent(bone_index, int(_bones[parent_name]))
	_skeleton.set_bone_rest(bone_index, Transform3D(Basis.IDENTITY, rest_position))


func _build_fox_blockout() -> void:
	var fur := Color("d96b32")
	var cream := Color("f6d7a7")
	var hoodie := Color("246b86")
	var accent := Color("55d6d1")
	var shorts := Color("25314d")
	var dark := Color("151923")
	var eye := Color("a8f3f2")

	_add_part("Torso", "TorsoBone", _capsule(0.56, 1.55), Vector3.ZERO, Vector3.ZERO, hoodie)
	_add_part("ChestAccent", "TorsoBone", _box(Vector3(0.55, 0.12, 0.08)), Vector3(0.0, 0.25, 0.52), Vector3(0.0, 0.0, 45.0), accent)
	_add_part("Head", "HeadBone", _sphere(0.73, 1.34), Vector3(0.0, 0.25, 0.0), Vector3.ZERO, fur)
	_add_part("Muzzle", "HeadBone", _sphere(0.39, 0.52), Vector3(0.0, -0.02, 0.58), Vector3(90.0, 0.0, 0.0), cream)
	_add_part("LeftEar", "HeadBone", _cone(0.25, 0.72), Vector3(-0.38, 0.88, 0.0), Vector3(0.0, 0.0, -8.0), fur)
	_add_part("RightEar", "HeadBone", _cone(0.25, 0.72), Vector3(0.38, 0.88, 0.0), Vector3(0.0, 0.0, 8.0), fur)
	_add_part("LeftEye", "HeadBone", _sphere(0.15, 0.28), Vector3(-0.24, 0.28, 0.62), Vector3.ZERO, eye)
	_add_part("RightEye", "HeadBone", _sphere(0.15, 0.28), Vector3(0.24, 0.28, 0.62), Vector3.ZERO, eye)
	_add_part("LeftPupil", "HeadBone", _sphere(0.075, 0.14), Vector3(-0.24, 0.28, 0.74), Vector3.ZERO, dark)
	_add_part("RightPupil", "HeadBone", _sphere(0.075, 0.14), Vector3(0.24, 0.28, 0.74), Vector3.ZERO, dark)
	_add_part("Nose", "HeadBone", _sphere(0.13, 0.19), Vector3(0.0, -0.05, 0.82), Vector3.ZERO, dark)

	_add_part("LeftUpperArm", "LeftUpperArmBone", _capsule(0.18, 0.88), Vector3(0.0, -0.39, 0.0), Vector3.ZERO, hoodie)
	_add_part("LeftLowerArm", "LeftLowerArmBone", _capsule(0.16, 0.76), Vector3(0.0, -0.33, 0.0), Vector3.ZERO, fur)
	_add_part("LeftHand", "LeftHandBone", _sphere(0.22, 0.38), Vector3(0.0, -0.17, 0.0), Vector3.ZERO, cream)
	_add_part("RightUpperArm", "RightUpperArmBone", _capsule(0.18, 0.88), Vector3(0.0, -0.39, 0.0), Vector3.ZERO, hoodie)
	_add_part("RightLowerArm", "RightLowerArmBone", _capsule(0.16, 0.76), Vector3(0.0, -0.33, 0.0), Vector3.ZERO, fur)
	_add_part("RightHand", "RightHandBone", _sphere(0.22, 0.38), Vector3(0.0, -0.17, 0.0), Vector3.ZERO, cream)

	_add_part("LeftUpperLeg", "LeftUpperLegBone", _capsule(0.23, 1.05), Vector3(0.0, -0.46, 0.0), Vector3.ZERO, shorts)
	_add_part("LeftLowerLeg", "LeftLowerLegBone", _capsule(0.19, 0.94), Vector3(0.0, -0.41, 0.0), Vector3.ZERO, fur)
	_add_part("LeftFoot", "LeftFootBone", _box(Vector3(0.48, 0.30, 0.82)), Vector3(0.0, -0.12, 0.24), Vector3.ZERO, accent)
	_add_part("RightUpperLeg", "RightUpperLegBone", _capsule(0.23, 1.05), Vector3(0.0, -0.46, 0.0), Vector3.ZERO, shorts)
	_add_part("RightLowerLeg", "RightLowerLegBone", _capsule(0.19, 0.94), Vector3(0.0, -0.41, 0.0), Vector3.ZERO, fur)
	_add_part("RightFoot", "RightFootBone", _box(Vector3(0.48, 0.30, 0.82)), Vector3(0.0, -0.12, 0.24), Vector3.ZERO, accent)
	_add_part("Tail", "TailBone", _capsule(0.31, 1.35), Vector3(0.48, -0.46, -0.18), Vector3(58.0, 0.0, -42.0), fur)
	_add_part("TailTip", "TailBone", _capsule(0.25, 0.62), Vector3(0.89, -0.82, -0.36), Vector3(58.0, 0.0, -42.0), cream)


func _add_part(part_name: String, bone_name: String, mesh: PrimitiveMesh, local_position: Vector3, local_rotation_degrees: Vector3, color: Color) -> void:
	var attachment := BoneAttachment3D.new()
	attachment.name = part_name + "Attachment"
	attachment.bone_name = bone_name
	_skeleton.add_child(attachment)

	var local_basis := Basis.from_euler(Vector3(
		deg_to_rad(local_rotation_degrees.x),
		deg_to_rad(local_rotation_degrees.y),
		deg_to_rad(local_rotation_degrees.z)
	))
	var part_transform := Transform3D(local_basis, local_position)

	var outline := MeshInstance3D.new()
	outline.name = part_name + "Outline"
	outline.mesh = mesh
	outline.transform = part_transform
	outline.material_override = _outline_material
	outline.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	attachment.add_child(outline)

	var surface := MeshInstance3D.new()
	surface.name = part_name
	surface.mesh = mesh
	surface.transform = part_transform
	surface.material_override = _material_for_color(color)
	surface.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	attachment.add_child(surface)
	_visible_parts.append(surface)
	_part_count += 1


func _calibrate_camera_framing() -> void:
	var saved_walking := _walking
	var saved_walk_time := _walk_time
	var saved_yaw := _yaw_degrees
	var combined_bounds := AABB()
	var has_combined_bounds := false
	_sampled_motion_bounds.clear()
	_walking = true

	for orientation_id in VIEW_ANGLES:
		_yaw_degrees = float(VIEW_ANGLES[orientation_id])
		_model_root.rotation_degrees.y = _yaw_degrees
		for phase in [0.0, 0.125, 0.25, 0.375, 0.5, 0.625, 0.75, 0.875]:
			_walk_time = WALK_DURATION_SECONDS * float(phase)
			_apply_walk_pose()
			_skeleton.force_update_all_bone_transforms()
			await get_tree().process_frame
			var sample_bounds := _combined_visible_parts_aabb()
			_sampled_motion_bounds.append(sample_bounds)
			if not has_combined_bounds:
				combined_bounds = sample_bounds
				has_combined_bounds = true
			else:
				combined_bounds = combined_bounds.merge(sample_bounds)

	_character_motion_bounds = combined_bounds
	var viewport_size := get_viewport().get_visible_rect().size
	var aspect := viewport_size.x / maxf(viewport_size.y, 1.0)
	var content_height := combined_bounds.size.y
	var content_width_as_height := combined_bounds.size.x / maxf(aspect, 0.01)
	_camera.size = maxf(content_height, content_width_as_height) * FRAMING_SAFETY_FACTOR
	var ground_y := combined_bounds.position.y
	var ground_margin := _camera.size * GROUND_MARGIN_FACTOR
	var camera_center_y := ground_y - ground_margin + _camera.size * 0.5
	var camera_center_x := combined_bounds.position.x + combined_bounds.size.x * 0.5
	_camera.position = Vector3(camera_center_x, camera_center_y, 8.0)
	_camera.look_at(Vector3(camera_center_x, camera_center_y, 0.0), Vector3.UP)

	_walking = saved_walking
	_walk_time = saved_walk_time
	_yaw_degrees = saved_yaw
	_apply_walk_pose()
	_model_root.rotation_degrees.y = _yaw_degrees
	_skeleton.force_update_all_bone_transforms()
	_framing_calibrating = false


func _combined_visible_parts_aabb() -> AABB:
	var combined := AABB()
	var has_bounds := false
	for part in _visible_parts:
		if not part.visible:
			continue
		var part_bounds := _transformed_aabb(part.get_aabb(), part.global_transform)
		if not has_bounds:
			combined = part_bounds
			has_bounds = true
		else:
			combined = combined.merge(part_bounds)
	return combined


func _transformed_aabb(local_bounds: AABB, transform: Transform3D) -> AABB:
	var minimum := Vector3(INF, INF, INF)
	var maximum := Vector3(-INF, -INF, -INF)
	for x_side in [0.0, 1.0]:
		for y_side in [0.0, 1.0]:
			for z_side in [0.0, 1.0]:
				var local_point := local_bounds.position + Vector3(
					local_bounds.size.x * x_side,
					local_bounds.size.y * y_side,
					local_bounds.size.z * z_side
				)
				var world_point := transform * local_point
				minimum = minimum.min(world_point)
				maximum = maximum.max(world_point)
	return AABB(minimum, maximum - minimum)


func _create_shaders() -> void:
	_toon_shader = Shader.new()
	_toon_shader.code = """
shader_type spatial;
render_mode cull_back, depth_draw_opaque;
uniform vec4 base_color : source_color = vec4(1.0);
void fragment() {
	ALBEDO = base_color.rgb;
	ROUGHNESS = 0.82;
	EMISSION = base_color.rgb * 0.10;
}
void light() {
	float n_dot_l = max(dot(NORMAL, LIGHT), 0.0);
	float band = n_dot_l > 0.62 ? 1.0 : (n_dot_l > 0.22 ? 0.66 : 0.34);
	DIFFUSE_LIGHT += base_color.rgb * LIGHT_COLOR * band * ATTENUATION;
}
"""

	var outline_shader := Shader.new()
	outline_shader.code = """
shader_type spatial;
render_mode cull_front, unshaded;
uniform vec4 outline_color : source_color = vec4(0.035, 0.045, 0.065, 1.0);
uniform float outline_width = 0.025;
void vertex() {
	VERTEX += NORMAL * outline_width;
}
void fragment() {
	ALBEDO = outline_color.rgb;
}
"""
	_outline_material = ShaderMaterial.new()
	_outline_material.shader = outline_shader
	_outline_material.set_shader_parameter("outline_width", OUTLINE_WIDTH)


func _material_for_color(color: Color) -> ShaderMaterial:
	var key := color.to_html()
	if _materials.has(key):
		return _materials[key] as ShaderMaterial
	var material := ShaderMaterial.new()
	material.shader = _toon_shader
	material.set_shader_parameter("base_color", color)
	_materials[key] = material
	return material


func _capsule(radius: float, height: float) -> CapsuleMesh:
	var mesh := CapsuleMesh.new()
	mesh.radius = radius
	mesh.height = height
	mesh.radial_segments = 20
	mesh.rings = 8
	return mesh


func _sphere(radius: float, height: float) -> SphereMesh:
	var mesh := SphereMesh.new()
	mesh.radius = radius
	mesh.height = height
	mesh.radial_segments = 24
	mesh.rings = 12
	return mesh


func _box(size: Vector3) -> BoxMesh:
	var mesh := BoxMesh.new()
	mesh.size = size
	return mesh


func _cone(radius: float, height: float) -> CylinderMesh:
	var mesh := CylinderMesh.new()
	mesh.top_radius = 0.02
	mesh.bottom_radius = radius
	mesh.height = height
	mesh.radial_segments = 20
	mesh.rings = 4
	return mesh


func _apply_walk_pose() -> void:
	if _skeleton == null:
		return
	var phase := TAU * _walk_time / WALK_DURATION_SECONDS if _walking else 0.0
	var stride := sin(phase)
	var knee_left := maxf(0.0, -stride)
	var knee_right := maxf(0.0, stride)
	var bob := absf(sin(phase)) * 0.065 if _walking else 0.0

	_set_pose_position("TorsoBone", Vector3(0.0, bob, 0.0))
	_set_pose_rotation("TorsoBone", Vector3(0.0, 0.0, stride * 1.5))
	_set_pose_rotation("HeadBone", Vector3(0.0, 0.0, -stride * 1.2))
	_set_pose_rotation("LeftUpperArmBone", Vector3(-stride * 18.0, 0.0, 0.0))
	_set_pose_rotation("RightUpperArmBone", Vector3(stride * 18.0, 0.0, 0.0))
	_set_pose_rotation("LeftLowerArmBone", Vector3(-4.0 - knee_right * 8.0, 0.0, 0.0))
	_set_pose_rotation("RightLowerArmBone", Vector3(-4.0 - knee_left * 8.0, 0.0, 0.0))
	_set_pose_rotation("LeftUpperLegBone", Vector3(stride * 25.0, 0.0, 0.0))
	_set_pose_rotation("RightUpperLegBone", Vector3(-stride * 25.0, 0.0, 0.0))
	_set_pose_rotation("LeftLowerLegBone", Vector3(-knee_left * 28.0, 0.0, 0.0))
	_set_pose_rotation("RightLowerLegBone", Vector3(-knee_right * 28.0, 0.0, 0.0))
	_set_pose_rotation("LeftFootBone", Vector3(-stride * 10.0 + knee_left * 15.0, 0.0, 0.0))
	_set_pose_rotation("RightFootBone", Vector3(stride * 10.0 + knee_right * 15.0, 0.0, 0.0))
	_set_pose_rotation("TailBone", Vector3(0.0, -stride * 10.0, stride * 7.0))


func _set_pose_position(bone_name: String, offset: Vector3) -> void:
	_skeleton.set_bone_pose_position(int(_bones[bone_name]), offset)


func _set_pose_rotation(bone_name: String, degrees: Vector3) -> void:
	var radians := Vector3(deg_to_rad(degrees.x), deg_to_rad(degrees.y), deg_to_rad(degrees.z))
	_skeleton.set_bone_pose_rotation(int(_bones[bone_name]), Basis.from_euler(radians).get_rotation_quaternion())


func _set_orientation(orientation_id: String) -> void:
	if not VIEW_ANGLES.has(orientation_id):
		return
	_yaw_degrees = float(VIEW_ANGLES[orientation_id])


func _orientation_label() -> String:
	var normalized := fposmod(_yaw_degrees, 360.0)
	var best_name := "custom"
	var best_distance := INF
	for orientation_id in VIEW_ANGLES:
		var angle := float(VIEW_ANGLES[orientation_id])
		var distance := absf(wrapf(normalized - angle, -180.0, 180.0))
		if distance < best_distance:
			best_distance = distance
			best_name = orientation_id
	return best_name if best_distance < 1.0 else "custom %.1f deg" % normalized


func _build_controls_overlay() -> void:
	var layer := CanvasLayer.new()
	layer.name = "ControlsOverlay"
	add_child(layer)
	_status_label = Label.new()
	_status_label.name = "Status"
	_status_label.position = Vector2(14, 12)
	_status_label.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_status_label.add_theme_color_override("font_color", Color("e8f5ff"))
	_status_label.add_theme_color_override("font_shadow_color", Color(0.02, 0.03, 0.05, 0.95))
	_status_label.add_theme_constant_override("shadow_offset_x", 2)
	_status_label.add_theme_constant_override("shadow_offset_y", 2)
	layer.add_child(_status_label)


func _update_status() -> void:
	if _status_label == null:
		return
	_status_label.text = "3D TOON PET POC  |  %s  |  WALK %s\n1 Front  2 3/4R  3 SideR  4 Back3/4R  5 Back\nLeft/Right: continuous Y turn  |  Space: walk  |  Drag  |  Esc" % [
		_orientation_label(),
		"ON" if _walking else "OFF",
	]


func _set_mouse_passthrough() -> void:
	var interaction_hull := PackedVector2Array([
		Vector2(205, 55),
		Vector2(395, 55),
		Vector2(455, 170),
		Vector2(470, 430),
		Vector2(430, 645),
		Vector2(170, 645),
		Vector2(130, 430),
		Vector2(145, 170),
	])
	DisplayServer.window_set_mouse_passthrough(interaction_hull)


func _print_diagnostics() -> void:
	var window := get_window()
	print("Godot3DToonPetPOC _ready")
	print("transparency_available=", DisplayServer.has_feature(DisplayServer.FEATURE_WINDOW_TRANSPARENCY))
	print("window.transparent=", window.transparent)
	print("viewport.transparent_bg=", get_viewport().transparent_bg)
	print("borderless=", window.borderless)
	print("always_on_top=", window.always_on_top)
	print("skeleton_bones=", _skeleton.get_bone_count())
	print("visible_mesh_parts=", _part_count)
	print("camera_projection=orthogonal")
	print("character_motion_aabb=", _character_motion_bounds)
	print("camera_orthographic_size=", _camera.size)
	print("camera_ground_anchor_y=", _character_motion_bounds.position.y)


func _run_poc_checks() -> void:
	var failures: Array[String] = []
	for bone_name in REQUIRED_BONES:
		if not _bones.has(bone_name):
			failures.append("missing bone: %s" % bone_name)
	if _skeleton.get_bone_count() != REQUIRED_BONES.size():
		failures.append("unexpected skeleton bone count")
	if _part_count < 20:
		failures.append("blockout did not create all expected visible parts")
	if _camera.projection != Camera3D.PROJECTION_ORTHOGONAL:
		failures.append("camera is not orthographic")
	if _sampled_motion_bounds.size() != VIEW_ANGLES.size() * 8:
		failures.append("framing did not sample all orientation/walk combinations")
	else:
		var half_height := _camera.size * 0.5
		var half_width := half_height * get_viewport().get_visible_rect().size.aspect()
		var camera_left := _camera.position.x - half_width
		var camera_right := _camera.position.x + half_width
		var camera_bottom := _camera.position.y - half_height
		var camera_top := _camera.position.y + half_height
		for sample_bounds in _sampled_motion_bounds:
			if sample_bounds.position.x < camera_left or sample_bounds.end.x > camera_right:
				failures.append("sampled character bounds exceed horizontal framing")
				break
			if sample_bounds.position.y < camera_bottom or sample_bounds.end.y > camera_top:
				failures.append("sampled character bounds exceed vertical framing")
				break

	for orientation_id in VIEW_ANGLES:
		_set_orientation(orientation_id)
		if not is_equal_approx(_yaw_degrees, float(VIEW_ANGLES[orientation_id])):
			failures.append("orientation did not set: %s" % orientation_id)

	_walking = true
	_walk_time = WALK_DURATION_SECONDS * 0.25
	_apply_walk_pose()
	var left_leg_rotation := _skeleton.get_bone_pose_rotation(int(_bones["LeftUpperLegBone"])).get_euler().x
	var right_leg_rotation := _skeleton.get_bone_pose_rotation(int(_bones["RightUpperLegBone"])).get_euler().x
	if is_zero_approx(left_leg_rotation) or is_zero_approx(right_leg_rotation) or signf(left_leg_rotation) == signf(right_leg_rotation):
		failures.append("walk legs are not alternating")
	_set_orientation("side_right")
	_walk_time = WALK_DURATION_SECONDS * 0.75
	_apply_walk_pose()
	if not is_equal_approx(_yaw_degrees, 90.0):
		failures.append("orientation changed while walk pose advanced")

	if failures.is_empty():
		print("poc_checks_passed=true")
		get_tree().quit()
		return
	for failure in failures:
		push_error("poc_check_failed: %s" % failure)
	get_tree().quit(1)
