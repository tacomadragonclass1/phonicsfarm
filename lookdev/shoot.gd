extends SceneTree
## Shoot lookdev/lookdev.tscn under one named treatment.
##
##     godot --path . --script lookdev/shoot.gd -- <variant>
##
## ⛔ NOT --headless. Capture needs a rendered window, and the draw is FORCED
## rather than awaited -- see the note in tests/capture.gd. Awaiting
## frame_post_draw never returns when the window is not composited, which is
## what made this whole area of the project look unverifiable.

const SHADER := "res://storybook/painted.gdshader"

# Overridden from the command line so a sweep needs no file edit:
#   godot --path . --script lookdev/shoot.gd -- ink 0.34 1.9
# ⭐ CHOSEN BY SWEEP, not by taste alone. 0.34 / 1.9 was the first guess
# and both were invisible -- the grain read as nothing and the outline
# was not drawing at all. 1.2 / 14.0 proved the plumbing and was far too
# much. These sit between.
static var GRAIN := 0.12
static var INK_W := 3.4
static var STRETCH := 6.0
static var VIEW := "near16"


func _initialize() -> void:
	call_deferred("run")


func run() -> void:
	var args := OS.get_cmdline_user_args()
	var variant: String = args[0] if args.size() > 0 else "base"
	if args.size() > 1:
		GRAIN = float(args[1])
	if args.size() > 2:
		INK_W = float(args[2])
	if args.size() > 3:
		STRETCH = float(args[3])
	if args.size() > 4:
		VIEW = args[4]
	# ⛔ Two scenes share this harness. `foliage` has no cottage, so the
	# repaint list cannot be hard-coded -- it walks whatever is there.
	var scene_path := "res://lookdev/lookdev.tscn"
	if VIEW == "foliage":
		scene_path = "res://lookdev/foliage.tscn"
	elif VIEW == "land" or VIEW == "landwide" or VIEW == "south":
		scene_path = "res://scenes/cvc_land.tscn"
	elif VIEW == "clearing" or VIEW == "clearwide":
		scene_path = "res://lookdev/clearing.tscn"
	elif VIEW == "cvc" or VIEW == "trollface":
		scene_path = "res://lookdev/cvc.tscn"
	var scene: Node3D = load(scene_path).instantiate()
	root.add_child(scene)
	current_scene = scene

	var sun := scene.get_node("Sun") as DirectionalLight3D
	var env := (scene.get_node("WorldEnvironment") as WorldEnvironment).environment

	# ⭐ THE LEVERS, each one strictly additive on the one before it, so a
	# difference between two plates can only have come from the lever named
	# between them. Mixing two changes into one plate is how a comparison
	# stops being able to answer anything.
	var levers := {
		"base":    {},
		"lit":     {"light": true},
		"painted": {"light": true, "paint": true},
		"grain":   {"light": true, "paint": true, "grain": true},
		"grade":   {"light": true, "paint": true, "grain": true, "grade": true},
		"ink":     {"light": true, "paint": true, "grain": true, "grade": true,
		            "ink": true},
		"patina":  {"light": true, "paint": true, "grain": true, "grade": true,
		            "ink": true, "mode": 0},
		"brush":   {"light": true, "paint": true, "grain": true, "grade": true,
		            "ink": true, "mode": 1},
	}
	var lever: Dictionary = levers.get(variant, {})

	if lever.get("light", false):
		_relight(sun, env)
	if lever.get("grade", false):
		_regrade(env)
	if lever.get("paint", false):
		_repaint(scene, lever.get("ink", false), lever.get("grain", false),
		         int(lever.get("mode", 0)))

	_frame(scene.get_node("Camera3D") as Camera3D)

	await create_timer(0.7).timeout
	RenderingServer.force_draw(false)
	var path := "/tmp/lookdev-%s.png" % variant
	if VIEW != "iso":
		path = "/tmp/lookdev-%s-%s.png" % [variant, VIEW]
	root.get_texture().get_image().save_png(path)
	if VIEW in ["iso", "low", "near", "near16", "persp", "eye", "ground"]:
		_readability(scene)
	print("SHOT ", path)
	quit()


## ⭐⭐ THE LETTERS ARE THE PRODUCT. A camera that makes the world look better
## and the letters worse is not an improvement, and "it still reads fine" is
## not something anybody can check from a screenshot taken at desk distance.
##
## So each block's plaque is projected to the screen and its on-screen HEIGHT
## reported in pixels, along with whether it is in frame at all. The shipping
## camera is the baseline every other view has to beat or match.
func _readability(scene: Node3D) -> void:
	var camera := scene.get_node("Camera3D") as Camera3D
	var size := get_root().size
	var line := "READ %-7s " % VIEW
	for name in ["BlockC", "Block", "BlockT", "BlockS"]:
		var block := scene.get_node(name) as Node3D
		var foot: Vector3 = block.global_position
		var head: Vector3 = foot + Vector3(0, 0.42, 0)
		if camera.is_position_behind(foot):
			line += "%s:behind " % name
			continue
		var a := camera.unproject_position(foot)
		var b := camera.unproject_position(head)
		var px: float = absf(a.y - b.y)
		var onscreen: bool = (a.x > 0.0 and a.x < float(size.x)
			and a.y > 0.0 and a.y < float(size.y))
		line += "%s:%dpx%s " % [name.replace("Block", "") if name != "Block" else "A",
			int(round(px)), "" if onscreen else "(off)"]
	print(line)


## ⛔⛔ THE CAMERA MAY BE DOING AS MUCH OF THE "ASSET PACK" READ AS THE
## SHADING IS. An orthographic lens at pitch 30 is the convention for a
## PRODUCT SHOT of a model -- it is how an asset store photographs the thing
## it is selling, and how a diorama is lit on a shelf. Nothing inside the
## frame has to look like an asset pack for the frame itself to say so.
##
## ⛔ The gameplay camera really is ortho / pitch 30 / yaw 30 and never turns,
## so changing it is a GAME decision and not an art one. These views exist to
## find out how much of the problem is the lens before anybody pays for that.
##
## Direction from target to camera for pitch p, yaw y:
##     (sin y * cos p, sin p, cos y * cos p)
func _frame(camera: Camera3D) -> void:
	# ⛔ `fixed_camera.gd` RE-PLACES ITSELF every frame from its own
	# pitch/yaw/distance and follows the player. Setting a position without
	# stopping it means the script wins and the shot is whatever the game
	# would have framed -- which is right for "land" and wrong for a wide
	# overview of the plan.
	camera.set_process(false)
	var target := Vector3(0.1, 0.9, -1.1)
	match VIEW:
		"trollface":
			# ⛔ A CHARACTER CANNOT BE JUDGED FROM THE GAME CAMERA. Three
			# rounds of this troll were assessed at 22 m from a pitch-16
			# ortho, where a face is forty pixels, and every round "fixed"
			# something that was never the problem. Look at the thing from
			# the front, close, before touching it again.
			camera.projection = Camera3D.PROJECTION_PERSPECTIVE
			camera.fov = 34.0
			target = Vector3(0.0, 1.35, 0.0)
			camera.position = target + Vector3(0.22, 0.12, 1.0) * 5.4
		"land":
			# ⛔ The level's OWN camera carries fixed_camera.gd, which
			# overwrites rotation in _ready. Overriding it here would test a
			# camera the game never uses -- so this view only moves the
			# target and lets the script place itself.
			camera.projection = Camera3D.PROJECTION_ORTHOGONAL
			camera.size = 8.2
			target = Vector3(-1.0, 1.60, -3.4)
			camera.position = target + Vector3(0.4806, 0.2756, 0.8324) * 26.0
		"landwide":
			# The whole world, to judge the PLAN rather than the framing.
			# ⛔ RETUNED when the world tripled: 62 / (-16, -20) framed the
			# OLD 40 x 88 m ground and now crops away the village, the mill
			# and the river all at once -- a plate that silently shows a
			# third of the subject is worse than no plate.
			camera.projection = Camera3D.PROJECTION_ORTHOGONAL
			camera.size = 168.0
			target = Vector3(-22.0, 0.8, -30.0)
			camera.position = target + Vector3(0.4806, 0.4500, 0.8324) * 150.0
		"south":
			# The river and the open ground the pedestals now stand in.
			camera.projection = Camera3D.PROJECTION_ORTHOGONAL
			camera.size = 54.0
			target = Vector3(10.0, 0.8, 12.0)
			camera.position = target + Vector3(0.4806, 0.3200, 0.8324) * 70.0
		"clearing":
			camera.projection = Camera3D.PROJECTION_ORTHOGONAL
			camera.size = 8.2
			target = Vector3(-1.0, 1.60, -3.4)
			camera.position = target + Vector3(0.4806, 0.2756, 0.8324) * 26.0
		"clearwide":
			# The whole clearing, to judge the PLAN rather than the framing.
			camera.projection = Camera3D.PROJECTION_ORTHOGONAL
			camera.size = 26.0
			target = Vector3(-2.0, 0.8, -6.0)
			camera.position = target + Vector3(0.4806, 0.4500, 0.8324) * 30.0
		"cvc":
			camera.projection = Camera3D.PROJECTION_ORTHOGONAL
			camera.size = 8.0
			target = Vector3(0.0, 1.30, 0.6)
			camera.position = target + Vector3(0.4806, 0.2756, 0.8324) * 24.0
		"foliage":
			# Square on to the row, low enough to read every silhouette
			# against sky rather than against the ground behind it.
			camera.projection = Camera3D.PROJECTION_ORTHOGONAL
			camera.size = 5.2
			target = Vector3(0.6, 1.45, 0.2)
			camera.position = target + Vector3(0.30, 0.22, 0.93) * 22.0
		"low":
			# Same orthographic lens, much lower. Isolates PITCH from
			# projection: if this alone helps, the problem was the god's-eye
			# angle and not the ortho.
			camera.projection = Camera3D.PROJECTION_ORTHOGONAL
			camera.size = 11.0
			camera.position = target + Vector3(0.4806, 0.2756, 0.8324) * 24.0
		"near":
			# ⭐ THE CANDIDATE. Ortho kept, pitch down to 22 and the frame
			# pulled in from 10.5 m to 8.0 -- "lower and closer in" without
			# giving up the constant scale the board depends on.
			# ⛔ The look-at point rises with the pitch drop. At a low angle
			# a target on the ground pushes everything standing UP out of
			# the top of the frame -- the first run of this decapitated the
			# chimney.
			camera.projection = Camera3D.PROJECTION_ORTHOGONAL
			camera.size = 8.6
			target = Vector3(0.1, 1.5, -1.1)
			camera.position = target + Vector3(0.5317, 0.3746, 0.7592) * 24.0
		"near16":
			# ⭐⭐ THE CHOSEN CAMERA. Orthographic, pitch 16, pulled in.
			#
			# ⛔ The look-at point RISES as the pitch drops. A target on the
			# ground is fine at pitch 30 and decapitates everything standing
			# up at pitch 16 -- the first cut of this lost the chimney and
			# half the roof. At a low angle the frame is mostly vertical
			# subject, so aim at the middle of it.
			#
			# ⛔ A letter goes off-screen here, and that is a DECISION, not a
			# defect: "the player will go around the space to collect
			# letters, that's the fun of it". See the note in
			# lookdev/DECISIONS.md -- it retires the rule that every letter
			# must be visible from a fixed camera, which `tests/village.gd`
			# currently enforces.
			camera.projection = Camera3D.PROJECTION_ORTHOGONAL
			camera.size = 8.2
			target = Vector3(0.1, 1.6, -1.1)
			camera.position = target + Vector3(0.4806, 0.2756, 0.8324) * 24.0
		"persp":
			camera.projection = Camera3D.PROJECTION_PERSPECTIVE
			camera.fov = 28.0
			camera.position = target + Vector3(0.5317, 0.3746, 0.7592) * 26.0
		"eye":
			# ⛔ A CHILD'S EYE HEIGHT, 1.15 m. Kept honest: this is where the
			# game would be played from, not a hero shot taken from it.
			camera.projection = Camera3D.PROJECTION_PERSPECTIVE
			camera.fov = 52.0
			target = Vector3(-0.6, 0.55, -0.4)
			camera.position = Vector3(4.6, 1.15, 5.0)
		"ground":
			camera.projection = Camera3D.PROJECTION_PERSPECTIVE
			camera.fov = 48.0
			target = Vector3(-1.2, 1.3, -2.4)
			camera.position = Vector3(5.4, 1.62, 5.2)
		_:
			camera.projection = Camera3D.PROJECTION_ORTHOGONAL
			camera.size = 10.5
			camera.position = target + Vector3(0.433, 0.500, 0.750) * 24.0
	camera.look_at(target)


## ⭐ LIGHT WITH A DIRECTION AND AIR TO CARRY IT. The published grade is a
## near-overhead key at energy 0.40, 26 degrees wide, with shadows at 0.34
## opacity -- which is a lightbox, not a time of day. Everything sits at the
## same distance because there is no fog, and nothing has a shadow long
## enough to tell you where the sun is.
func _relight(sun: DirectionalLight3D, env: Environment) -> void:
	# Low and from the side: a long shadow is what says "late afternoon",
	# and a side key is the only thing that makes a wall's corner read.
	sun.rotation_degrees = Vector3(-34.0, 38.0, 0.0)
	sun.light_color = Color(1.0, 0.94, 0.83)
	sun.light_energy = 1.15
	sun.light_angular_distance = 2.2
	sun.shadow_enabled = true
	sun.shadow_opacity = 1.0
	sun.shadow_blur = 1.2

	# ⛔ Ambient goes COOL and DOWN. Warm key against cool fill is the whole
	# trick; raising both is what bleached the last attempt to pastel.
	env.ambient_light_color = Color(0.58, 0.66, 0.84)
	env.ambient_light_energy = 0.55

	# Air. Distance desaturation is most of what "dreamy" means -- without it
	# a far hedge is as present as a near doorway and the world reads flat.
	env.fog_enabled = true
	env.fog_light_color = Color(0.78, 0.82, 0.86)
	env.fog_light_energy = 1.0
	# ⛔ 0.0022, not 0.013. The first number put the whole scene behind a
	# white sheet -- and the reason is the ORTHOGRAPHIC camera: it sits 24 m
	# back from a subject it is not perspective-projecting, so every pixel
	# is already deep in the fog before the subject starts. Depth fog has to
	# be set against the camera's standoff, not against the scene's size.
	env.fog_density = 0.0022
	env.fog_aerial_perspective = 0.22
	env.fog_sky_affect = 0.1

	env.tonemap_exposure = 1.0
	env.adjustment_saturation = 1.12


func _repaint(scene: Node3D, with_ink: bool, heavy_grain: bool,
		mode: int) -> void:
	var applier: PaintedSurface = PaintedSurface.new()
	applier.outline = with_ink
	applier.grain_strength = GRAIN if heavy_grain else 0.0
	applier.grain_scale = 9.0 if mode == 1 else 7.5
	applier.ink_width = INK_W
	applier.apply(scene)
	applier.free()
	if not heavy_grain:
		return
	# ⛔⛔ GRAIN AT 0.085 WAS A WHISPER. The complaint about this set is that a
	# painted thing has MARKS in it and these have none, and a mark you have
	# to be told about is not a mark. It is also the one surface lever that
	# does not care about texel density -- the terrain carries 16 texels per
	# metre against a 142 px/m camera, so nothing baked into it can ever
	# resolve, but a per-pixel world-space mark resolves at any density.
	for node in scene.find_children("*", "MeshInstance3D", true, false):
		var mi := node as MeshInstance3D
		for surface in mi.get_surface_override_material_count():
			var m := mi.get_surface_override_material(surface)
			if m is ShaderMaterial and (m as ShaderMaterial).shader != null:
				var sm := m as ShaderMaterial
				sm.set_shader_parameter("grain_strength", GRAIN)
				sm.set_shader_parameter("grain_scale",
					9.0 if mode == 1 else 7.5)
				sm.set_shader_parameter("grain_warm", 0.5)
				sm.set_shader_parameter("grain_mode", mode)
				sm.set_shader_parameter("grain_stretch", STRETCH)
				if sm.next_pass is ShaderMaterial:
					(sm.next_pass as ShaderMaterial).set_shader_parameter(
						"width_screen", INK_W)


## ⭐ MEASURED, not matched by eye. Sampled across the whole frame, the
## published build sits at mean saturation 0.707 against the Cycles control's
## 0.304 -- 2.3x over, which is the acid green in one number. Value is 0.411
## against 0.546, so it is also too dark. The target here is the control's
## pair, and `lookdev/measure.py` checks the result rather than trusting it.
func _regrade(env: Environment) -> void:
	env.adjustment_saturation = 0.78
	env.tonemap_exposure = 1.22
	env.ambient_light_energy = 0.62
