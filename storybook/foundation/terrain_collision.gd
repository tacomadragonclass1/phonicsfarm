@tool
extends Node

## Gives the foundation terrain real collision at load.
##
## The ground in scenes/main.tscn is a flat BoxShape3D. This one is not flat:
## the play area rolls over about 0.35 m with a maximum slope near 8 degrees,
## and `player.gd` walks it natively -- it is a CharacterBody3D with gravity,
## `drop_block` already raycasts DOWN for the drop point, and Phoneme Village
## has shipped raised terrain since September.
##
## `create_trimesh_collision()` rather than a HeightMapShape3D, deliberately:
## the mesh is already a regular grid so either would work, but the trimesh
## needs no height array to be kept in sync with the Blender build, and 13k
## triangles of STATIC concave shape is nothing to build at load.
##
## ⛔ The body it creates lands on collision LAYER 1, which is what the rest
## of the game expects of ground: `player.gd::ground_height()` raycasts on
## mask 1, and `can_reach()` uses mask 13, which includes it. That second one
## matters -- a rise of about half a metre inside the 1.65 m reach span would
## make a block unpickable, which is why the play area is kept gentle.


func _ready() -> void:
	for node in get_parent().find_children("*", "MeshInstance3D", true, false):
		var mesh_instance := node as MeshInstance3D
		if mesh_instance.mesh == null:
			continue
		if mesh_instance.get_node_or_null("_col") != null:
			continue
		var body := StaticBody3D.new()
		body.name = "_col"
		var shape := CollisionShape3D.new()
		shape.shape = mesh_instance.mesh.create_trimesh_shape()
		body.add_child(shape)
		mesh_instance.add_child(body)
