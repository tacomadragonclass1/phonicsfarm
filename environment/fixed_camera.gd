@tool
extends Camera3D

# Keep the isometric angle fixed while translating with Chuck through the level.
#
# The angle is described here rather than baked into the scene transform, so it
# can be tuned in one place: the camera's position and rotation are both derived
# from pitch/yaw/distance. Movement stays screen-relative on its own, because
# player.gd reads its walking axes off this camera's basis.

## Downward tilt. Shallower shows more of each object's sides; steeper tends
## toward a flat top-down map. 30 is the isometric compromise: enough of every
## top face to read a ramp as a slope rather than a painted rectangle, without
## flattening the world into a map.
@export_range(5.0, 80.0) var pitch_degrees := 30.0:
	set(value):
		pitch_degrees = value
		place()

## Rotation around the board. 45 looks straight down the board's axes and gives
## every box a single flat face; off 45 turns two faces toward the camera.
@export_range(-180.0, 180.0) var yaw_degrees := 30.0:
	set(value):
		yaw_degrees = value
		place()

## How far back along that angle the camera sits. Orthographic, so this does
## not change the framing -- only what can clip in front of it.
@export var distance := 26.0:
	set(value):
		distance = value
		place()

## Framing. Smaller is more zoomed in. The width fallback keeps a very wide
## window from cropping the top and bottom off the play area. Deliberately
## close: being in the world beats seeing every letter at once.
@export var zoom := 9.0:
	set(value):
		zoom = value
		fit_clearing()

@export var minimum_width := 13.0:
	set(value):
		minimum_width = value
		fit_clearing()

var target: Node3D
var follow_offset := Vector3(11.26, 13.0, 19.5)


func _ready() -> void:
	place()
	if Engine.is_editor_hint():
		return
	target = get_parent().get_node_or_null("Player")
	get_viewport().size_changed.connect(fit_clearing)
	fit_clearing()


func _process(_delta: float) -> void:
	if target:
		global_position = target.global_position + follow_offset


## Point the camera down the configured angle and back it off by `distance`.
func place() -> void:
	rotation = Vector3(deg_to_rad(-pitch_degrees), deg_to_rad(yaw_degrees), 0.0)
	# Sit opposite the view direction so the target lands in the middle.
	follow_offset = -(basis * Vector3.FORWARD) * distance
	if Engine.is_editor_hint() and is_inside_tree():
		position = follow_offset


func fit_clearing() -> void:
	if not is_inside_tree():
		return
	var viewport_size := get_viewport().get_visible_rect().size
	var aspect := viewport_size.x / maxf(viewport_size.y, 1.0)
	size = maxf(zoom, minimum_width / aspect)
