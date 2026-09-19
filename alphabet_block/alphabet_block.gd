@tool
class_name AlphabetBlock
extends StaticBody3D

@export var letter := "a":
	set(value):
		letter = value.to_lower().left(1)
		if is_node_ready():
			update_letter()

var is_carried := false
var pedestal: Pedestal


func _ready() -> void:
	update_letter()


func update_letter() -> void:
	for label in $Letters.get_children():
		label.text = letter


func pick_up(anchor: Node3D) -> void:
	is_carried = true
	collision_layer = 0
	collision_mask = 0
	reparent(anchor, false)
	position = Vector3.ZERO
	rotation = Vector3.ZERO


func put_on_ground(parent: Node3D, point: Vector3) -> void:
	reparent(parent, false)
	global_position = point
	rotation = Vector3.ZERO
	is_carried = false
	collision_layer = 4
	collision_mask = 2
