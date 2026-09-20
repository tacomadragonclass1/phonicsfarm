extends Camera3D

# Keep the isometric angle fixed while translating with Chuck through the level.
@export var follow_offset := Vector3(16.0, 10.55, 16.0)

var target: Node3D


func _ready() -> void:
	target = get_parent().get_node_or_null("Player")
	get_viewport().size_changed.connect(fit_clearing)
	fit_clearing()


func _process(_delta: float) -> void:
	if target:
		global_position = target.global_position + follow_offset


func fit_clearing() -> void:
	var viewport_size := get_viewport().get_visible_rect().size
	var aspect := viewport_size.x / maxf(viewport_size.y, 1.0)
	# A smaller orthographic size gives the closer miniature view requested.
	size = maxf(18.0, 25.0 / aspect)
