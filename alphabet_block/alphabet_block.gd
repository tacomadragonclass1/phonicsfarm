@tool
class_name AlphabetBlock
extends StaticBody3D

## Emitted when Chuck picks this block up. Phoneme Village listens for it to
## judge its own blocks; nothing in CVC Land is connected to it.
signal picked_up(block: AlphabetBlock)

@export var letter := "a":
	set(value):
		letter = value.to_lower().left(1)
		if is_node_ready():
			update_letter()

var is_carried := false
## Phoneme Village sets this on its own blocks. A wrong letter put back down
## there must stay quiet, because playing its sound stops whatever is already
## playing -- which was Annette halfway through repeating her question.
## CVC Land leaves it false: every drop there still sounds the letter.
var silent_drops := false
var pedestal: Pedestal
## Container a dropped block returns to. Keeps Phoneme Village's blocks out of
## CVC Land's "Blocks" node so a board refresh can still find and free them.
var home: Node3D
var is_highlighted := false
var face_material: StandardMaterial3D
var default_face_color: Color
var sparkle: CPUParticles3D


func _ready() -> void:
	update_letter()
	if not home:
		home = get_parent() as Node3D
	if not Engine.is_editor_hint():
		# The packed scene shares meshes/materials: isolate this block's faces.
		face_material = $Visual/Front.get_active_material(0).duplicate()
		default_face_color = face_material.albedo_color
		for face in $Visual.get_children():
			if face.name != "Cube":
				face.material_override = face_material


func update_letter() -> void:
	for label in $Letters.get_children():
		label.text = letter


func pick_up(anchor: Node3D) -> void:
	set_highlighted(false)
	set_visual_lift(0.0)
	is_carried = true
	collision_layer = 0
	collision_mask = 0
	reparent(anchor, false)
	position = Vector3.ZERO
	rotation = Vector3.ZERO
	play_sound()
	picked_up.emit(self)


func put_on_ground(parent: Node3D, point: Vector3) -> void:
	set_highlighted(false)
	set_visual_lift(0.0)
	reparent(parent, false)
	global_position = point
	rotation = Vector3.ZERO
	is_carried = false
	collision_layer = 4
	collision_mask = 2
	if not silent_drops:
		play_sound()


func play_sound() -> void:
	if not Engine.is_editor_hint():
		get_node("/root/PhonemeAudio").play_letter(letter)


func set_highlighted(enabled: bool) -> void:
	is_highlighted = enabled
	if face_material:
		face_material.albedo_color = Color(1.0, 0.68, 0.08) if enabled else default_face_color
	if not enabled and sparkle:
		sparkle.emitting = false
		sparkle.visible = false


func set_visual_lift(height: float) -> void:
	$Visual.position.y = height
	$Letters.position.y = height


func celebrate() -> void:
	if not sparkle:
		sparkle = CPUParticles3D.new()
		sparkle.emitting = false
		sparkle.one_shot = true
		sparkle.amount = 12
		sparkle.lifetime = 0.55
		sparkle.explosiveness = 1.0
		sparkle.emission_shape = CPUParticles3D.EMISSION_SHAPE_SPHERE
		sparkle.emission_sphere_radius = 0.45
		sparkle.direction = Vector3.UP
		sparkle.spread = 100.0
		sparkle.initial_velocity_min = 0.6
		sparkle.initial_velocity_max = 1.2
		sparkle.gravity = Vector3(0, -0.6, 0)
		var mesh := SphereMesh.new()
		mesh.radius = 0.035
		mesh.height = 0.07
		var material := StandardMaterial3D.new()
		material.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
		material.albedo_color = Color(1.0, 0.8, 0.18)
		mesh.material = material
		sparkle.mesh = mesh
		add_child(sparkle)
		sparkle.position.y = 0.9
	sparkle.visible = true
	sparkle.restart()
	sparkle.emitting = true


func set_face_color(color: Color) -> void:
	if face_material:
		face_material.albedo_color = color


func vanish() -> void:
	# Phoneme Village's reward: the block leaves a puff behind and is freed by
	# the caller. The smoke is a separate node so it outlives the block.
	var smoke := CPUParticles3D.new()
	smoke.emitting = false
	smoke.one_shot = true
	smoke.amount = 20
	smoke.lifetime = 0.8
	smoke.explosiveness = 0.92
	smoke.emission_shape = CPUParticles3D.EMISSION_SHAPE_SPHERE
	smoke.emission_sphere_radius = 0.3
	smoke.direction = Vector3.UP
	smoke.spread = 60.0
	smoke.initial_velocity_min = 0.5
	smoke.initial_velocity_max = 1.4
	smoke.gravity = Vector3(0, 0.4, 0)
	smoke.scale_amount_min = 0.7
	smoke.scale_amount_max = 1.8
	var mesh := SphereMesh.new()
	mesh.radius = 0.12
	mesh.height = 0.24
	var material := StandardMaterial3D.new()
	material.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	material.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	material.albedo_color = Color(0.96, 0.96, 0.98, 0.72)
	mesh.material = material
	smoke.mesh = mesh
	# Parent to the scene, not to this block: the block is freed immediately.
	var scene := get_tree().current_scene
	scene.add_child(smoke)
	smoke.global_position = global_position + Vector3.UP * 0.45
	smoke.emitting = true
	get_tree().create_timer(smoke.lifetime + 0.4).timeout.connect(smoke.queue_free)
