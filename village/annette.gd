class_name VillageGuide
extends Node3D

## Annette, who names a sound and then shows where to look.
##
## Two clues, both silent and both deliberately weak:
##   * she TURNS to face the letter she is asking for, every time she asks;
##   * on a wrong answer she WALKS four or five steps toward it.
## Neither points at the block outright. A child who has not noticed her can
## still hunt the whole village; a child who has noticed knows which way to go.
##
## She is not a physics body -- nothing collides with her and she collides with
## nothing -- so the walk is hand-rolled: step along the ground, stop short of
## the letter, and stop early if a cottage or tree trunk is in the way. She
## always comes back to her post between letters, so she cannot wander off.

## Metres travelled per "step". The model stands about 1.6 units tall at its
## scene scale, so this is a stride, not a stride-and-a-half.
@export var step_length := 0.55
## "Four or five steps": which one is picked per hint is random, so repeated
## wrong answers do not look mechanical.
@export var hint_steps_min := 4
@export var hint_steps_max := 5
@export var walk_speed := 1.9
@export var turn_speed := 7.0
## How close she is willing to get to the letter. She must never end up
## standing on the block she is asking for, or the clue hides the answer.
@export var standoff := 2.2
## Total distance she will stray from her post, however many wrong answers
## come in. Keeps her on the green and in shot.
@export var max_drift := 7.0

## Where she stands, and which way she looks, when nothing is going on.
## The village hangs off a 45-degree-rotated Environment node, so every yaw
## here is a GLOBAL yaw: mixing the two spaces points her 45 degrees wide.
var home_position: Vector3
var home_yaw := 0.0
## Where the current walk is headed. Only meaningful while `walking`.
var walk_target := Vector3.ZERO
var walking := false
## Walking home is allowed to finish on the mark; walking to a letter stops
## short of it. Tracked as a flag, because her Y changes as she climbs and the
## target vector alone cannot be compared reliably.
var going_home := false
## Distance left in the current walk. A hint is a fixed number of steps, not
## "however far the letter happens to be".
var budget := 0.0
## Yaw she settles on once she stops. While walking, the direction of travel
## wins, or she would stroll along sideways.
var resting_yaw := 0.0
var animation: AnimationPlayer

@onready var model: Node3D = $Model


func _ready() -> void:
	home_position = global_position
	home_yaw = global_rotation.y
	resting_yaw = home_yaw
	animation = model.find_child("AnimationPlayer", true, false)
	if animation:
		for animation_name in ["idle", "walk"]:
			if animation.has_animation(animation_name):
				animation.get_animation(animation_name).loop_mode = Animation.LOOP_LINEAR
		animation.play("idle")


func _physics_process(delta: float) -> void:
	if walking:
		_advance(delta)
	var wanted := resting_yaw
	if walking:
		var heading := walk_target - global_position
		heading.y = 0.0
		if heading.length_squared() > 0.0001:
			# The Kenney character faces its own local +Z.
			wanted = atan2(heading.x, heading.z)
	global_rotation.y = lerp_angle(global_rotation.y, wanted, turn_speed * delta)
	if animation:
		var next_animation := "walk" if walking else "idle"
		if animation.current_animation != next_animation:
			animation.play(next_animation, 0.2)


## Turn toward a point without moving. Called every time she asks a question.
## If she is mid-walk the turn is deferred until she arrives, so she does not
## moonwalk the last half metre.
func face(point: Vector3) -> void:
	var heading := point - global_position
	heading.y = 0.0
	if heading.length_squared() < 0.0001:
		return
	resting_yaw = atan2(heading.x, heading.z)


## The wrong-answer clue: four or five steps toward the letter she asked for.
func hint_toward(point: Vector3) -> void:
	var steps := randi_range(hint_steps_min, hint_steps_max)
	_walk_to(point, float(steps) * step_length)


## Back to her post, between letters. The walk home is not step-limited.
func return_home() -> void:
	_walk_to(home_position, INF)
	going_home = true
	resting_yaw = home_yaw


## Instantly back on her mark, no walk. For a fresh round and for tests that
## measure the static layout.
func snap_home() -> void:
	walking = false
	going_home = false
	budget = 0.0
	global_position = home_position
	resting_yaw = home_yaw
	global_rotation.y = home_yaw


func _walk_to(point: Vector3, distance: float) -> void:
	going_home = false
	walk_target = Vector3(point.x, global_position.y, point.z)
	budget = distance
	walking = true


func _advance(delta: float) -> void:
	var heading := walk_target - global_position
	heading.y = 0.0
	var remaining := heading.length()
	# Stop short of the letter itself, but walk right onto her home mark.
	var stop_short := 0.05 if going_home else standoff
	if remaining <= stop_short or budget <= 0.0:
		walking = false
		return
	var direction := heading / remaining
	if _blocked(direction):
		walking = false
		return
	var step := minf(walk_speed * delta, minf(budget, remaining - stop_short))
	var candidate := global_position + direction * step
	var ground := _ground_height(candidate)
	if is_nan(ground):
		# Nothing underfoot: the edge of the world, or a gap. Do not step off.
		walking = false
		return
	candidate.y = ground
	if not going_home and candidate.distance_to(home_position) > max_drift:
		walking = false
		return
	global_position = candidate
	budget -= step


## A cottage wall or tree trunk ahead. Their colliders are on layer 1, the
## same environment layer the ground uses, so this is a short feeler at
## chest height rather than at her feet.
func _blocked(direction: Vector3) -> bool:
	var from := global_position + Vector3.UP * 0.9
	var query := PhysicsRayQueryParameters3D.create(from, from + direction * 0.7, 1)
	return not get_world_3d().direct_space_state.intersect_ray(query).is_empty()


## The village has three levels, so her feet cannot assume Y = 0. Looks down
## from just above her current footing, the same way Chuck's drop test does.
## Returns NAN when there is no ground at all under that point.
func _ground_height(point: Vector3) -> float:
	var from := Vector3(point.x, global_position.y + 0.6, point.z)
	var query := PhysicsRayQueryParameters3D.create(from, from + Vector3.DOWN * 8.0, 1)
	var hit := get_world_3d().direct_space_state.intersect_ray(query)
	return hit.position.y if hit else NAN
