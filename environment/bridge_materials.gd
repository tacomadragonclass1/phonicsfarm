@tool
extends StaticBody3D
## Paints the Kenney bridge in the clearing's palette, at runtime.
##
## These colours used to be `surface_material_override` entries written onto
## the GLB's mesh node inside river.tscn. That works in the editor and in a
## `godot --path .` run, but the overrides are LOST in an exported build,
## because the node they sit on lives inside a nested instanced scene
## (`Bridge/Model` is itself an instance). The sibling river_tile.tscn gets
## away with the same trick only because its override targets a direct child
## of the instance root.
##
## The symptom was invisible until the web export: the deck came back as the
## model's own "stone" material -- pale blue-grey at metallic 1 -- and read as
## a flat grey slab. Assigning the materials from a script on a plain node
## cannot be dropped that way.

## One colour per mesh surface, in the GLB's own order:
## 0 woodBark (posts), 1 wood (rails), 2 stone (deck planks and post caps).
@export var surface_colors: Array[Color] = [
	Color(0.34, 0.18, 0.09),
	Color(0.63, 0.39, 0.18),
	Color(0.76, 0.55, 0.31),
]


func _ready() -> void:
	paint()


func paint() -> void:
	for node in find_children("*", "MeshInstance3D", true, false):
		var mesh := node as MeshInstance3D
		if not mesh.mesh:
			continue
		for surface in mesh.mesh.get_surface_count():
			if surface >= surface_colors.size():
				continue
			var material := StandardMaterial3D.new()
			material.albedo_color = surface_colors[surface]
			material.roughness = 1.0
			mesh.set_surface_override_material(surface, material)
