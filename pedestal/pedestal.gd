class_name Pedestal
extends StaticBody3D

var block: AlphabetBlock


func place(new_block: AlphabetBlock) -> void:
	if block:
		return
	block = new_block
	block.reparent($SnapPoint, false)
	block.position = Vector3.ZERO
	block.rotation = Vector3.ZERO
	block.is_carried = false
	block.pedestal = self
	block.collision_layer = 4
	block.collision_mask = 2


func remove_block() -> void:
	if block:
		block.pedestal = null
		block = null
