@tool
extends Node

## Tells Godot that a storybook GLB's baked texture is sRGB data.
##
## MEASURED, not guessed. The baked PNG inside every assets/storybook/*.glb
## holds exactly the sRGB bytes it should -- #93AC64 for meadow grass, checked
## byte for byte against the palette. But Godot's glTF import does not mark
## those embedded base-colour textures as sRGB, so the Compatibility renderer
## feeds them to the shader as if they were already linear. Everything comes
## out roughly a gamma too bright: in the browser the meadow measured
## (254, 255, 179) against the shipping game's (145, 190, 115), with the roof,
## the plaster and the block faces all clipping to white.
##
## Setting `albedo_texture_force_srgb` on the imported materials puts the
## conversion back. The same measurement afterwards reads (149, 203, 89).
##
## It lives on a CHILD node, and walks its parent, because three of the six
## storybook scenes already have a gameplay script on their root
## (alphabet_block.gd, player.gd, pedestal.gd) and none of those may be
## touched. Keeping the fix inside each asset's own scene means an asset
## carries its own correction wherever it is instanced.
##
## Materials are shared resources, so this is global and idempotent: whichever
## instance runs first fixes the material for every other instance too.


func _ready() -> void:
	fix(get_parent())


func fix(root: Node) -> void:
	if root == null:
		return
	for node in root.find_children("*", "MeshInstance3D", true, false):
		var mesh_instance := node as MeshInstance3D
		if mesh_instance.mesh == null:
			continue
		for surface in mesh_instance.mesh.get_surface_count():
			var material := mesh_instance.mesh.surface_get_material(surface)
			if material is StandardMaterial3D and material.albedo_texture:
				material.albedo_texture_force_srgb = true
