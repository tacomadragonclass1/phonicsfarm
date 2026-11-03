extends SceneTree
## Bake trimesh collision to disk, instead of building it at load.
##
## ⛔⛔ THE WEB BUILD IS SINGLE-THREADED. The console says so:
## "Build configuration: Emscripten 4.0.10, single-threaded". Everything --
## decompressing the pck, instancing scenes, and building physics shapes --
## happens on the ONE main thread, and anything slow there freezes the whole
## browser tab rather than merely dropping frames.
##
## `terrain_collision.gd` called `create_trimesh_shape()` at `_ready` on the
## terrain (13,122 faces) and the mill mound (12,490). That was survivable
## when the terrain was 2,048 faces; densifying its grid 6x to buy sharper
## ground edges made it six times the work, and nothing re-tested it in a
## browser afterwards. The published preview hung Chrome.
##
## A saved ConcavePolygonShape3D is deserialised instead of computed, which
## is the difference between reading a list of points and building one.

const SOURCES := {
	"terrain": "res://assets/storybook/explore/foundation_terrain.glb",
	"mill_mound": "res://assets/storybook/village/mill_mound.glb",
}


func _initialize() -> void:
	call_deferred("run")


func run() -> void:
	var failures := 0
	for name in SOURCES:
		var packed: PackedScene = load(SOURCES[name])
		if packed == null:
			print("FAIL: cannot load ", SOURCES[name])
			failures += 1
			continue
		var node := packed.instantiate()
		var best: ArrayMesh = null
		var best_faces := 0
		for child in node.find_children("*", "MeshInstance3D", true, false):
			var mesh_instance := child as MeshInstance3D
			if mesh_instance.mesh == null:
				continue
			var faces: int = mesh_instance.mesh.get_faces().size() / 3
			if faces > best_faces:
				best_faces = faces
				best = mesh_instance.mesh
		if best == null:
			print("FAIL: no mesh in ", name)
			failures += 1
			continue
		var shape := best.create_trimesh_shape()
		var path := "res://assets/storybook/collision/%s.res" % name
		var err := ResourceSaver.save(shape, path)
		if err != OK:
			print("FAIL: save ", path, " -> ", err)
			failures += 1
		else:
			print("baked %-12s %6d faces -> %s" % [name, best_faces, path])
		node.queue_free()
	print("BAKE RESULT: %d failures" % failures)
	quit(1 if failures else 0)
