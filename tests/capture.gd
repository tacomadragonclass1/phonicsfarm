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
	if "--pedestals" in OS.get_cmdline_user_args() or "--feedback" in OS.get_cmdline_user_args():
		var camera := scene.get_node("Camera3D") as Camera3D
		camera.set_process(false)
		var center := Vector3(-0.8, 0.5, 0.8)
		camera.position = center + Vector3(12, 8, 12)
		camera.look_at(center)
		camera.size = 10
		for index in range(3):
			var block := scene.get_node("Blocks/Block_" + ["c", "a", "t"][index]) as AlphabetBlock
			scene.get_node("Pedestals/Pedestal" + str(index + 1)).place(block)
		output = "/tmp/phonics-pedestals.png"
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
	if "--village" in OS.get_cmdline_user_args():
		# Phoneme Village with a round already scattered, seen from the south.
		var village := scene.get_node("Environment/PhonemeVillage") as PhonemeVillage
		village.start_round()
		var camera := scene.get_node("Camera3D") as Camera3D
		camera.set_process(false)
		var centre: Vector3 = village.global_position
		camera.position = centre + Vector3(20, 22, 20)
		camera.look_at(centre)
		camera.size = 46
		output = "/tmp/phonics-village.png"
	if "--village-close" in OS.get_cmdline_user_args():
		var village := scene.get_node("Environment/PhonemeVillage") as PhonemeVillage
		village.start_round()
		scene.get_node("Player").position = village.to_global(Vector3(0, 0.02, 12))
		output = "/tmp/phonics-village-close.png"
	if "--world" in OS.get_cmdline_user_args():
		var camera := scene.get_node("Camera3D") as Camera3D
		camera.set_process(false)
		var centre: Vector3 = scene.get_node("Environment").to_global(Vector3(0, 0, -24))
		camera.position = centre + Vector3(40, 60, 40)
		camera.look_at(centre)
		camera.size = 104
		output = "/tmp/phonics-world.png"
	if "--close-up" in OS.get_cmdline_user_args():
		var camera := scene.get_node("Camera3D") as Camera3D
		camera.set_process(false)
		var block: Node3D = scene.get_node("Blocks/Block_a")
		camera.position = block.global_position + Vector3(2, 2, 2)
		camera.look_at(block.global_position + Vector3.UP * 0.4)
		camera.size = 3.5
		output = "/tmp/phonics-close-up.png"
	await create_timer(1.0).timeout
	if "--feedback" in OS.get_cmdline_user_args():
		scene.get_node("SoundLever").activate()
		await create_timer(0.18).timeout
		await RenderingServer.frame_post_draw
		root.get_texture().get_image().save_png("/tmp/phonics-feedback-active.png")
		await root.get_node("PhonemeAudio").sequence_finished
		await create_timer(0.12).timeout
		output = "/tmp/phonics-feedback-word.png"
	await RenderingServer.frame_post_draw
	root.get_texture().get_image().save_png(output)
	quit()
