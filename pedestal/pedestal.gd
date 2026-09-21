class_name Pedestal
extends StaticBody3D

signal occupancy_changed(removed: bool)

var block: AlphabetBlock
var lift_tween: Tween
var lift := 0.0
@onready var base_rest: Vector3 = $Base.position
@onready var base_scale: Vector3 = $Base.scale
@onready var top_rest: Vector3 = $Top.position


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
	block.set_highlighted(false)
	occupancy_changed.emit(false)
	block.play_sound()


func remove_block() -> void:
	if block:
		reset_lift()
		block.set_highlighted(false)
		block.pedestal = null
		block = null
		occupancy_changed.emit(true)


func raise_for_sound() -> void:
	reset_lift()
	if block:
		block.set_highlighted(true)
		lift_tween = create_tween()
		lift_tween.tween_method(_set_lift, 0.0, 0.35, 0.12).set_trans(Tween.TRANS_QUAD).set_ease(Tween.EASE_OUT)


func reset_lift() -> void:
	if lift_tween:
		lift_tween.kill()
	_set_lift(0.0)


func _set_lift(height: float) -> void:
	lift = height
	# Animate only the visible column/top/block. SnapPoint and colliders stay
	# at rest so Chuck can retrieve blocks even during a sound.
	$Base.position = base_rest + Vector3.UP * height * 0.5
	$Base.scale = base_scale + Vector3(0, height / 0.5, 0)
	$Top.position = top_rest + Vector3.UP * height
	if block:
		block.set_visual_lift(height)
