extends SceneTree


func _initialize() -> void:
	call_deferred("capture")


func capture() -> void:
	if DisplayServer.get_name() == "headless":
		push_error("Capture requires a rendered window; omit --headless.")
		quit(1)
		return
	var scene: Node3D = load("res://scenes/main.tscn").instantiate()
	root.add_child(scene)
	current_scene = scene
	var output := "/tmp/phonics-clearing.png"
	if "--river" in OS.get_cmdline_user_args():
		scene.get_node("Player").position = scene.get_node("Environment").to_global(Vector3(0, 0.02, 4))
		output = "/tmp/phonics-river.png"
	if "--overview" in OS.get_cmdline_user_args():
		var camera := scene.get_node("Camera3D") as Camera3D
		camera.set_process(false)
		camera.position = Vector3(16, 20, 16)
		camera.look_at(Vector3.ZERO)
		camera.size = 40
		output = "/tmp/phonics-overview.png"
	if "--close-up" in OS.get_cmdline_user_args():
		var camera := scene.get_node("Camera3D") as Camera3D
		camera.set_process(false)
		var block: Node3D = scene.get_node("Blocks/Block_a")
		camera.position = block.global_position + Vector3(2, 2, 2)
		camera.look_at(block.global_position + Vector3.UP * 0.4)
		camera.size = 3.5
		output = "/tmp/phonics-close-up.png"
	await create_timer(1.0).timeout
	await RenderingServer.frame_post_draw
	root.get_texture().get_image().save_png(output)
	quit()
