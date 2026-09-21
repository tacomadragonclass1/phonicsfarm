extends SceneTree
## Phoneme Village: the fetch-the-sound round, its board refresh, and the
## multi-level terrain Chuck has to walk to reach the raised letters.

var failures := 0
var scene: Node3D
var player: CharacterBody3D
var village: PhonemeVillage
var audio: AudioStreamPlayer
var heard: Array[String] = []
var prompts: Array[String] = []
var answers: Array = []


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


func teleport(point: Vector3) -> void:
	player.velocity = Vector3.ZERO
	player.global_position = point
	await frames(6)


## Stand next to a block and use the ordinary interaction, not a direct call:
## the village must react to a real pickup.
func fetch(block: AlphabetBlock) -> void:
	await teleport(block.global_position + Vector3(0.9, 0.02, 0.0))
	player.interact()
	await frames(2)


func find_block(letter: String) -> AlphabetBlock:
	for block in village.blocks:
		if block.letter == letter:
			return block
	return null


func positions() -> Dictionary:
	var out := {}
	for block in village.blocks:
		out[block.letter] = block.global_position
	return out


func run() -> void:
	scene = load("res://scenes/main.tscn").instantiate()
	root.add_child(scene)
	current_scene = scene
	player = scene.get_node("Player")
	village = scene.get_node("Environment/PhonemeVillage")
	audio = root.get_node("PhonemeAudio")
	audio.letter_started.connect(on_letter)
	village.prompted.connect(func(letter): prompts.append(letter))
	village.answered.connect(func(letter, correct): answers.append([letter, correct]))
	# Six real seconds per letter would make this suite unusable.
	village.celebration_delay = 0.25
	await frames(6)

	# --- entering the village starts a round ------------------------------
	check(village.state == PhonemeVillage.State.ASLEEP, "village sleeps until Chuck arrives")
	check(village.blocks.is_empty(), "no village blocks exist before the first round")
	var cvc_before: int = scene.get_node("Blocks").get_child_count()

	await teleport(village.to_global(Vector3(0, 0.02, 12)))
	await frames(6)
	check(village.state == PhonemeVillage.State.LISTENING, "walking in wakes the village")
	check(village.blocks.size() == 23, "a round scatters 23 blocks")
	var letters := {}
	for block in village.blocks:
		letters[block.letter] = true
	check(letters.size() == 23, "every village letter is on the board exactly once")
	# k duplicates c's recording; q and x are blends that open on the same /k/.
	check(not letters.has("k") and not letters.has("q") and not letters.has("x"),
		"k, q and x are kept out of the village so each sound has one answer")
	check(letters.has("c") and letters.has("z"), "the letters they collided with stay")
	check(scene.get_node("Blocks").get_child_count() == cvc_before,
		"CVC Land's alphabet row is untouched by a village round")

	# --- Annette asks with her sentence, then the block's own recording ----
	check(prompts.size() == 1, "Annette asks exactly one question on arrival")
	var target: String = village.target
	check(heard.size() >= 1 and heard[0] == "annette_find", "prompt opens with Annette's sentence")
	check(audio.pending_letters.has(target) or heard.has(target),
		"prompt then plays the target letter's own phoneme")

	# --- the wrong letter is corrected, not punished ----------------------
	var wrong_letter := "a" if target != "a" else "b"
	var wrong_block := find_block(wrong_letter)
	heard.clear()
	await fetch(wrong_block)
	await frames(4)
	check(player.carried_block == wrong_block, "a wrong letter stays in Chuck's hands")
	check(village.blocks.has(wrong_block), "a wrong letter is not removed from the board")
	check(answers.size() == 1 and answers[0] == [wrong_letter, false], "the wrong answer is reported")
	var queued: Array = audio.pending_letters.duplicate()
	queued.push_front(heard[0] if heard.size() else "")
	check(queued.has("wrong_chime"), "a wrong letter plays the soft chime")
	check(queued.has("annette_find"), "Annette repeats the question after a wrong letter")
	check(village.target == target, "the question does not change after a wrong letter")
	check(village.state == PhonemeVillage.State.LISTENING, "Chuck can keep trying")

	# put the wrong block back down
	player.interact()
	await frames(4)
	check(player.carried_block == null, "the wrong letter can be put down again")

	# --- the right letter is celebrated and vanishes ----------------------
	var right_block := find_block(target)
	var before_count: int = village.blocks.size()
	await fetch(right_block)
	check(village.state == PhonemeVillage.State.CELEBRATING, "the right letter starts the celebration")
	# The raise and flash run for about nine tenths of a second before the poof.
	for i in 180:
		await frames(1)
		if not is_instance_valid(right_block):
			break
	check(not is_instance_valid(right_block), "the right letter poofs away")
	check(player.carried_block == null, "Chuck's hands are empty again after the poof")
	check(village.blocks.size() == before_count - 1, "the found letter leaves the board")
	check(answers.back() == [target, true], "the right answer is reported")

	for i in 120:
		await frames(1)
		if prompts.size() > 1:
			break
	check(prompts.size() == 2, "Annette asks for the next letter after the pause")
	check(prompts[1] != prompts[0], "the next question is a different letter")

	# --- a found letter is never asked for again ---------------------------
	# Regression: `target` used to survive a correct answer, so walking out
	# during the celebration and back in re-asked for the block that had just
	# poofed -- a question with no answer left on the board.
	var found_letter: String = answers.back()[0]
	var right2 := find_block(village.target)
	await fetch(right2)
	await teleport(scene.get_node("Environment").to_global(Vector3(0, 0.02, 0)))
	for i in 180:
		await frames(1)
		if not is_instance_valid(right2):
			break
	var vanished: String = answers.back()[0]
	check(village.state == PhonemeVillage.State.ASLEEP, "leaving mid-celebration sleeps the village")
	await teleport(village.to_global(Vector3(0, 0.02, 12)))
	await frames(8)
	check(village.target != vanished, "the letter just found is not asked for again")
	check(village.target != found_letter, "nor is any earlier one")
	check(village.has_block(village.target), "the letter asked for is actually on the board")
	for letter in village.found:
		check(not village.queue.has(letter), "found letter '%s' is off the queue" % letter)

	# --- touching Annette repeats the sound on its own ---------------------
	for i in 300:
		await frames(1)
		if not audio.playing and audio.pending_letters.is_empty():
			break
	heard.clear()
	var asked: String = village.target
	await teleport(village.get_node("Annette").global_position)
	await frames(6)
	check(heard == [asked], "touching Annette replays just the phoneme, with no sentence")
	check(village.target == asked, "touching Annette does not change the question")

	# --- leaving pauses the round, returning repeats the same question ----
	var paused_target: String = village.target
	await teleport(scene.get_node("Environment").to_global(Vector3(0, 0.02, 0)))
	await frames(6)
	check(village.state == PhonemeVillage.State.ASLEEP, "walking out pauses the round")
	var prompt_count := prompts.size()
	await teleport(village.to_global(Vector3(0, 0.02, 12)))
	await frames(6)
	check(village.state == PhonemeVillage.State.LISTENING, "walking back in resumes the round")
	check(village.target == paused_target, "Chuck is asked the same letter he left on")
	check(prompts.size() == prompt_count + 1, "the repeat is spoken, not silent")

	# --- raised terrain -----------------------------------------------------
	var levels := {}
	for point in village.get_node("SpawnPoints").get_children():
		levels[snappedf(point.position.y, 0.5)] = true
	check(levels.has(0.0) and levels.has(1.0) and levels.has(2.0),
		"letters can be scattered across all three walkable levels")

	var foot := village.to_global(Vector3(5.5, 0.1, 7.0))
	await teleport(foot)
	Input.action_press("move_up")
	for i in 90:
		await frames(1)
	Input.action_release("move_up")
	await frames(10)
	var climbed: Vector3 = village.to_local(player.global_position)
	check(climbed.y > 0.8, "Chuck walks up the ramp onto the terrace")
	check(climbed.z < 3.0, "the climb actually crosses onto the terrace")

	# a block dropped up there stays up there
	var carried := find_block(village.queue[0] if village.queue.size() else "z")
	if carried:
		await teleport(carried.global_position + Vector3(0.9, 0.02, 0))
		player.interact()
		await frames(2)
		await teleport(village.to_global(Vector3(8.0, 1.1, -1.0)))
		player.interact()
		await frames(4)
		if not player.carried_block:
			check(village.to_local(carried.global_position).y > 0.8,
				"a block dropped on the terrace rests on the terrace, not the ground below")

	# --- a finished alphabet refreshes the board --------------------------
	await teleport(village.to_global(Vector3(0, 0.02, 12)))
	await frames(6)
	var old_positions := positions()
	village.queue.clear()
	village.next_prompt()
	await frames(6)
	check(village.blocks.size() == 23, "finishing the alphabet lays out a fresh 23 blocks")
	var moved := 0
	var fresh := positions()
	for letter in old_positions:
		if not fresh.has(letter) or fresh[letter].distance_to(old_positions[letter]) > 0.5:
			moved += 1
	check(moved >= 18, "the refreshed board puts the letters somewhere new (%d of 23 moved)" % moved)
	check(scene.get_node("Blocks").get_child_count() == cvc_before,
		"CVC Land still has its own 26 blocks after a refresh")

	print("VILLAGE RESULT: ", failures, " failures")
	quit(1 if failures else 0)
