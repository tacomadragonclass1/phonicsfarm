extends Control

# A virtual joypad feeds the SAME Input Map as a physical controller. A separate
# device ID lets keyboard/gamepad input coexist with two-finger touch input.
const VIRTUAL_DEVICE := 100
const NO_POINTER := -2
const MOUSE_POINTER := -1
var movement_pointer := NO_POINTER
var interact_pointer := NO_POINTER
var stick := Vector2.ZERO


func joystick_center() -> Vector2:
	return Vector2(112, size.y - 112)


func button_center() -> Vector2:
	return joystick_center() + Vector2(160, 0)


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
		if movement_pointer == NO_POINTER and point.distance_to(joystick_center()) < 86:
			movement_pointer = pointer
			pointer_motion(pointer, point)
		elif interact_pointer == NO_POINTER and point.distance_to(button_center()) < 60:
			interact_pointer = pointer
			send_button(true)
	else:
		if movement_pointer == pointer:
			movement_pointer = NO_POINTER
			set_stick(Vector2.ZERO)
		if interact_pointer == pointer:
			interact_pointer = NO_POINTER
			send_button(false)
	queue_redraw()


func pointer_motion(pointer: int, point: Vector2) -> void:
	if pointer == movement_pointer:
		set_stick(((point - joystick_center()) / 62.0).limit_length())


func set_stick(value: Vector2) -> void:
	stick = value
	for axis in [JOY_AXIS_LEFT_X, JOY_AXIS_LEFT_Y]:
		var event := InputEventJoypadMotion.new()
		event.device = VIRTUAL_DEVICE
		event.axis = axis
		event.axis_value = stick.x if axis == JOY_AXIS_LEFT_X else stick.y
		Input.parse_input_event(event)
	queue_redraw()


func send_button(pressed: bool) -> void:
	var event := InputEventJoypadButton.new()
	event.device = VIRTUAL_DEVICE
	event.button_index = JOY_BUTTON_A
	event.pressed = pressed
	Input.parse_input_event(event)


func release_controls() -> void:
	movement_pointer = NO_POINTER
	interact_pointer = NO_POINTER
	set_stick(Vector2.ZERO)
	send_button(false)


func _notification(what: int) -> void:
	if what == NOTIFICATION_APPLICATION_FOCUS_OUT or what == NOTIFICATION_WM_WINDOW_FOCUS_OUT:
		release_controls()


func _draw() -> void:
	var center := joystick_center()
	draw_circle(center, 82, Color(0.12, 0.22, 0.2, 0.22))
	draw_arc(center, 82, 0, TAU, 64, Color(1, 1, 0.94, 0.65), 2, true)
	draw_circle(center + stick * 52, 31, Color(1, 0.98, 0.88, 0.8))
	var button := button_center()
	var tint := Color(1, 0.9, 0.6, 0.95) if interact_pointer != NO_POINTER else Color(1, 0.98, 0.88, 0.85)
	draw_circle(button, 56, tint)
	draw_arc(button, 56, 0, TAU, 64, Color(0.3, 0.4, 0.3, 0.6), 2, true)
	draw_string(ThemeDB.fallback_font, button + Vector2(-45, 6), "Pick / Put", HORIZONTAL_ALIGNMENT_CENTER, 90, 16, Color(0.16, 0.26, 0.23))
