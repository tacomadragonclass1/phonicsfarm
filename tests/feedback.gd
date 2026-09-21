extends "res://tests/lever.gd"

var originals: Dictionary = {}
var observed: Array[String] = []


func arrange(letters: Array[String]) -> void:
	audio.stop_sequence()
	if player.carried_block:
		var carried: AlphabetBlock = player.carried_block
		carried.put_on_ground(scene.get_node("Blocks"), originals[carried.letter])
		player.carried_block = null
	for slot in slots:
		if slot.block:
			var block: AlphabetBlock = slot.block
			slot.remove_block()
			block.put_on_ground(scene.get_node("Blocks"), originals[block.letter])
	for index in letters.size():
		if letters[index] != "":
			slots[index].place(find_letter(letters[index]))
	audio.stop_sequence()
	observed.clear()


func find_letter(letter: String) -> AlphabetBlock:
	for node in get_nodes_in_group("alphabet_blocks"):
		if node.letter == letter:
			return node
	return null


func observe_feedback(letter: String) -> void:
	if not lever.sequence_running:
		return
	observed.append(letter)
	var active: Pedestal = lever.sounding_slots[lever.sounding_index]
	check(active.block.letter == letter and active.block.is_highlighted,
		"gold block matches sounding letter " + letter)
	for slot in slots:
		if slot != active:
			check(is_zero_approx(slot.lift), "other pedestals are at rest during " + letter)


func check_rest() -> void:
	for slot in slots:
		check(is_zero_approx(slot.lift) and slot.get_node("Base").position == slot.base_rest
			and slot.get_node("Base").scale == slot.base_scale
			and slot.get_node("Top").position == slot.top_rest, "pedestal returns to exact rest geometry")
		check(slot.get_node("SnapPoint").position == Vector3(0, 0.62, 0)
			and slot.get_node("CollisionShape3D").position == Vector3(0, 0.31, 0),
			"snap point and collider retain their original height")
		if slot.block:
			check(slot.block.get_node("Visual").position == Vector3.ZERO
				and slot.block.get_node("Letters").position == Vector3.ZERO,
				"block visuals and lettering return to rest")


func run() -> void:
	scene = load("res://scenes/main.tscn").instantiate()
	root.add_child(scene)
	current_scene = scene
	player = scene.get_node("Player")
	lever = scene.get_node("SoundLever")
	audio = root.get_node("PhonemeAudio")
	audio.letter_started.connect(observe_feedback)
	for index in 3:
		slots.append(scene.get_node("Pedestals/Pedestal" + str(index + 1)))
	for block in get_nodes_in_group("alphabet_blocks"):
		originals[block.letter] = block.global_position
	await frames()
	for word in ["a", "i", "at", "it", "cat", "dog", "the", "mum", "qat"]:
		check(lever.WordList.is_word(word), "dictionary accepts " + word)
	for word in ["", "b", "q", "cs", "nhs", "kb", "dkl", "csc", "bobbie", "zqx", "ct"]:
		check(not lever.WordList.is_word(word), "dictionary rejects " + word)

	arrange(["c", "a", "t"])
	check(not find_letter("c").is_highlighted, "placing blocks waits for lever validation")
	lever.activate()
	await frames(10)
	check(slots[0].lift > 0.3 and slots[0].block.get_node("Visual").position.y > 0.3,
		"pedestal and block visibly rise together during sound")
	check(slots[0].block.position == Vector3.ZERO, "animated block physics origin stays on snap point")
	check(not find_letter("d").is_highlighted and
		find_letter("d").face_material.albedo_color == find_letter("d").default_face_color,
		"unrelated blocks keep default material color")
	check(find_letter("c").face_material != find_letter("a").face_material,
		"block face materials are independent")
	check(lever.get_node("Pulse").visible, "lever emits a visible pulse")
	await wait_for_audio()
	await frames()
	check(observed == ["c", "a", "t"], "visual feedback follows sound order")
	check(lever.recognized_word == "cat", "completed cat recognized")
	for slot in slots:
		check(slot.block.is_highlighted and slot.block.sparkle != null,
			"valid word stays gold and emits sparkles")
	check_rest()

	var removed := slots[0].block
	slots[0].remove_block()
	removed.pick_up(player.carry_anchor)
	player.carried_block = removed
	check(not removed.is_highlighted and removed.face_material.albedo_color == removed.default_face_color,
		"removed block immediately returns to default color")
	check(lever.recognized_word == "at" and slots[1].block.is_highlighted and slots[2].block.is_highlighted,
		"removing c rechecks remaining at and keeps those blocks gold")
	var second := slots[1].block
	slots[1].remove_block()
	second.put_on_ground(scene.get_node("Blocks"), originals["a"])
	check(lever.recognized_word == "" and not slots[2].block.is_highlighted,
		"removing a clears stale word color from remaining t")

	for letter in ["a", "i"]:
		arrange(["", letter, ""])
		lever.activate()
		await wait_for_audio()
		await frames()
		check(lever.recognized_word == letter and slots[1].block.is_highlighted,
			"single occupied middle slot recognizes " + letter)
	arrange(["a", "", "t"])
	lever.activate()
	await wait_for_audio()
	await frames()
	check(lever.recognized_word == "at" and observed == ["a", "t"], "gap is skipped for sounds and word recognition")
	check_rest()

	arrange(["z", "q", "x"])
	lever.activate()
	await wait_for_audio()
	await frames()
	check(lever.recognized_word == "", "invalid sequence is not recognized")
	for slot in slots:
		check(not slot.block.is_highlighted, "invalid sequence returns every block to default color")
	check_rest()

	# Retrieve a raised block through the actual player interaction path.
	arrange(["c", "a", "t"])
	player.global_position = slots[0].global_position + slots[0].global_basis.z * 1.2 + Vector3.UP * 0.02
	player.velocity = Vector3.ZERO
	await frames()
	lever.activate()
	await frames(9)
	player.interact()
	check(player.carried_block == find_letter("c") and not lever.sequence_running,
		"Chuck retrieves raised block and cancels sequence")
	check(not player.carried_block.is_highlighted, "retrieved block has no lingering gold")
	check_rest()
	await wait_for_audio()
	check(observed == ["c"], "cancelled sequence does not animate queued letters")

	arrange(["c", "a", "t"])
	lever.activate()
	await frames(8)
	lever.activate()
	await wait_for_audio()
	await frames()
	check(lever.recognized_word == "cat", "rapid restart still recognizes completed word")
	check_rest()
	arrange(["", "", ""])
	lever.activate()
	await frames()
	check(not lever.sequence_running and lever.recognized_word == "" and not audio.playing,
		"empty lever pull is silent with no stale word state")
	check_rest()
	print("FEEDBACK RESULT: ", failures, " failures")
	quit(1 if failures else 0)
