extends SceneTree

var failures := 0
var scene: Node3D
var player: CharacterBody3D
var lever: SoundLever
var audio: AudioStreamPlayer
var heard: Array[String] = []
var started_at: Array[int] = []
var slots: Array[Pedestal] = []
var blocks: Array[AlphabetBlock] = []
var original_positions: Array[Vector3] = []


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


func on_letter(letter: String) -> void:
	heard.append(letter)
	started_at.append(Time.get_ticks_msec())


func wait_for_audio() -> void:
	for i in 300:
		await frames(1)
		if not audio.playing and audio.pending_letters.is_empty():
			return
	check(false, "audio sequence finishes within five seconds")


func press_interact() -> void:
	var event := InputEventKey.new()
	event.physical_keycode = KEY_E
	event.pressed = true
	Input.parse_input_event(event)
	await frames()
	event = InputEventKey.new()
	event.physical_keycode = KEY_E
	event.pressed = false
	Input.parse_input_event(event)
	await frames()


func set_slots(mask: int) -> void:
	for index in 3:
		if slots[index].block:
			slots[index].remove_block()
		blocks[index].put_on_ground(scene.get_node("Blocks"), original_positions[index])
		if mask & (1 << index):
			slots[index].place(blocks[index])
	audio.play_letter("")
	heard.clear()
	started_at.clear()


func run() -> void:
	scene = load("res://scenes/main.tscn").instantiate()
	root.add_child(scene)
	current_scene = scene
	player = scene.get_node("Player")
	lever = scene.get_node("SoundLever")
	audio = root.get_node("PhonemeAudio")
	audio.letter_started.connect(on_letter)
	for index in 3:
		slots.append(scene.get_node("Pedestals/Pedestal" + str(index + 1)))
		blocks.append(scene.get_node("Blocks/Block_" + ["q", "a", "t"][index]))
		original_positions.append(blocks[index].global_position)
	await frames()
	check(absf(slots[0].global_position.distance_to(slots[1].global_position) - 2.38) < 0.001
		and absf(slots[1].global_position.distance_to(slots[2].global_position) - 2.38) < 0.001,
		"pedestal center spacing reduced by 30 percent")
	var camera := scene.get_node("Camera3D") as Camera3D
	var screen_order := true
	var previous_x := camera.unproject_position(lever.global_position).x
	for slot in slots:
		var x := camera.unproject_position(slot.global_position).x
		screen_order = screen_order and x > previous_x
		previous_x = x
	check(screen_order, "lever and three slots ordered left to right on screen")
	var approach := lever.global_position + lever.global_basis.z * 1.2 + Vector3.UP * 0.02
	player.global_position = approach
	player.velocity = Vector3.ZERO
	await frames()
	check(player.nearest_sound_lever() == lever, "lever reachable from front")
	for mask in range(8):
		set_slots(mask)
		var expected: Array[String] = []
		for index in 3:
			if mask & (1 << index):
				expected.append(blocks[index].letter)
		await press_interact()
		await wait_for_audio()
		check(heard == expected, "occupancy %d plays only occupied slots left to right: %s" % [mask, str(expected)])
		var sequential := true
		for index in range(1, heard.size()):
			var duration: float = audio.SOUNDS[heard[index - 1]].get_length()
			sequential = sequential and started_at[index] - started_at[index - 1] >= duration * 1000.0 - 40.0
		check(sequential, "occupancy %d waits for each clip to finish" % mask)
		check(player.carried_block == null, "lever does not retrieve a pedestal block")

	set_slots(7)
	lever.activate()
	await frames()
	heard.clear()
	lever.activate()
	await wait_for_audio()
	check(heard == ["q", "a", "t"], "repeated pull restarts without stale queued sounds: " + str(heard))
	check(absf(lever.get_node("Handle").rotation.x - deg_to_rad(-25.0)) < 0.001, "lever handle returns after pull")

	lever.activate()
	await frames()
	heard.clear()
	var carried := scene.get_node("Blocks/Block_m") as AlphabetBlock
	carried.pick_up(player.carry_anchor)
	player.carried_block = carried
	await wait_for_audio()
	check(heard == ["m"], "block pickup cancels remaining lever sequence")
	heard.clear()
	await press_interact()
	await wait_for_audio()
	check(heard == ["q", "a", "t"] and player.carried_block == carried, "lever works while carrying without dropping the block")

	# The shared reach query must reject an intervening solid obstacle.
	var obstacle := StaticBody3D.new()
	var collider := CollisionShape3D.new()
	var shape := BoxShape3D.new()
	shape.size = Vector3(1.0, 1.0, 0.2)
	collider.shape = shape
	obstacle.add_child(collider)
	scene.add_child(obstacle)
	obstacle.global_transform = lever.global_transform
	obstacle.global_position += lever.global_basis.z * 0.65 + Vector3.UP * 0.5
	await frames()
	check(player.nearest_sound_lever() == null, "lever cannot be activated through an obstacle")
	obstacle.queue_free()
	player.global_position = Vector3(0, 0.02, 3)
	player.velocity = Vector3.ZERO
	await frames()
	check(player.nearest_sound_lever() == null, "lever cannot be activated out of range")
	print("LEVER RESULT: ", failures, " failures")
	quit(1 if failures else 0)
