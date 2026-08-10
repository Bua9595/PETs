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
	var parts_by_id: Dictionary = {}
	for part_value in manifest.get("parts", []) as Array:
		var part := part_value as Dictionary
		var part_id := String(part.get("part_id", ""))
		var parent_bone := bones_by_name.get(String(part.get("parent_bone", ""))) as Bone2D
		var asset_path := _resolve_asset_path(manifest_path, String(part.get("asset_path", "")))
		if parent_bone == null or not FileAccess.file_exists(asset_path):
			push_error("Production pet part cannot be loaded: %s" % part_id)
			continue
		var texture := _load_texture(asset_path)
		if texture == null:
			push_error("Production pet part is not a loadable texture: %s" % part_id)
			continue
		var sprite := Sprite2D.new()
		sprite.name = part_id
		sprite.texture = texture
		sprite.centered = false
		sprite.position = _vector2_from_value(part.get("local_position", [0, 0])) - _vector2_from_value(part.get("pivot", [0, 0]))
		sprite.z_index = int(part.get("z_index", 0))
		sprite.visible = bool(part.get("visible", true))
		parent_bone.add_child(sprite)
		parts_by_id[part_id] = sprite
	return {"manifest": manifest, "parts_by_id": parts_by_id, "bones_by_name": bones_by_name}


func _load_manifest(manifest_path: String) -> Dictionary:
	var json := JSON.new()
	if json.parse(FileAccess.get_file_as_string(manifest_path)) != OK or not json.data is Dictionary:
		push_error("Unable to parse production pet manifest: %s" % manifest_path)
		return {}
	var manifest := json.data as Dictionary
	var schema_version: Variant = manifest.get("schema_version")
	if typeof(schema_version) != TYPE_INT or schema_version != SUPPORTED_SCHEMA_VERSION:
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


func _resolve_asset_path(manifest_path: String, asset_path: String) -> String:
	if asset_path.begins_with("res://"):
		return asset_path
	return manifest_path.get_base_dir().path_join(asset_path).simplify_path()


func _load_texture(asset_path: String) -> Texture2D:
	if asset_path.get_extension().to_lower() != "svg":
		return load(asset_path) as Texture2D
	var svg_source := FileAccess.get_file_as_string(asset_path)
	if svg_source.is_empty():
		return null
	var image := Image.new()
	if image.load_svg_from_string(svg_source, 1.0) != OK:
		return null
	return ImageTexture.create_from_image(image)


func _vector2_from_value(value: Variant) -> Vector2:
	var values := value as Array
	if values.size() != 2:
		return Vector2.ZERO
	return Vector2(float(values[0]), float(values[1]))
