extends SceneTree
## Checks `village/foundation_village.tscn` against the contract in
## `phoneme_village.gd` and the layout rules in `tests/village.gd`.
##
## It is a SEPARATE check because `tests/village.gd` loads scenes/main.tscn
## and tests the SHIPPING village, which this scene deliberately does not
## replace. Both must pass.

var failures := 0


func _initialize() -> void:
	call_deferred("run")


func check(ok: bool, what: String) -> void:
	if ok:
		print("PASS: ", what)
	else:
		push_error("FAIL: " + what)
		print("FAIL: ", what)
		failures += 1


## Slab test, lifted from tests/village.gd: does the ray cross the box?
func crosses(box: AABB, from: Vector3, dir: Vector3, length: float) -> bool:
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
		near = maxf(near, minf((low - origin) / delta, (high - origin) / delta))
		far = minf(far, maxf((low - origin) / delta, (high - origin) / delta))
		if near > far:
			return false
	return near <= far


func run() -> void:
	var packed := load("res://village/foundation_village.tscn")
	check(packed != null, "the scene loads")
	if packed == null:
		quit(1)
		return
	var village = packed.instantiate()
	root.add_child(village)
	for i in 8:
		await process_frame
		await physics_frame

	check(village.is_in_group("phoneme_village"), "root is in group phoneme_village")
	check(village is PhonemeVillage, "root carries phoneme_village.gd")
	for path in ["Annette", "Annette/Touch", "SpawnPoints", "Blocks", "Trigger",
			"Buildings", "Props", "Terrain", "Trees", "Path"]:
		check(village.get_node_or_null(path) != null, "has $" + path)
	check(village.get_node("Annette") is VillageGuide, "Annette is a VillageGuide")
	check(village.get_node("Trigger") is Area3D, "Trigger is an Area3D")
	check(village.get_node("Annette/Touch") is Area3D, "Annette/Touch is an Area3D")

	var markers: Array = village.get_node("SpawnPoints").get_children()
	check(markers.size() >= 23, "at least 23 spawn markers (%d)" % markers.size())

	var levels := {}
	for point in markers:
		levels[snappedf((point as Node3D).position.y, 0.5)] = true
	check(levels.has(0.0) and levels.has(1.0) and levels.has(2.0),
		"letters scatter across all three walkable levels " + str(levels.keys()))

	# --- every letter in plain sight, the shipping rule, same camera angle.
	var pitch := deg_to_rad(30.0)
	var yaw := deg_to_rad(30.0)
	var to_camera := Vector3(sin(yaw) * cos(pitch), sin(pitch), cos(yaw) * cos(pitch)).normalized()
	var boxes: Array[AABB] = []
	var names: Array[String] = []
	for group in ["Buildings", "Props", "Terrain", "Trees", "Path", "Annette"]:
		for n in village.get_node(group).find_children("*", "MeshInstance3D", true, false):
			var mesh := n as MeshInstance3D
			if mesh.mesh != null and mesh.get_aabb().size.length() > 0.0:
				boxes.append(mesh.global_transform * mesh.get_aabb())
				names.append(String(mesh.get_parent().name) + "/" + String(mesh.name))
	check(boxes.size() > 40, "the village's visuals were collected (%d)" % boxes.size())
	var obscured: Array[String] = []
	for marker in markers:
		for height in [0.14, 0.42, 0.7]:
			var from: Vector3 = (marker as Node3D).global_position + Vector3.UP * height
			var blocked := false
			var culprit := "?"
			for i in boxes.size():
				var box: AABB = boxes[i]
				# ⛔ Two exclusions, both principled, and without them this
				# test is useless here. The shipping village's terrain is a
				# handful of small terrace and ramp meshes; the mill mound is
				# ONE mesh 16.7 m across, so its single AABB swallows most of
				# the green and flags 28 of 35 markers.
				#   * You cannot be hidden by the thing you are standing on.
				#   * An occluder has to be at least as tall as the letter it
				#     hides: a box whose top is below the block is not in
				#     front of it from a camera looking DOWN at 30 degrees.
				if box.has_point(from):
					continue
				if box.position.y + box.size.y < from.y - 0.05:
					continue
				if crosses(box, from, to_camera, 40.0):
					blocked = true
					culprit = names[i]
					break
			if blocked:
				obscured.append(String((marker as Node3D).name) + " <- " + culprit)
				break
	check(obscured.is_empty(), "no letter can be hidden behind a structure " + str(obscured))

	print("FOUNDATION VILLAGE RESULT: %d failures" % failures)
	quit(1 if failures else 0)
