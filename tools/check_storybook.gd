extends SceneTree

## Headless check that the Painted Storybook slice is wired up correctly.
##
##   godot --headless --path . --script res://tools/check_storybook.gd
##
## Not in tests/ on purpose: the deploy workflow runs a fixed list of suites
## and this is an authoring aid for the visual redesign, not a guard on the
## shipping game. It checks the things that would fail SILENTLY -- a renamed
## node in a GLB, a missing animation, a block that no longer snaps to a
## pedestal -- rather than anything about how the assets look.

var failures: Array[String] = []


func _initialize() -> void:
	call_deferred("run")


func check(condition: bool, message: String) -> void:
	if condition:
		print("  ok    ", message)
	else:
		failures.append(message)
		print("  FAIL  ", message)


func run() -> void:
	var scene: Node3D = load("res://scenes/storybook_slice.tscn").instantiate()
	root.add_child(scene)
	current_scene = scene
	await process_frame
	await process_frame

	print("alphabet block")
	var block := scene.get_node("Blocks/Loose1") as AlphabetBlock
	check(block != null, "Loose1 is an AlphabetBlock")
	var visual: Node3D = block.get_node("Visual")
	var faces := ["Front", "Right", "Back", "Left", "Top"]
	for face in faces:
		check(visual.get_node_or_null(face) is MeshInstance3D,
			"Visual/%s survived the GLB import as a MeshInstance3D" % face)
	check(visual.get_node_or_null("Cube") is MeshInstance3D,
		"Visual/Cube exists and is excluded from face repainting")
	check(block.face_material != null,
		"alphabet_block.gd duplicated a face material off Visual/Front")
	var aabb: AABB = (visual.get_node("Cube") as MeshInstance3D).get_aabb()
	check(absf(aabb.size.x - 0.8) < 0.02 and absf(aabb.size.y - 0.8) < 0.02,
		"block body is still 0.8 x 0.8 (got %.3f x %.3f)" % [aabb.size.x, aabb.size.y])
	check(block.get_node("Letters").get_child_count() == 5,
		"five Label3D letters, still generated at runtime")
	block.letter = "q"
	check((block.get_node("Letters/Front") as Label3D).text == "q",
		"changing AlphabetBlock.letter still updates every face")

	print("chuck")
	var player := scene.get_node("Player")
	var animation: AnimationPlayer = player.get_node("Visual/Model").find_child(
		"AnimationPlayer", true, false)
	check(animation != null, "an AnimationPlayer is reachable under Visual/Model")
	if animation:
		check(animation.has_animation("idle"), "animation named exactly 'idle'")
		check(animation.has_animation("walk"), "animation named exactly 'walk'")
		check(animation.get_animation("idle").loop_mode == Animation.LOOP_LINEAR,
			"player.gd set the idle loop")
	check(player.get_node_or_null("Visual/CarryAnchor") != null,
		"CarryAnchor is where player.gd expects it")
	var capsule := (player.get_node("CollisionShape3D") as CollisionShape3D).shape
	check(capsule is CapsuleShape3D and absf(capsule.height - 1.16) < 0.001,
		"collision capsule is unchanged at 1.16 high")

	print("pedestals")
	for index in 3:
		var pedestal := scene.get_node("Pedestals/Pedestal%d" % (index + 1)) as Pedestal
		check(pedestal.block != null,
			"pedestal %d received its block through Pedestal.place()" % (index + 1))
		if pedestal.block:
			var top: float = pedestal.block.global_position.y
			check(absf(top - 0.62) < 0.001,
				"block %d rests at 0.62, the snap height (got %.3f)" % [index + 1, top])
		check(absf(pedestal.get_node("SnapPoint").position.y - 0.62) < 0.001,
			"pedestal %d SnapPoint is at 0.62" % (index + 1))
	var spelled := ""
	for index in 3:
		spelled += (scene.get_node("Pedestals/Pedestal%d" % (index + 1)) as Pedestal).block.letter
	check(spelled == "cat", "the pedestals spell 'cat' (got '%s')" % spelled)

	print("pedestal lift")
	var first := scene.get_node("Pedestals/Pedestal1") as Pedestal
	var rest_snap: float = first.get_node("SnapPoint").global_position.y
	first.raise_for_sound()
	await create_timer(0.25).timeout
	check(first.get_node("Base").scale.y > 1.1,
		"raising for sound stretches Base (scale.y = %.2f)" % first.get_node("Base").scale.y)
	check(absf(first.get_node("SnapPoint").global_position.y - rest_snap) < 0.001,
		"SnapPoint does NOT move during the lift, so retrieval stays reliable")
	first.reset_lift()

	print("budget")
	var total := 0
	var materials := {}
	for node in scene.find_children("*", "MeshInstance3D", true, false):
		var mesh: Mesh = (node as MeshInstance3D).mesh
		if not mesh:
			continue
		for surface in mesh.get_surface_count():
			total += int(mesh.surface_get_arrays(surface)[Mesh.ARRAY_INDEX].size() / 3.0)
			var material := mesh.surface_get_material(surface)
			if material:
				materials[material.get_rid()] = true
	print("  scene triangles: ", total, "   distinct mesh materials: ", materials.size())

	print("")
	if failures.is_empty():
		print("storybook slice: all checks passed")
		quit(0)
	else:
		print("storybook slice: %d FAILED" % failures.size())
		for message in failures:
			print("  - ", message)
		quit(1)
