extends CanvasLayer

## The floating count of letters found in the current Phoneme Village round.
##
## Deliberately almost nothing: one number in the very top-left corner, no
## label, no box, no animation when it changes. It is a progress reassurance
## for the adult in the room and for a child who wants to see the number climb,
## not a score -- nothing is lost, and there is no target to beat.
##
## It only exists while Chuck is in the village. CVC Land has no round to count,
## and a stray "0" floating over the lever game would be noise.

## Height of the NUMBER, as a fraction of the design viewport height (800),
## so "roughly a sixteenth of the screen" holds on whatever the classroom
## screen turns out to be. Measured on the drawn digit rather than on the font
## size, because a digit is drawn at roughly 72% of its font size.
@export var digit_height_fraction := 1.0 / 16.0
const DIGIT_TO_FONT := 1.0 / 0.72
## Corner inset, in the same 1280x800 design space the touch layer uses.
@export var margin := Vector2(18.0, 6.0)
@export var fade_time := 0.35
## Never fully opaque: it sits over the grass, not in front of it.
@export var resting_alpha := 0.72

var village: PhonemeVillage
var fade: Tween

@onready var count_label: Label = $Count


func _ready() -> void:
	var design_height: float = ProjectSettings.get_setting("display/window/size/viewport_height", 800)
	count_label.add_theme_font_size_override(
		"font_size", roundi(design_height * digit_height_fraction * DIGIT_TO_FONT))
	count_label.position = margin
	count_label.modulate.a = 0.0
	# The village is instanced in the main scene, and this layer is a sibling of
	# it, so wait one frame rather than assuming who is ready first.
	village = get_tree().get_first_node_in_group("phoneme_village")
	if not village:
		return
	village.round_started.connect(_on_round_started)
	village.answered.connect(_on_answered)
	village.presence_changed.connect(_on_presence_changed)
	_show_count()


func _on_round_started() -> void:
	# A finished alphabet lays out a brand new board: the count starts over.
	_show_count()


func _on_answered(_letter: String, correct: bool) -> void:
	if correct:
		_show_count()


func _on_presence_changed(present: bool) -> void:
	if fade:
		fade.kill()
	fade = create_tween()
	fade.tween_property(count_label, "modulate:a", resting_alpha if present else 0.0, fade_time)


func _show_count() -> void:
	count_label.text = str(village.found.size())
