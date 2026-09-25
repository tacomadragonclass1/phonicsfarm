extends Control

## Touch and mouse control with nothing drawn on screen.
##
## One finger anywhere is the walking stick: press to plant it, drag in any
## direction to steer, let go to stop. A second finger tapped anywhere puts the
## carried block down. A single quick tap that never moved does the same, so the
## lever can still be pulled one-handed.
##
## Picking up is not a control at all -- Chuck picks a block up by walking into
## it (see player.gd).
##
## Both pointers feed the SAME Input Map as a keyboard or gamepad, through
## virtual joypad device 100, so player.gd has no touch-specific movement code.
const VIRTUAL_DEVICE := 100
const NO_POINTER := -2
const MOUSE_POINTER := -1
## Drag distance, in the 1280x800 design space, that means full speed.
const DRAG_RANGE := 110.0
## A press shorter than this, which never really moved, counts as a tap.
const TAP_MILLISECONDS := 320
const TAP_SLOP := 24.0

var movement_pointer := NO_POINTER
var origin := Vector2.ZERO
var pressed_at := 0
var travelled := 0.0
var stick := Vector2.ZERO


func _process(_delta: float) -> void:
	# Safety net. If a pointer-up is ever lost -- a mouse released outside the
	# canvas, a browser swallowing the event -- Chuck would walk forever. The
	# mouse can be polled for its real state; touch reports cancellation itself.
	if movement_pointer == MOUSE_POINTER and not Input.is_mouse_button_pressed(MOUSE_BUTTON_LEFT):
		release_controls()


func _input(event: InputEvent) -> void:
	if event is InputEventScreenTouch:
		pointer_button(event.index, event.position, event.pressed and not event.canceled)
	elif event is InputEventScreenDrag:
		pointer_motion(event.index, event.position)
	elif event is InputEventMouseButton and event.button_index == MOUSE_BUTTON_LEFT:
		pointer_button(MOUSE_POINTER, event.position, event.pressed)
	elif event is InputEventMouseMotion:
		pointer_motion(MOUSE_POINTER, event.position)


func pointer_button(pointer: int, point: Vector2, pressed: bool) -> void:
	if pressed:
		if movement_pointer == NO_POINTER:
			movement_pointer = pointer
			origin = point
			pressed_at = Time.get_ticks_msec()
			travelled = 0.0
			set_stick(Vector2.ZERO)
		else:
			# Any further finger, anywhere on the screen: put the block down.
			tap()
	elif movement_pointer == pointer:
		movement_pointer = NO_POINTER
		set_stick(Vector2.ZERO)
		if travelled < TAP_SLOP and Time.get_ticks_msec() - pressed_at < TAP_MILLISECONDS:
			tap()


func pointer_motion(pointer: int, point: Vector2) -> void:
	if pointer != movement_pointer:
		return
	var offset := point - origin
	travelled = maxf(travelled, offset.length())
	if offset.length() > DRAG_RANGE:
		# Let the anchor trail the finger, so one long drag keeps steering
		# instead of pinning the direction to wherever the press landed.
		origin = point - offset.normalized() * DRAG_RANGE
		offset = point - origin
	set_stick(offset / DRAG_RANGE)


func set_stick(value: Vector2) -> void:
	stick = value.limit_length()
	for axis in [JOY_AXIS_LEFT_X, JOY_AXIS_LEFT_Y]:
		var event := InputEventJoypadMotion.new()
		event.device = VIRTUAL_DEVICE
		event.axis = axis
		event.axis_value = stick.x if axis == JOY_AXIS_LEFT_X else stick.y
		Input.parse_input_event(event)


func send_button(pressed: bool) -> void:
	var event := InputEventJoypadButton.new()
	event.device = VIRTUAL_DEVICE
	event.button_index = JOY_BUTTON_A
	event.pressed = pressed
	Input.parse_input_event(event)


## One clean press-and-release. The player polls the action in _physics_process,
## and Godot may not flush a synthesised event until the next frame, so the
## press is held across two physics frames before it is let go.
func tap() -> void:
	send_button(true)
	await get_tree().physics_frame
	await get_tree().physics_frame
	await get_tree().process_frame
	send_button(false)


func release_controls() -> void:
	movement_pointer = NO_POINTER
	set_stick(Vector2.ZERO)
	send_button(false)


func _notification(what: int) -> void:
	if what == NOTIFICATION_APPLICATION_FOCUS_OUT or what == NOTIFICATION_WM_WINDOW_FOCUS_OUT:
		release_controls()
