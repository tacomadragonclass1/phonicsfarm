@tool
extends Node
class_name PaintedSurface

## Apply the painted shader and the ink outline to everything under a scene.
##
## ⛔⛔ THIS IS THE ART DIRECTION. Without this node in the scene the build
## renders raw StandardMaterial3D -- flat albedo at uniform roughness, no
## line, no surface marks -- which is the asset-pack look the whole pass was
## spent escaping. The first export to /preview/ shipped exactly that,
## because the shaders had only ever been applied by the look-dev harness and
## nobody had put them in a LEVEL.
##
## ⭐ Nothing is rebaked and no asset is modified. Materials are applied as
## surface OVERRIDES on each MeshInstance3D, so the GLBs, the atlases and the
## bakes are untouched and deleting this node restores the old look exactly.
##
## ⛔ Materials are SHARED resources. Overriding on the instance rather than
## writing to `mesh.surface_set_material` is what stops one prop recolouring
## every other instance of the same asset.

const PAINTED := preload("res://storybook/painted.gdshader")
const INK := preload("res://storybook/ink.gdshader")

## The settled look. See lookdev/DECISIONS.md for how each was chosen.
@export var grain_strength := 0.12
@export var grain_scale := 7.5
@export var grain_warm := 0.5
## In PIXELS. The hull is pushed in clip space, so one weight covers a 4 m
## cottage and a 5 cm berry alike -- a pen does not get thicker for bigger
## subjects.
@export var ink_width := 3.4
@export var outline := true
@export var enabled := true


func _ready() -> void:
	if enabled:
		apply(get_parent())


func apply(root: Node) -> void:
	if root == null:
		return
	for node in root.find_children("*", "MeshInstance3D", true, false):
		var mesh_instance := node as MeshInstance3D
		if mesh_instance.mesh == null:
			continue
		for surface in mesh_instance.mesh.get_surface_count():
			var source := mesh_instance.mesh.surface_get_material(surface)
			if source is not StandardMaterial3D:
				continue
			var standard := source as StandardMaterial3D
			if standard.albedo_texture == null:
				# ⛔ LEAVE THE FLAT MATERIALS ALONE. A material with no
				# texture is one of `painter.flat_material`'s -- the block's
				# letter faces, which are deliberately perfectly even cream
				# and are skipped by the bake for that reason. The die is the
				# one thing in the set that already worked; this has no
				# business relighting it.
				continue
			var material := ShaderMaterial.new()
			material.shader = PAINTED
			material.set_shader_parameter("albedo_tex", standard.albedo_texture)
			material.set_shader_parameter("grain_strength", grain_strength)
			material.set_shader_parameter("grain_scale", grain_scale)
			material.set_shader_parameter("grain_warm", grain_warm)
			if outline:
				# ⛔ next_pass, not a duplicated MeshInstance. A second node
				# would need its transform, visibility and culling kept in
				# step for every asset in the game; a second pass cannot
				# drift.
				var hull := ShaderMaterial.new()
				hull.shader = INK
				hull.set_shader_parameter("width_screen", ink_width)
				material.next_pass = hull
			mesh_instance.set_surface_override_material(surface, material)
