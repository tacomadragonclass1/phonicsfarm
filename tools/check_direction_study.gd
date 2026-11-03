extends SceneTree
func _initialize() -> void:
	call_deferred("go")
func go() -> void:
	var scene: Node3D = load("res://scenes/direction_study.tscn").instantiate()
	root.add_child(scene)
	current_scene = scene
	await process_frame
	await process_frame
	var ok := true
	for d in ["D1", "D2", "D3"]:
		var group := scene.get_node_or_null(d)
		if group == null:
			print("MISSING group ", d); ok = false; continue
		var block := group.get_node_or_null("Block1") as AlphabetBlock
		if block == null:
			print("MISSING block in ", d); ok = false; continue
		var visual: Node3D = block.get_node("Visual")
		var faces := ["Cube", "Front", "Right", "Back", "Left", "Top"]
		for f in faces:
			if not (visual.get_node_or_null(f) is MeshInstance3D):
				print("  ", d, " block missing ", f); ok = false
		if block.face_material == null:
			print("  ", d, " face material not duplicated"); ok = false
		if (block.get_node("Letters/Front") as Label3D).text != "c":
			print("  ", d, " letter wrong"); ok = false
		var aabb: AABB = (visual.get_node("Cube") as MeshInstance3D).get_aabb()
		print(d, " block body ", String.num(aabb.size.x, 3), " x ", String.num(aabb.size.y, 3))
	var tris := 0
	for node in scene.find_children("*", "MeshInstance3D", true, false):
		var m: Mesh = (node as MeshInstance3D).mesh
		if m:
			for s in m.get_surface_count():
				tris += int(m.surface_get_arrays(s)[Mesh.ARRAY_INDEX].size() / 3.0)
	print("study scene triangles: ", tris)
	print("direction study: ", "OK" if ok else "FAILED")
	quit(0 if ok else 1)
