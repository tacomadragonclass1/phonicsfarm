@tool
extends Node3D
## Softens the Kenney Nature Kit's imported materials.
##
## Those GLBs carry their colour in `baseColorFactor` but ship with
## `metallicFactor: 1`, which reads as dark and shiny under the clearing's
## flat lighting. The river and bridge solve this with hand-written
## `surface_material_override`s; that does not scale to a village full of
## props, so this walks every mesh under the node instead.
##
## Materials are duplicated per surface, so fixing one prop never recolours
## another instance sharing the imported resource.

@export var roughness := 1.0
@export var specular := 0.15

# Shared natural colours tie the imported scatter to the painted wooden village.
# Flowers retain their identifying colours; foliage, rock and timber are quieter.
const PALETTE := {
	"grass": Color(0.37, 0.51, 0.32),
	"dirt": Color(0.53, 0.43, 0.32),
	"_defaultMat": Color(0.64, 0.62, 0.53),
	"stone": Color(0.60, 0.60, 0.53),
	"woodBark": Color(0.44, 0.30, 0.20),
	"wood": Color(0.63, 0.45, 0.28),
	"woodInner": Color(0.77, 0.64, 0.43),
}


func _ready() -> void:
	soften(self)


func soften(node: Node) -> void:
	for child in node.get_children():
		var mesh := child as MeshInstance3D
		if mesh:
			for surface in mesh.mesh.get_surface_count():
				var material := mesh.get_active_material(surface)
				if material is StandardMaterial3D and material.metallic > 0.0:
					var fixed: StandardMaterial3D = material.duplicate()
					fixed.metallic = 0.0
					fixed.roughness = roughness
					fixed.metallic_specular = specular
					if PALETTE.has(material.resource_name):
						fixed.albedo_color = PALETTE[material.resource_name]
					mesh.set_surface_override_material(surface, fixed)
		soften(child)
