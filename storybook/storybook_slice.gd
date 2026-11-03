extends Node3D

## Sets the vertical slice up so it can be judged, not just looked at.
##
## Placing the three blocks through `Pedestal.place()` rather than by parking
## them at the right coordinates is deliberate: it runs the REAL interaction
## path -- reparenting to SnapPoint, the reciprocal block/pedestal references,
## the letter sound, the face-material duplication -- against the new block
## model. If the storybook block had broken any of that, it breaks here, on
## the first frame, instead of in a classroom.

## Spelled on the pedestals at startup, left to right.
@export var opening_word := "cat"


func _ready() -> void:
	var blocks: Node3D = $Blocks
	for index in mini(opening_word.length(), 3):
		var pedestal := get_node_or_null(
			"Pedestals/Pedestal%d" % (index + 1)) as Pedestal
		var block := blocks.get_node_or_null(
			"Placed%d" % (index + 1)) as AlphabetBlock
		if pedestal and block:
			block.letter = opening_word[index]
			pedestal.place(block)
