extends SceneTree

var scene: Node3D
var player: CharacterBody3D
var board: Node3D
var failures := 0


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


func teleport(point: Vector3) -> void:
	player.global_position = board.to_global(point)
	player.velocity = Vector3.ZERO
	await frames()


func walk(action: String, count: int) -> void:
	Input.action_press(action)
	await frames(count)
	Input.action_release(action)
	await frames(15)


func run() -> void:
	scene = load("res://scenes/main.tscn").instantiate()
	root.add_child(scene)
	current_scene = scene
	player = scene.get_node("Player")
	board = scene.get_node("Environment")
	await frames(5)
	var camera: Camera3D = scene.get_node("Camera3D")
	var camera_rotation := camera.global_rotation
	var ui: Control = scene.get_node("TouchControls/Controls")
	check(ui.button_center().x - ui.joystick_center().x == 160.0, "Pick/Put beside joystick")
	check(ui.button_center().distance_to(ui.joystick_center()) > 146.0, "touch hit areas do not overlap")

	# All letters must be on dry land and individually accessible from the north.
	var blocks: Node3D = scene.get_node("Blocks")
	var row_ok := blocks.get_child_count() == 26
	var pickup_ok := true
	for i in blocks.get_child_count():
		var block: AlphabetBlock = blocks.get_child(i)
		var original := block.global_position
		var local := board.to_local(original)
		row_ok = row_ok and absf(local.z - 12.0) < 0.01 and absf(local.x) < 15.0
		row_ok = row_ok and block.letter == "abcdefghijklmnopqrstuvwxyz"[i]
		await teleport(local + Vector3(0, 0.02, -0.95))
		player.interact()
		pickup_ok = pickup_ok and player.carried_block == block
		if player.carried_block:
			var carried: AlphabetBlock = player.carried_block
			carried.put_on_ground(blocks, original)
			player.carried_block = null
		# Reparent appends at the end; restore scene order for the next iteration.
		blocks.move_child(block, i)
		await frames()
	check(row_ok, "all 26 letters in order on a single dry row inside board")
	check(pickup_ok, "each letter can be approached and picked up independently")

	await teleport(Vector3(0, 0.02, 2.8))
	Input.action_press("move_down")
	await frames(65)
	check(absf(Vector2(player.velocity.x, player.velocity.z).length() - 6.4) < 0.05, "Chuck walks at double speed")
	Input.action_release("move_down")
	await frames(15)
	check(board.to_local(player.global_position).z > 8.3, "Chuck walks across bridge without jumping")
	check(absf(player.global_position.y) < 0.05, "Chuck returns to dry ground height")
	check(camera.global_position.distance_to(player.global_position + camera.follow_offset) < 0.01, "camera follows Chuck across river")
	check(camera.global_rotation.is_equal_approx(camera_rotation), "camera angle stays fixed")

	var block: AlphabetBlock = blocks.get_node("Block_n")
	await teleport(board.to_local(block.global_position) + Vector3(0, 0.02, -0.95))
	player.interact()
	check(player.carried_block == block, "pick up letter on south bank")
	await teleport(Vector3(0, 0.02, 10))
	await walk("move_up", 65)
	check(board.to_local(player.global_position).z < 4.0 and player.carried_block == block, "carry letter back over bridge")
	var slot: Pedestal = scene.get_node("Pedestals/Pedestal2")
	player.global_position = slot.global_position + Vector3(0.85, 0.02, 0.85)
	player.velocity = Vector3.ZERO
	await frames()
	player.interact()
	check(slot.block == block, "fetched letter places on pedestal")

	await teleport(Vector3(6, 0.02, 3.5))
	await walk("move_down", 55)
	check(board.to_local(player.global_position).z < 4.8, "river blocks walking into water away from bridge")
	await teleport(Vector3(-12, 0.02, -2.6))
	await walk("move_left", 32)
	check(board.to_local(player.global_position).x < -15.0, "tree gap has no leftover interior wall")
	await walk("move_left", 120)
	var west_edge: float = board.to_local(player.global_position).x
	# The clearing walls are gone. Chuck should walk straight through where the
	# old 34-wide boundary stood and only stop at the edge of the whole world.
	check(west_edge < -17.0, "no leftover wall at the old clearing edge")
	check(west_edge > -20.3, "single outer boundary keeps Chuck on board")
	check(west_edge < -19.5, "Chuck actually reaches that outer boundary")

	print("LAYOUT RESULT: ", failures, " failures")
	quit(1 if failures else 0)
