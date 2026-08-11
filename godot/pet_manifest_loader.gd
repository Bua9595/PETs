## Shared, scene-agnostic loader for versioned production pet manifests.
## A future Godot scene supplies its existing Skeleton2D and optional PetRoot.
class_name ProductionPetManifestLoader
extends RefCounted

const SUPPORTED_SCHEMA_VERSION := 1


func load_into(manifest_path: String, skeleton: Skeleton2D, pet_root: Node2D = null) -> Dictionary:
	var manifest := _load_manifest(manifest_path)
	if manifest.is_empty():
		return {}
	if pet_root != null:
		pet_root.position = _vector2_from_value(manifest.get("ground_anchor", [0, 0]))
	var bones_by_name := _index_bones(skeleton)
	_apply_bone_layout(manifest.get("bones", []), bones_by_name)
	var parts_by_id: Dictionary = {}
	var missing_assets := 0
	for part_value in manifest.get("parts", []) as Array:
		var part := part_value as Dictionary
		var part_id := String(part.get("part_id", ""))
		var parent_bone := bones_by_name.get(String(part.get("parent_bone", ""))) as Bone2D
		var asset_path := _resolve_asset_path(manifest_path, String(part.get("asset_path", "")))
		if parent_bone == null or not FileAccess.file_exists(asset_path):
			missing_assets += 1
			push_error("Production pet part cannot be loaded: %s" % part_id)
			continue
		var texture := _load_texture(asset_path)
		if texture == null:
			missing_assets += 1
			push_error("Production pet part is not a loadable texture: %s" % part_id)
			continue
		var sprite := Sprite2D.new()
		sprite.name = part_id
		sprite.texture = texture
		sprite.texture_filter = CanvasItem.TEXTURE_FILTER_LINEAR_WITH_MIPMAPS
		sprite.texture_repeat = CanvasItem.TEXTURE_REPEAT_DISABLED
		sprite.centered = false
		sprite.position = _vector2_from_value(part.get("local_position", [0, 0])) - _vector2_from_value(part.get("pivot", [0, 0]))
		sprite.z_index = int(part.get("z_index", 0))
		sprite.visible = bool(part.get("visible", true))
		parent_bone.add_child(sprite)
		parts_by_id[part_id] = sprite
	print("manifest_assets_missing=", missing_assets)
	return {"manifest": manifest, "parts_by_id": parts_by_id, "bones_by_name": bones_by_name}


func _load_manifest(manifest_path: String) -> Dictionary:
	var json := JSON.new()
	if json.parse(FileAccess.get_file_as_string(manifest_path)) != OK or not json.data is Dictionary:
		push_error("Unable to parse production pet manifest: %s" % manifest_path)
		return {}
	var manifest := json.data as Dictionary
	var schema_version: Variant = manifest.get("schema_version")
	var schema_is_numeric := typeof(schema_version) == TYPE_INT or typeof(schema_version) == TYPE_FLOAT
	if not schema_is_numeric or float(schema_version) != float(SUPPORTED_SCHEMA_VERSION):
		push_error("Unsupported production pet manifest schema version: %s (supported: %d)" % [schema_version, SUPPORTED_SCHEMA_VERSION])
		return {}
	return manifest


func _index_bones(node: Node) -> Dictionary:
	var indexed: Dictionary = {}
	_index_bones_recursive(node, indexed)
	return indexed


func _index_bones_recursive(node: Node, indexed: Dictionary) -> void:
	if node is Bone2D:
		indexed[node.name] = node
	for child in node.get_children():
		_index_bones_recursive(child, indexed)


func _apply_bone_layout(bone_values: Variant, bones_by_name: Dictionary) -> void:
	for bone_value in bone_values as Array:
		var bone_data := bone_value as Dictionary
		var bone := bones_by_name.get(String(bone_data.get("bone_id", ""))) as Bone2D
		if bone == null:
			continue
		bone.position = _vector2_from_value(bone_data.get("rest_position", [0, 0]))
		bone.rotation_degrees = float(bone_data.get("rest_rotation_degrees", 0.0))
		bone.rest = bone.transform


func _resolve_asset_path(manifest_path: String, asset_path: String) -> String:
	if asset_path.begins_with("res://"):
		return asset_path
	return manifest_path.get_base_dir().path_join(asset_path).simplify_path()


func _load_texture(asset_path: String) -> Texture2D:
	var image := Image.new()
	if asset_path.get_extension().to_lower() == "svg":
		var svg_source := FileAccess.get_file_as_string(asset_path)
		if svg_source.is_empty() or image.load_svg_from_string(svg_source, 1.0) != OK:
			return null
	elif image.load(asset_path) != OK:
		return null
	if not image.has_mipmaps():
		var mipmap_error := image.generate_mipmaps()
		if mipmap_error != OK:
			push_warning("Unable to generate mipmaps for production pet texture: %s" % asset_path)
	return ImageTexture.create_from_image(image)


func _vector2_from_value(value: Variant) -> Vector2:
	var values := value as Array
	if values.size() != 2:
		return Vector2.ZERO
	return Vector2(float(values[0]), float(values[1]))
