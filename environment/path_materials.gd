@tool
extends Node3D
## Warm, matte stepping stones. Runtime overrides survive nested Web exports.

func _ready() -> void:
	var index := 0
	for node in find_children("*", "MeshInstance3D", true, false):
		var mesh := node as MeshInstance3D
		var material := StandardMaterial3D.new()
		var shade := float(index % 4) * 0.018
		material.albedo_color = Color(0.64 + shade, 0.60 + shade, 0.48 + shade)
		material.roughness = 1.0
		material.metallic_specular = 0.1
		mesh.material_override = material
		index += 1
