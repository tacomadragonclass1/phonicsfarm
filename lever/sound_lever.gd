class_name SoundLever
extends StaticBody3D

const WordList = preload("res://assets/words/english_words.gd")

# Assign slots in screen-left to screen-right order in the level.
@export var pedestal_paths: Array[NodePath] = []
var pull_tween: Tween
var pulse_tween: Tween
var slots: Array[Pedestal] = []
var sounding_slots: Array[Pedestal] = []
var sounding_index := -1
var sequence_running := false
var recognized_word := ""
@onready var audio: AudioStreamPlayer = get_node("/root/PhonemeAudio")


func _ready() -> void:
	for path in pedestal_paths:
		var pedestal := get_node(path) as Pedestal
		slots.append(pedestal)
		pedestal.occupancy_changed.connect(_on_occupancy_changed)
	audio.letter_started.connect(_on_letter_started)
	audio.sequence_finished.connect(_on_sequence_finished)
	audio.sequence_cancelled.connect(_on_sequence_cancelled)


func activate() -> void:
	audio.stop_sequence()
	clear_feedback()
	sounding_slots.clear()
	sounding_index = -1
	var letters: Array[String] = []
	for pedestal in slots:
		if pedestal.block:
			sounding_slots.append(pedestal)
			letters.append(pedestal.block.letter)
	sequence_running = not letters.is_empty()
	audio.play_sequence(letters)
	if pull_tween:
		pull_tween.kill()
	pull_tween = create_tween()
	pull_tween.tween_property($Handle, "rotation:x", deg_to_rad(30.0), 0.1)
	pull_tween.tween_property($Handle, "rotation:x", deg_to_rad(-25.0), 0.3)
	if pulse_tween:
		pulse_tween.kill()
	$Pulse.visible = true
	$Pulse.scale = Vector3.ONE * 0.65
	$Pulse.transparency = 0.0
	pulse_tween = create_tween().set_parallel(true)
	pulse_tween.tween_property($Pulse, "scale", Vector3.ONE * 1.6, 0.45)
	pulse_tween.tween_property($Pulse, "transparency", 1.0, 0.45)
	pulse_tween.chain().tween_callback($Pulse.hide)


func _on_letter_started(_letter: String) -> void:
	if not sequence_running:
		return
	if sounding_index >= 0:
		sounding_slots[sounding_index].reset_lift()
	sounding_index += 1
	sounding_slots[sounding_index].raise_for_sound()


func _on_sequence_finished() -> void:
	if not sequence_running:
		return
	sequence_running = false
	for pedestal in slots:
		pedestal.reset_lift()
	show_word_result(true)


func _on_sequence_cancelled() -> void:
	if sequence_running:
		sequence_running = false
		clear_feedback()


func _on_occupancy_changed(removed: bool) -> void:
	if sequence_running:
		audio.stop_sequence()
	clear_feedback()
	if removed:
		show_word_result(false)


func clear_feedback() -> void:
	recognized_word = ""
	for pedestal in slots:
		pedestal.reset_lift()
		if pedestal.block:
			pedestal.block.set_highlighted(false)


func show_word_result(with_sparkles: bool) -> void:
	var word := ""
	for pedestal in slots:
		if pedestal.block:
			word += pedestal.block.letter
	var valid := WordList.is_word(word)
	recognized_word = word if valid else ""
	for pedestal in slots:
		if pedestal.block:
			pedestal.block.set_highlighted(valid)
			if valid and with_sparkles:
				pedestal.block.celebrate()
