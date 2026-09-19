extends SceneTree


func _initialize() -> void:
	call_deferred("capture")


func capture() -> void:
	var scene: Node3D = load("res://scenes/main.tscn").instantiate()
	root.add_child(scene)
	current_scene = scene
	var output := "/tmp/phonics-clearing.png"
	if "--close-up" in OS.get_cmdline_user_args():
		var camera := scene.get_node("Camera3D") as Camera3D
		camera.position = Vector3(-0.8, 5, -0.9)
		camera.look_at(Vector3(-4.8, 0.4, -4.9))
		camera.size = 3.5
		output = "/tmp/phonics-close-up.png"
	await create_timer(1.0).timeout
	await RenderingServer.frame_post_draw
	root.get_texture().get_image().save_png(output)
	quit()
