class_name PhonemeVillage
extends Node3D
## Phoneme Village: Annette names a SOUND, Chuck fetches the letter that makes it.
##
## The village owns its own 26 blocks, scattered over the three walkable levels.
## CVC Land's alphabet row is untouched, so the lever game still works while a
## round is in progress.
##
## Annette speaks only the sentence wrappers. The phoneme in her prompt is the
## same human recording the block itself plays, so the child is matching one
## sound against itself rather than against a second voice's imitation.

const BLOCK_SCENE := preload("res://alphabet_block/alphabet_block.tscn")

## The village alphabet leaves out k, q and x, because the question
## "find the letter that says ___" has to have exactly one right answer.
##   k  -- c.wav and k.wav are the SAME recording (both /k/), so /k/ named two
##         letters and picking the other one was judged wrong for no reason
##         the child could hear. c stays, k goes.
##   q  -- /kw/, and x -- /ks/. Both are two sounds blended, and both open on
##         that same /k/, so they collide with c by ear.
## CVC Land still carries the full 26; this only affects the fetch game.
const LETTERS := "abcdefghijlmnoprstuvwyz"
const FLASH_GOLD := Color(1.0, 0.82, 0.16)
const FLASH_WHITE := Color(1.0, 1.0, 1.0)

signal round_started
signal prompted(letter: String)
signal answered(letter: String, correct: bool)
## Chuck walked in or out. The found-letters counter rides on this, so it is
## only on screen where it means something.
signal presence_changed(present: bool)

enum State {
	ASLEEP,      ## Chuck is not in the village
	LISTENING,   ## Annette has asked; waiting for a pickup
	CELEBRATING, ## correct letter: raising, flashing, poofing
	RESTING,     ## the pause after "Good job" before the next prompt
}

## The requested pause between "Good job" and the next letter.
@export var celebration_delay := 6.0
@export var raise_time := 0.3
@export var flash_interval := 0.14
@export var flash_count := 4
## Local offset the block is lifted to, measured from the player's CarryAnchor.
@export var raise_offset := Vector3(0.0, 0.62, -0.55)

var state := State.ASLEEP
## The letter currently being asked for. Empty means nothing is outstanding --
## it is cleared the moment a letter is found, so a round can never resume by
## asking again for a block that has already poofed away.
var target := ""
var queue: Array[String] = []
var found: Array[String] = []
var blocks: Array[AlphabetBlock] = []
var player: CharacterBody3D

@onready var annette: VillageGuide = $Annette
@onready var spawn_points: Node3D = $SpawnPoints
@onready var block_root: Node3D = $Blocks
@onready var audio: Node = get_node("/root/PhonemeAudio")


func _ready() -> void:
	$Trigger.body_entered.connect(_on_body_entered)
	$Trigger.body_exited.connect(_on_body_exited)
	$Annette/Touch.body_entered.connect(_on_annette_touched)


## Walking into Annette repeats the SOUND on its own, without her sentence.
## Silent while she is still speaking, so bumping her on the way in cannot
## chop the question in half.
func _on_annette_touched(body: Node3D) -> void:
	if body != player or state != State.LISTENING or target.is_empty():
		return
	if audio.playing or not audio.pending_letters.is_empty():
		return
	audio.play_sequence([target] as Array[String])


func _on_body_entered(body: Node3D) -> void:
	if not body.has_method("interact"):
		return
	player = body
	# Presence is about Chuck being HERE, not about the round, so it is
	# reported before the early return -- a round already under way (a capture
	# script starts one by hand) still puts the counter on screen.
	presence_changed.emit(true)
	if state != State.ASLEEP:
		return
	resume()


## Pick up wherever the round was left. Chuck may have walked out mid-question,
## mid-celebration, or during the pause between letters.
func resume() -> void:
	if blocks.is_empty():
		start_round()
	elif target.is_empty() or not has_block(target):
		# Nothing outstanding, or the outstanding letter is already off the
		# board. Move on instead of asking for something that is not there.
		next_prompt()
	else:
		speak_prompt()


func _on_body_exited(body: Node3D) -> void:
	if body != player:
		return
	state = State.ASLEEP
	audio.stop_sequence()
	# Nobody is watching: she tidies herself back onto her mark.
	annette.return_home()
	presence_changed.emit(false)


## Scatters a fresh set of 26 blocks and starts the alphabet over.
func start_round() -> void:
	annette.snap_home()
	refresh_board()
	queue = letter_list()
	queue.shuffle()
	found.clear()
	target = ""
	round_started.emit()
	next_prompt()


## Rebuilds the board. Every refresh puts the letters in different places.
func refresh_board() -> void:
	for block in blocks:
		if is_instance_valid(block):
			release(block)
			block.queue_free()
	blocks.clear()
	var markers := spawn_points.get_children()
	markers.shuffle()
	var letters := letter_list()
	for index in letters.size():
		var block: AlphabetBlock = BLOCK_SCENE.instantiate()
		block.letter = letters[index]
		block.home = block_root
		# A wrong letter being put down must NOT re-play its sound here: that
		# stop-and-play cut Annette off halfway through repeating the question.
		# CVC Land's blocks still sound on every drop.
		block.silent_drops = true
		block_root.add_child(block)
		block.global_position = (markers[index] as Node3D).global_position
		block.picked_up.connect(_on_block_picked_up)
		blocks.append(block)


## GDScript has no character iterator that yields Strings, so build one.
func letter_list() -> Array[String]:
	var out: Array[String] = []
	for index in LETTERS.length():
		out.append(LETTERS[index])
	return out


func next_prompt() -> void:
	# Never ask for a letter that is not on the board any more.
	while not queue.is_empty() and not has_block(queue[0]):
		queue.pop_front()
	if queue.is_empty():
		# Every letter found: new board, new positions, start again.
		start_round()
		return
	target = queue.pop_front()
	speak_prompt()


func find_block(letter: String) -> AlphabetBlock:
	for block in blocks:
		if is_instance_valid(block) and block.letter == letter:
			return block
	return null


func has_block(letter: String) -> bool:
	return find_block(letter) != null


func speak_prompt() -> void:
	state = State.LISTENING
	audio.play_sequence(["annette_find", target] as Array[String])
	# The quiet clue: she looks at the letter she is asking for. If she is
	# still walking home she turns once she arrives.
	var block := find_block(target)
	if block:
		annette.face(block.global_position)
	prompted.emit(target)


func _on_block_picked_up(block: AlphabetBlock) -> void:
	if state != State.LISTENING or not blocks.has(block):
		return
	var correct := block.letter == target
	if correct:
		blocks.erase(block)
		found.append(target)
		# Reported only once the letter is in `found`: the on-screen counter
		# reads that array, and would otherwise always be one behind.
		answered.emit(block.letter, true)
		# Cleared immediately: this letter must never be asked for again, not
		# on resume and not by a stale queue entry.
		target = ""
		celebrate(block)
	else:
		answered.emit(block.letter, false)
		# Not a buzzer: he hears what he grabbed, a soft two-note fall, then the
		# same question again. The wrong block stays in his hands to put down.
		audio.play_sequence([block.letter, "wrong_chime", "annette_find", target] as Array[String])
		# And the second clue gets stronger: she walks a few steps toward the
		# letter she actually asked for.
		var wanted := find_block(target)
		if wanted:
			annette.hint_toward(wanted.global_position)


func celebrate(block: AlphabetBlock) -> void:
	state = State.CELEBRATING
	var tween := create_tween()
	tween.tween_property(block, "position", raise_offset, raise_time)
	await tween.finished
	for index in flash_count:
		if not is_instance_valid(block):
			return
		block.set_face_color(FLASH_WHITE if index % 2 == 0 else FLASH_GOLD)
		await get_tree().create_timer(flash_interval).timeout
	if not is_instance_valid(block):
		return
	block.vanish()
	release(block)
	block.queue_free()
	audio.play_sequence(["annette_good"] as Array[String])
	# Any steps she took as a clue are undone before the next question, so a
	# long run of wrong answers cannot walk her across the village.
	annette.return_home()
	# Only advance the state if Chuck is still here. Leaving mid-celebration
	# puts the village back to sleep and that must not be overwritten.
	if state != State.CELEBRATING:
		return
	state = State.RESTING
	await get_tree().create_timer(celebration_delay).timeout
	if state == State.RESTING:
		next_prompt()


func release(block: AlphabetBlock) -> void:
	if player and player.carried_block == block:
		player.carried_block = null
