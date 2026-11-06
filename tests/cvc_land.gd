extends SceneTree
## CVC Land, rebuilt: the build-a-word loop on the new layout.
##
## ⭐ This exists because every judgement about the rebuilt level so far came
## from still frames. A picture cannot tell you whether a block can be picked
## up, whether the pedestals read the word in the right order, or whether a
## letter is stranded behind another one.
##
## ⛔ The no-hidden-letter rule the village suite enforces is RETIRED here by
## decision -- a letter may sit off-camera, because walking out to collect it
## is the game. What replaces it is REACHABILITY: every block must be
## pickable from somewhere.

var failures := 0
var scene: Node3D
var player: CharacterBody3D
var lever: SoundLever
var pedestals: Array = []
## Where every block started, so a reachability sweep can put each one back
## instead of leaving the layout in a heap at Chuck's feet.
var homes := {}


func _initialize() -> void:
	call_deferred("run")


func check(condition: bool, description: String) -> void:
	if condition:
		print("PASS: ", description)
	else:
		push_error("FAIL: " + description)
		failures += 1


func frames(count: int = 3) -> void:
	for i in count:
		await physics_frame
		await process_frame


func teleport(point: Vector3) -> void:
	player.velocity = Vector3.ZERO
	player.global_position = point
	await frames(6)


func block_for(letter: String) -> AlphabetBlock:
	for node in scene.get_tree().get_nodes_in_group("alphabet_blocks"):
		var block := node as AlphabetBlock
		if block.letter == letter and not block.pedestal and not block.is_carried:
			return block
	return null


## Walk into a block the way a child does: Chuck picks loose blocks up on
## contact, with no button pressed.
func fetch(letter: String) -> AlphabetBlock:
	if player.carried_block:
		await release()
	var block := block_for(letter)
	if block == null:
		return null
	# ⛔ 0.80, not 0.95. `touch_pickup_distance` IS 0.95 and the comparison
	# is a strict `<`, so standing at exactly 0.95 lands on the boundary and
	# the pickup fires or does not depending on float noise -- which read as
	# "19 of 20 letters are unreachable" when the level was fine.
	# ⛔⛔ DO NOT CALL `pick_up_by_touch` HERE. Chuck already picks loose
	# blocks up on CONTACT from `_physics_process`, and that function has no
	# guard against being called while carrying -- it just overwrites
	# `carried_block`, leaving the previous block with `is_carried` still
	# true and orphaned forever. Calling it on top of the automatic pickup
	# stranded nineteen of twenty blocks and read as "the level is broken".
	#
	# ⛔ 0.80, not 0.95. `touch_pickup_distance` IS 0.95 and the comparison
	# is a strict `<`, so standing at exactly 0.95 is a coin flip.
	await teleport(block.global_position + Vector3(0.80, 0.02, 0.0))
	player.pick_up_by_touch()
	await frames(3)
	return block


## Put down whatever Chuck is holding and clear the player's own state.
##
## ⛔ Clearing `carried_block` alone is not enough: the block stays parented
## to the carry anchor with `is_carried` true, so the next `block_for` skips
## it and the sweep ends up holding a letter it never put back. That left
## Chuck carrying a `t` into the word test and every later fetch returned
## null.
## ⛔⛔ AND SWEEP UP ORPHANS. `pick_up_by_touch` has no guard against being
## called while already carrying -- it overwrites `carried_block` and leaves
## the previous block with `is_carried` true, parented to the carry anchor,
## invisible to every later `block_for`. Chuck picks up on CONTACT from
## _physics_process as well, so a teleport next to a block and an explicit
## call can both fire in the same frame. Nineteen of twenty blocks ended up
## stranded that way, which read as "the level is broken" when the level was
## fine and the harness was not.
##
## 👉 Worth noting beyond this test: the same hole exists in the game. It is
## unreachable today because touch input only fires the call when Chuck is
## empty-handed, but it is one caller away from stranding a letter.
func release(home: Vector3 = Vector3.INF) -> void:
	var block: AlphabetBlock = player.carried_block
	player.carried_block = null
	for node in scene.get_tree().get_nodes_in_group("alphabet_blocks"):
		var stray := node as AlphabetBlock
		if stray != block and stray.is_carried and not stray.pedestal:
			stray.put_on_ground(scene, homes.get(stray, stray.global_position))
	if block:
		# ⛔⛔ PUT IT BACK WHERE IT CAME FROM. Releasing at the block's
		# CURRENT position means releasing at Chuck's carry anchor -- so a
		# twenty-block sweep ends with twenty blocks stacked on one spot,
		# and every later fetch picks a letter at random out of the pile.
		# A test that checks reachability must not destroy the layout it is
		# checking.
		block.put_on_ground(scene, homes.get(block, block.global_position)
			if home == Vector3.INF else home)
	await frames(3)


func run() -> void:
	scene = load("res://scenes/cvc_land.tscn").instantiate()
	root.add_child(scene)
	await frames(10)
	player = scene.get_node("Player")
	lever = scene.get_node("SoundLever")
	for child in scene.get_node("Pedestals").get_children():
		pedestals.append(child)

	var blocks := scene.get_tree().get_nodes_in_group("alphabet_blocks")
	for node in blocks:
		homes[node] = (node as AlphabetBlock).global_position
	check(blocks.size() == 20, "twenty letters are out (%d)" % blocks.size())
	check(pedestals.size() == 3, "three pedestals")
	check(lever != null, "the bell is wired as the sound lever")

	# --- the art direction is actually IN the level ------------------------
	# ⛔⛔ The first export to /preview/ shipped without it. The shaders had
	# only ever been applied by the look-dev harness, so the published build
	# rendered raw StandardMaterial3D and looked exactly like the asset pack
	# the whole art pass was spent escaping. Nothing caught it but a
	# screenshot, so it is a test now.
	var painted := 0
	var textured := 0
	for node in scene.find_children("*", "MeshInstance3D", true, false):
		var mesh_instance := node as MeshInstance3D
		if mesh_instance.mesh == null:
			continue
		for surface in mesh_instance.mesh.get_surface_count():
			var source = mesh_instance.mesh.surface_get_material(surface)
			if source is StandardMaterial3D and source.albedo_texture != null:
				textured += 1
				var over = mesh_instance.get_surface_override_material(surface)
				if over is ShaderMaterial and over.next_pass is ShaderMaterial:
					painted += 1
	check(textured > 0 and painted == textured,
		"every textured surface carries the painted shader and the ink pass "
		+ "(%d/%d)" % [painted, textured])

	# --- every letter can actually be picked up ----------------------------
	# ⛔ COMPARE AGAINST WHAT WAS FETCHED, not against what was iterated.
	# Five letters are duplicated between the onset and ending zones, so
	# `block_for("t")` can legitimately hand back the OTHER t -- and testing
	# the iterated instance then reports a successful pickup as a failure.
	var unreachable: Array[String] = []
	for node in blocks:
		var block := node as AlphabetBlock
		var got := await fetch(block.letter)
		if got == null or player.carried_block != got:
			unreachable.append(block.letter)
		else:
			# ⛔ `put_on_ground`, not a `drop` that does not exist. Clearing
			# `carried_block` alone leaves `is_carried` true on the block
			# and the next fetch skips it, so the whole sweep reports
			# everything after the first letter as unreachable.
			await release()
	check(unreachable.is_empty(),
		"every letter is reachable %s" % [unreachable])

	await release()
	# --- build a word -------------------------------------------------------
	# "bad": b from the onset zone, a from the vowels, d from the endings.
	var spelled := ""
	for index in range(3):
		var letter := "bad"[index]
		var block := await fetch(letter)
		if block == null or player.carried_block != block:
			check(false, "could not fetch '%s'" % letter)
			continue
		var pedestal: Pedestal = pedestals[index]
		await teleport(pedestal.global_position + Vector3(0.0, 0.02, 1.0))
		player.interact()
		await frames(4)
		if pedestal.block:
			spelled += pedestal.block.letter
	check(spelled == "bad",
		"three letters placed left to right spell 'bad' (got '%s')" % spelled)

	# ⛔ The ORDER is the lever's, not the scene tree's: `pedestal_paths` has
	# to run screen-left to screen-right or the word comes out backwards.
	lever.activate()
	await frames(4)
	lever.show_word_result(false)
	await frames(2)
	check(lever.recognized_word == "bad",
		"the bell reads the row as a word (got '%s')" % lever.recognized_word)

	print("CVC LAND RESULT: %d failures" % failures)
	quit(1 if failures else 0)
