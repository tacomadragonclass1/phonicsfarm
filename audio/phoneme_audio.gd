extends AudioStreamPlayer

signal letter_started(letter: String)
signal sequence_finished
signal sequence_cancelled

var pending_letters: Array[String] = []
var sequence_active := false

# Explicit resource references keep every letter's recording in Web exports.
const SOUNDS := {
	"a": preload("res://assets/audio/phonemes/a.wav"),
	"b": preload("res://assets/audio/phonemes/b.wav"),
	"c": preload("res://assets/audio/phonemes/c.wav"),
	"d": preload("res://assets/audio/phonemes/d.wav"),
	"e": preload("res://assets/audio/phonemes/e.wav"),
	"f": preload("res://assets/audio/phonemes/f.wav"),
	"g": preload("res://assets/audio/phonemes/g.wav"),
	"h": preload("res://assets/audio/phonemes/h.wav"),
	"i": preload("res://assets/audio/phonemes/i.wav"),
	"j": preload("res://assets/audio/phonemes/j.wav"),
	"k": preload("res://assets/audio/phonemes/k.wav"),
	"l": preload("res://assets/audio/phonemes/l.wav"),
	"m": preload("res://assets/audio/phonemes/m.wav"),
	"n": preload("res://assets/audio/phonemes/n.wav"),
	"o": preload("res://assets/audio/phonemes/o.wav"),
	"p": preload("res://assets/audio/phonemes/p.wav"),
	"q": preload("res://assets/audio/phonemes/q.wav"),
	"r": preload("res://assets/audio/phonemes/r.wav"),
	"s": preload("res://assets/audio/phonemes/s.wav"),
	"t": preload("res://assets/audio/phonemes/t.wav"),
	"u": preload("res://assets/audio/phonemes/u.wav"),
	"v": preload("res://assets/audio/phonemes/v.wav"),
	"w": preload("res://assets/audio/phonemes/w.wav"),
	"x": preload("res://assets/audio/phonemes/x.wav"),
	"y": preload("res://assets/audio/phonemes/y.wav"),
	"z": preload("res://assets/audio/phonemes/z.wav"),
}

# Annette's spoken lines for Phoneme Village, plus the wrong-answer chime.
# These are sequenced in the same queue as the letters, so a prompt is simply
# ["annette_find", "b"]: her sentence, then the block's own human recording.
# Keys must not collide with a letter. See tools/generate_annette.py.
const VOICE := {
	"annette_find": preload("res://assets/audio/voice/annette_find.wav"),
	"annette_good": preload("res://assets/audio/voice/annette_good.wav"),
	"wrong_chime": preload("res://assets/audio/voice/wrong_chime.wav"),
}


func _ready() -> void:
	finished.connect(_play_next)


func play_letter(letter: String) -> void:
	play_sequence([letter])


func play_sequence(letters: Array[String]) -> void:
	# A new interaction replaces both the current sound and any queued letters.
	stop_sequence()
	for letter in letters:
		var key := letter.to_lower()
		if SOUNDS.has(key) or VOICE.has(key):
			pending_letters.append(key)
	sequence_active = not pending_letters.is_empty()
	_play_next()


func stop_sequence() -> void:
	stop()
	pending_letters.clear()
	if sequence_active:
		sequence_active = false
		sequence_cancelled.emit()


func _play_next() -> void:
	if pending_letters.is_empty():
		if sequence_active:
			sequence_active = false
			sequence_finished.emit()
		return
	var letter: String = pending_letters.pop_front()
	stream = SOUNDS[letter] if SOUNDS.has(letter) else VOICE[letter]
	play()
	letter_started.emit(letter)
