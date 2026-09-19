extends Camera3D

# Keep the full clearing in view on tall screens, without following the player.
func _ready() -> void:
	get_viewport().size_changed.connect(fit_clearing)
	fit_clearing()


func fit_clearing() -> void:
	var viewport_size := get_viewport().get_visible_rect().size
	var aspect := viewport_size.x / maxf(viewport_size.y, 1.0)
	size = maxf(20.0, 25.0 / aspect)
