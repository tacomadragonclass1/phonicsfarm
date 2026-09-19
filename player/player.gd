extends CharacterBody3D

@export var walk_speed := 3.2
@export var acceleration := 16.0
@export var interaction_distance := 1.65

var carried_block: AlphabetBlock
@onready var visual: Node3D = $Visual
@onready var carry_anchor: Marker3D = $Visual/CarryAnchor
@onready var camera: Camera3D = get_viewport().get_camera_3d()
@onready var animation: AnimationPlayer = $Visual/Model.find_child("AnimationPlayer", true, false)


func _ready() -> void:
	if animation:
		for animation_name in ["idle", "walk"]:
			if animation.has_animation(animation_name):
				animation.get_animation(animation_name).loop_mode = Animation.LOOP_LINEAR


func _physics_process(delta: float) -> void:
	var input := Input.get_vector("move_left", "move_right", "move_up", "move_down")
	var right := camera.global_basis.x
	var down := camera.global_basis.z
	right.y = 0.0
	down.y = 0.0
	var direction := right.normalized() * input.x + down.normalized() * input.y
	velocity.x = move_toward(velocity.x, direction.x * walk_speed, acceleration * delta)
	velocity.z = move_toward(velocity.z, direction.z * walk_speed, acceleration * delta)
	velocity.y = -1.0 if is_on_floor() else velocity.y - 20.0 * delta
	move_and_slide()
	if direction.length_squared() > 0.01:
		# The Kenney character faces local +Z.
		visual.rotation.y = lerp_angle(visual.rotation.y, atan2(direction.x, direction.z), 14.0 * delta)
	if animation:
		var next_animation := "walk" if direction.length_squared() > 0.01 else "idle"
		if animation.current_animation != next_animation:
			animation.play(next_animation, 0.15)
	if Input.is_action_just_pressed("interact"):
		interact()


func interact() -> void:
	if carried_block:
		var pedestal := nearest_empty_pedestal()
		if pedestal:
			pedestal.place(carried_block)
			carried_block = null
		else:
			drop_block()
		return
	var nearest: AlphabetBlock
	var nearest_distance := interaction_distance
	for node in get_tree().get_nodes_in_group("alphabet_blocks"):
		var block := node as AlphabetBlock
		if block.is_carried:
			continue
		var distance := horizontal_distance(block.global_position)
		if distance < nearest_distance and can_reach(block):
			nearest = block
			nearest_distance = distance
	if nearest:
		if nearest.pedestal:
			nearest.pedestal.remove_block()
		carried_block = nearest
		nearest.pick_up(carry_anchor)


func nearest_empty_pedestal() -> Pedestal:
	var nearest: Pedestal
	var nearest_distance := interaction_distance
	for node in get_tree().get_nodes_in_group("pedestals"):
		var pedestal := node as Pedestal
		var distance := horizontal_distance(pedestal.global_position)
		if not pedestal.block and distance < nearest_distance and can_reach(pedestal):
			nearest = pedestal
			nearest_distance = distance
	return nearest


func horizontal_distance(point: Vector3) -> float:
	return Vector2(global_position.x, global_position.z).distance_to(Vector2(point.x, point.z))


func can_reach(target: Node3D) -> bool:
	var query := PhysicsRayQueryParameters3D.create(
		global_position + Vector3.UP * 0.6, target.global_position + Vector3.UP * 0.4, 13)
	var hit := get_world_3d().direct_space_state.intersect_ray(query)
	if hit.is_empty() or hit.collider == target:
		return true
	return target is AlphabetBlock and hit.collider == target.pedestal


func drop_block() -> void:
	# Try nearby ground positions, starting in front. Never overlap another body
	# or put a block through a tree/wall. If surrounded, keep carrying it.
	var forward := visual.global_basis.z
	var shape := BoxShape3D.new()
	shape.size = Vector3(0.84, 0.76, 0.84)
	for angle in [0.0, 45.0, -45.0, 90.0, -90.0, 135.0, -135.0, 180.0]:
		var offset := forward.rotated(Vector3.UP, deg_to_rad(angle)) * 1.12
		var point := Vector3(global_position.x + offset.x, 0.02, global_position.z + offset.z)
		var query := PhysicsShapeQueryParameters3D.new()
		query.shape = shape
		query.transform = Transform3D(Basis.IDENTITY, point + Vector3.UP * 0.4)
		query.collision_mask = 15
		if not get_world_3d().direct_space_state.intersect_shape(query).is_empty():
			continue
		var ray := PhysicsRayQueryParameters3D.create(global_position + Vector3.UP * 0.4, point + Vector3.UP * 0.4, 13)
		if not get_world_3d().direct_space_state.intersect_ray(ray).is_empty():
			continue
		carried_block.put_on_ground(get_tree().current_scene.get_node("Blocks"), point)
		carried_block = null
		return
