extends SceneTree
## TEMPORARY layout aid. Prints Phoneme Village spawn positions that are
## standable, block-sized and NOT hidden behind any structure from the fixed
## camera angle. The permanent guarantee lives in tests/village.gd.

const LEVELS := {0.0: 24, 1.0: 8, 2.0: 4}
const MIN_SEPARATION := 2.6

var occluders: Array = []
var to_camera := Vector3.ZERO
var village: Node3D
var space: PhysicsDirectSpaceState3D


func _initialize() -> void:
	call_deferred("run")


func collect_occluders(node: Node) -> void:
	if node is MeshInstance3D:
		var mesh := node as MeshInstance3D
		var aabb := mesh.get_aabb()
		if aabb.size.length() > 0.0:
			occluders.append(mesh.global_transform * aabb)
	for child in node.get_children():
		collect_occluders(child)


## Slab test: does the segment from `from` along `dir` for `length` cross `box`?
func hits(box: AABB, from: Vector3, dir: Vector3, length: float) -> bool:
	var near := 0.0
	var far := length
	for axis in 3:
		var origin: float = from[axis]
		var delta: float = dir[axis]
		var low: float = box.position[axis]
		var high: float = box.position[axis] + box.size[axis]
		if absf(delta) < 0.00001:
			if origin < low or origin > high:
				return false
			continue
		var t1 := (low - origin) / delta
		var t2 := (high - origin) / delta
		near = maxf(near, minf(t1, t2))
		far = minf(far, maxf(t1, t2))
		if near > far:
			return false
	return near <= far


func visible_from_camera(point: Vector3) -> bool:
	for height in [0.14, 0.42, 0.7]:
		var from := point + Vector3(0, height, 0)
		for box in occluders:
			if hits(box, from, to_camera, 40.0):
				return false
	return true


func ground_at(x: float, z: float) -> Variant:
	var from := village.to_global(Vector3(x, 6.0, z))
	var query := PhysicsRayQueryParameters3D.create(from, from + Vector3.DOWN * 12.0, 1)
	var hit := space.intersect_ray(query)
	if hit.is_empty() or hit.normal.y < 0.98:
		return null
	return hit.position


func clear_for_block(point: Vector3) -> bool:
	var shape := BoxShape3D.new()
	shape.size = Vector3(0.9, 0.8, 0.9)
	var query := PhysicsShapeQueryParameters3D.new()
	query.shape = shape
	query.transform = Transform3D(Basis.IDENTITY, point + Vector3.UP * 0.45)
	query.collision_mask = 1
	return space.intersect_shape(query, 1).is_empty()


func standable(point: Vector3) -> bool:
	# Chuck has to be able to get alongside the block to touch it.
	var shape := CapsuleShape3D.new()
	shape.radius = 0.32
	shape.height = 1.2
	for angle in [0, 90, 180, 270]:
		var offset := Vector3(1.05, 0, 0).rotated(Vector3.UP, deg_to_rad(angle))
		var query := PhysicsShapeQueryParameters3D.new()
		query.shape = shape
		query.transform = Transform3D(Basis.IDENTITY, point + offset + Vector3.UP * 0.62)
		query.collision_mask = 1
		if space.intersect_shape(query, 1).is_empty():
			return true
	return false


func run() -> void:
	var scene: Node3D = load("res://scenes/main.tscn").instantiate()
	root.add_child(scene)
	current_scene = scene
	await process_frame
	await physics_frame
	await physics_frame
	village = scene.get_node("Environment/PhonemeVillage")
	space = village.get_world_3d().direct_space_state
	var camera: Camera3D = scene.get_node("Camera3D")
	to_camera = camera.global_basis.z.normalized()
	print("toward camera (village local): ", village.to_local(village.global_position + to_camera))
	for name in ["Buildings", "Props", "Terrain", "Trees", "Path", "Annette"]:
		collect_occluders(village.get_node(name))
	print("occluders: ", occluders.size())
	var cottage: Node3D = village.get_node("Buildings/Cottage1")
	var merged := AABB()
	for mesh in cottage.find_children("*", "MeshInstance3D", true, false):
		var box: AABB = (mesh as MeshInstance3D).global_transform * (mesh as MeshInstance3D).get_aabb()
		merged = box if merged.size == Vector3.ZERO else merged.merge(box)
	print("cottage world AABB: pos ", merged.position, " size ", merged.size)

	# Keep letters out of the houses' back yards and off the hearth.
	var keep_clear: Array = [[Vector2(-2.2, 12.6), 2.2], [Vector2(0.0, 1.5), 2.2]]
	for house in village.get_node("Buildings").get_children():
		keep_clear.append([Vector2((house as Node3D).position.x, (house as Node3D).position.z), 2.8])

	var candidates: Array = []
	var step := 0.8
	var x := -16.0
	while x <= 16.0:
		var z := -17.0
		while z <= 17.0:
			var point = ground_at(x, z)
			if point != null:
				var local: Vector3 = village.to_local(point)
				if Vector2(local.x, local.z).length() < 16.5 and clear_for_block(point) \
						and standable(point) and visible_from_camera(point):
					candidates.append(local)
			z += step
		x += step

	print("valid candidates: ", candidates.size())
	var chosen: Array = []
	for level in LEVELS:
		var pool: Array = []
		for local in candidates:
			if absf(local.y - level) < 0.4:
				pool.append(local)
		# Farthest-point selection: an even spread, and the same one every run.
		var picked: Array = []
		if not pool.is_empty():
			pool.sort_custom(func(a, b): return a.z > b.z if absf(a.z - b.z) > 0.01 else a.x < b.x)
			picked.append(pool[0])
			while picked.size() < LEVELS[level]:
				var best: Variant = null
				var best_distance := 0.0
				for local in pool:
					var nearest := INF
					for other in picked:
						nearest = minf(nearest, Vector2(local.x - other.x, local.z - other.z).length())
					if nearest > best_distance:
						best_distance = nearest
						best = local
				if best == null or best_distance < MIN_SEPARATION:
					break
				picked.append(best)
		print("level %.1f: %d candidates, picked %d" % [level, pool.size(), picked.size()])
		chosen.append_array(picked)
	chosen.sort_custom(func(a, b): return a.z > b.z)
	for local in chosen:
		print("SPAWN %.2f %.2f %.2f" % [local.x, snappedf(local.y, 0.5), local.z])
	quit()
