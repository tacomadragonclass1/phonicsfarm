@tool
extends Node3D
## Keep the supplied UV atlas, but bring its mint foliage into the meadow palette.

func _ready() -> void:
	for node in find_children("*", "MeshInstance3D", true, false):
		var mesh := node as MeshInstance3D
		for surface in mesh.mesh.get_surface_count():
			var original := mesh.get_active_material(surface)
			if original is StandardMaterial3D:
				var material: StandardMaterial3D = original.duplicate()
				material.albedo_color = Color(0.78, 0.80, 0.58)
				material.roughness = 1.0
				material.metallic_specular = 0.1
				mesh.set_surface_override_material(surface, material)
