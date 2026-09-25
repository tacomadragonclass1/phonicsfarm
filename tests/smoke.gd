extends SceneTree

var failures := 0
var scene: Node3D
var player: CharacterBody3D
var phoneme_audio: AudioStreamPlayer


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
	player.global_position = point
	player.velocity = Vector3.ZERO
	await frames()


func key(code: Key, pressed: bool) -> void:
	var event := InputEventKey.new()
	event.physical_keycode = code
	event.pressed = pressed
	Input.parse_input_event(event)


func interact_key() -> void:
	key(KEY_E, true)
	await frames()
	key(KEY_E, false)
	await frames()


func find_block(letter: String) -> AlphabetBlock:
	for node in get_nodes_in_group("alphabet_blocks"):
		var block := node as AlphabetBlock
		if block.letter == letter:
			return block
	return null


func touch(index: int, point: Vector2, pressed: bool) -> void:
	var event := InputEventScreenTouch.new()
	event.index = index
	event.position = root.get_final_transform() * point
	event.pressed = pressed
	Input.parse_input_event(event)


func drag(index: int, point: Vector2) -> void:
	var event := InputEventScreenDrag.new()
	event.index = index
	event.position = root.get_final_transform() * point
	Input.parse_input_event(event)


func check_letter_audio(letter: String, description: String) -> void:
	check(phoneme_audio.playing and phoneme_audio.stream.resource_path ==
		"res://assets/audio/phonemes/" + letter + ".wav", description)
	phoneme_audio.stop()


func run() -> void:
	scene = load("res://scenes/main.tscn").instantiate()
	root.add_child(scene)
	current_scene = scene
	player = scene.get_node("Player")
	phoneme_audio = root.get_node("PhonemeAudio")
	await frames(5)
	check(not phoneme_audio.playing, "no phoneme on scene startup")
	for letter in "abcdefghijklmnopqrstuvwxyz":
		find_block(letter).play_sound()
		await frames(1)
		check_letter_audio(letter, "playable phoneme for " + letter)
	# A rapid second interaction must replace the first sound.
	find_block("m").play_sound()
	find_block("s").play_sound()
	check_letter_audio("s", "latest interaction replaces previous phoneme")
	phoneme_audio.play_letter("")
	check(not phoneme_audio.playing, "empty letter is silent")
	check(get_nodes_in_group("alphabet_blocks").size() == 26, "26 blocks")
	check(get_nodes_in_group("pedestals").size() == 3, "exactly 3 pedestals")
	check(scene.get_node_or_null("Environment/River/Bridge") != null, "river bridge exists")
	var letters := ""
	for block in get_nodes_in_group("alphabet_blocks"):
		letters += block.letter
	check(letters == "abcdefghijklmnopqrstuvwxyz", "all lowercase letters are data")
	for entry in [[KEY_LEFT, "move_left"], [KEY_RIGHT, "move_right"], [KEY_UP, "move_up"], [KEY_DOWN, "move_down"]]:
		key(entry[0], true)
		await frames()
		check(Input.is_action_pressed(entry[1]), "arrow binding: " + entry[1])
		key(entry[0], false)
		await frames()

	# Physical keyboard events must move relative to the camera, then stop.
	var start := player.global_position
	key(KEY_D, true)
	await frames(25)
	key(KEY_D, false)
	await frames(15)
	check(player.global_position.x > start.x + 0.3 and player.global_position.z < start.z - 0.3, "camera-relative keyboard movement")
	check(Vector2(player.velocity.x, player.velocity.z).length() < 0.01, "release decelerates to rest")

	var block: AlphabetBlock = find_block("a")
	await teleport(block.global_position + scene.get_node("Blocks").global_basis * Vector3(0, 0.02, -0.8))
	check(player.carried_block == block and block.collision_layer == 0, "walking into a block picks it up and disables collision")
	check(block.get_parent() == player.carry_anchor, "carried block follows visible anchor")
	check_letter_audio("a", "contact pickup plays letter")
	var pedestal: Pedestal = scene.get_node("Pedestals/Pedestal2")
	await teleport(pedestal.global_position + Vector3(0, 0.02, 1.2))
	await interact_key()
	check(pedestal.block == block and player.carried_block == null, "block snaps onto empty pedestal")
	check(block.position == Vector3.ZERO and block.global_position.is_equal_approx(pedestal.get_node("SnapPoint").global_position), "exact snap location")
	check_letter_audio("a", "pedestal placement plays letter")
	pedestal.place(find_block("b"))
	check(not phoneme_audio.playing, "occupied pedestal rejects placement silently")
	await interact_key()
	check(player.carried_block == block and pedestal.block == null and block.pedestal == null, "retrieve block frees pedestal")
	check_letter_audio("a", "pedestal retrieval plays letter")
	await teleport(Vector3(0, 0.02, 3))
	await interact_key()
	check(player.carried_block == null and block.collision_layer == 4, "ground drop restores solid block")
	check(absf(block.global_position.y - 0.02) < 0.001, "ground drop stays above floor")
	check_letter_audio("a", "ground drop plays letter")
	await frames(10)
	check(player.carried_block == null, "a block just put down is not picked straight back up")
	# Stepping away and back re-arms it.
	await teleport(Vector3(0, 0.02, 6.5))
	await teleport(block.global_position + Vector3(0, 0.02, -0.8))
	check(player.carried_block == block, "the same block can be picked up again after walking away")
	await teleport(Vector3(0, 0.02, 3))
	await interact_key()

	# Repeated placement on each slot with different letters.
	for index in range(3):
		var next_block: AlphabetBlock = find_block(["b", "c", "d"][index])
		await teleport(next_block.global_position + scene.get_node("Blocks").global_basis * Vector3(0, 0.02, -0.8))
		var slot: Pedestal = scene.get_node("Pedestals/Pedestal" + str(index + 1))
		await teleport(slot.global_position + Vector3(0.8, 0.02, 0.8))
		await interact_key()
		check(slot.block == next_block, "independent occupancy in pedestal " + str(index + 1))

	# The whole screen is the controller: one finger walks, a second finger acts.
	await teleport(Vector3(0, 0.02, 3))
	var ui := scene.get_node("TouchControls/Controls")
	var anchor := Vector2(940, 180)
	touch(0, anchor, true)
	await frames(2)
	check(not Input.is_action_pressed("move_right"), "a planted finger on its own does not walk")
	drag(0, anchor + Vector2(140, 0))
	await frames(12)
	check(Input.get_action_strength("move_right") > 0.8, "dragging anywhere on the screen walks")
	touch(1, Vector2(160, 720), true)
	touch(1, Vector2(160, 720), false)
	await frames(6)
	check(Input.get_action_strength("move_right") > 0.8, "the walking finger survives a second finger")
	drag(0, anchor + Vector2(-140, 0))
	await frames(12)
	check(Input.get_action_strength("move_left") > 0.8, "the same finger can steer the other way")
	touch(0, anchor + Vector2(-140, 0), false)
	await frames(12)
	check(not Input.is_action_pressed("move_left"), "lifting the finger stops Chuck")

	# What the second finger is FOR: putting the carried block down. Checked by
	# its effect, not by the action flag, because the pulse is a frame long.
	var row_basis: Basis = scene.get_node("Blocks").global_basis
	var touch_block: AlphabetBlock = find_block("x")
	await teleport(touch_block.global_position + row_basis * Vector3(0, 0.02, -0.8))
	check(player.carried_block == touch_block, "contact pickup before the touch checks")
	await teleport(Vector3(0, 0.02, 3))
	touch(0, anchor, true)
	await frames(2)
	touch(1, Vector2(160, 720), true)
	touch(1, Vector2(160, 720), false)
	await frames(8)
	check(player.carried_block == null, "a second finger anywhere puts the block down")
	drag(0, anchor + Vector2(0, 60))
	touch(0, anchor + Vector2(0, 60), false)
	await frames(2)

	# A single quick tap that never moved does the same, so one hand is enough.
	var tap_block: AlphabetBlock = find_block("z")
	await teleport(tap_block.global_position + row_basis * Vector3(0, 0.02, -0.8))
	check(player.carried_block == tap_block, "contact pickup before the tap check")
	await teleport(Vector3(2.5, 0.02, 2.5))
	touch(0, anchor, true)
	touch(0, anchor, false)
	await frames(8)
	check(player.carried_block == null, "one quick tap with no drag acts")

	touch(0, anchor, true)
	drag(0, anchor + Vector2(140, 0))
	await frames()
	ui.notification(Node.NOTIFICATION_APPLICATION_FOCUS_OUT)
	await frames()
	check(not Input.is_action_pressed("move_right"), "focus loss clears the drag")
	touch(0, anchor + Vector2(140, 0), false)
	await frames()

	# Mouse follows the same pointer path, including dragging far past the range.
	var mouse := InputEventMouseButton.new()
	mouse.button_index = MOUSE_BUTTON_LEFT
	mouse.position = root.get_final_transform() * anchor
	mouse.pressed = true
	Input.parse_input_event(mouse)
	await frames()
	var motion := InputEventMouseMotion.new()
	motion.position = root.get_final_transform() * (anchor + Vector2(90, 0))
	Input.parse_input_event(motion)
	await frames()
	check(Input.is_action_pressed("move_right"), "mouse drag walks")
	motion.position = root.get_final_transform() * (anchor + Vector2(300, 0))
	Input.parse_input_event(motion)
	await frames()
	check(is_equal_approx(Input.get_action_strength("move_right"), 1.0), "a long drag clamps to full speed")
	mouse.position = motion.position
	mouse.pressed = false
	Input.parse_input_event(mouse)
	await frames()
	check(not Input.is_action_pressed("move_right"), "mouse release stops Chuck")
	key(KEY_D, true)
	touch(0, anchor, true)
	drag(0, anchor + Vector2(140, 0))
	await frames()
	touch(0, anchor + Vector2(140, 0), false)
	await frames()
	check(Input.is_action_pressed("move_right"), "touch release preserves held keyboard input")
	key(KEY_D, false)
	await frames()

	# Standard controller events, independent of vendor/model.
	var axis := InputEventJoypadMotion.new()
	axis.device = 0
	axis.axis = JOY_AXIS_LEFT_X
	axis.axis_value = -1.0
	Input.parse_input_event(axis)
	await frames()
	check(Input.is_action_pressed("move_left"), "controller left stick binding")
	axis.axis_value = 0.0
	Input.parse_input_event(axis)
	var button := InputEventJoypadButton.new()
	button.device = 0
	button.button_index = JOY_BUTTON_DPAD_UP
	button.pressed = true
	Input.parse_input_event(button)
	await frames()
	check(Input.is_action_pressed("move_up"), "controller D-pad binding")
	button.pressed = false
	Input.parse_input_event(button)
	button = InputEventJoypadButton.new()
	button.button_index = JOY_BUTTON_A
	button.pressed = true
	Input.parse_input_event(button)
	await frames()
	check(Input.is_action_pressed("interact"), "controller primary action binding")
	button.pressed = false
	Input.parse_input_event(button)

	# Sweep the player's actual collision shape against scene geometry.
	await teleport(Vector3(0, 0.02, 3))
	check(player.test_move(player.global_transform, Vector3(20, 0, 0)), "clearing boundary blocks movement")
	# The tree line has no invisible interior wall; only the board edge is sealed.
	var environment: Node3D = scene.get_node("Environment")
	await teleport(environment.to_global(Vector3(-12, 0.02, -2.6)))
	check(not player.test_move(player.global_transform, environment.global_basis * Vector3(-3.8, 0, 0)), "walk through a gap between trees")
	await teleport(Vector3(0, 0.02, 1.5))
	check(player.test_move(player.global_transform, Vector3(0, 0, -1.5)), "pedestal blocks movement")
	var ground_block: AlphabetBlock = scene.get_node("Blocks/Block_e")
	await teleport(ground_block.global_position + scene.get_node("Blocks").global_basis * Vector3(0, 0.02, -1.15))
	check(player.test_move(player.global_transform, scene.get_node("Blocks").global_basis * Vector3(0, 0, 1.15)), "ground block blocks movement")
	await teleport(ground_block.global_position + scene.get_node("Blocks").global_basis * Vector3(0, 0.02, -0.8))
	check(player.carried_block == ground_block, "contact pickup works on the alphabet rows")
	check_letter_audio("e", "contact pickup plays letter")
	await teleport(Vector3(2.5, 0.02, 2.5))
	var blockers: Array[StaticBody3D] = []
	for index in range(8):
		var obstacle := StaticBody3D.new()
		var collision := CollisionShape3D.new()
		var shape := BoxShape3D.new()
		shape.size = Vector3(0.8, 0.8, 0.8)
		collision.shape = shape
		obstacle.add_child(collision)
		scene.add_child(obstacle)
		var offset: Vector3 = player.visual.global_basis.z.rotated(Vector3.UP, index * PI / 4.0) * 1.12
		obstacle.global_position = player.global_position + offset + Vector3.UP * 0.4
		blockers.append(obstacle)
	await frames()
	await interact_key()
	check(player.carried_block == ground_block, "surrounded player keeps block instead of overlapping geometry")
	check(not phoneme_audio.playing, "blocked ground drop is silent")
	for obstacle in blockers:
		obstacle.queue_free()
	await frames()
	key(KEY_SPACE, true)
	await frames()
	key(KEY_SPACE, false)
	await frames()
	check(player.carried_block == null, "Space drops block after space becomes clear")
	check_letter_audio("e", "Space drop plays letter")
	var tree: Node3D = scene.get_node("Environment/Trees/Tree01")
	await teleport(tree.global_position + Vector3(1, 0.02, 0))
	check(player.test_move(player.global_transform, Vector3(-1, 0, 0)), "Kenney tree trunk blocks movement")
	print("SMOKE RESULT: ", failures, " failures")
	quit(1 if failures else 0)
