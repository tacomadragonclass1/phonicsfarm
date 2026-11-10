extends SceneTree
## Print the real bounding box of every scene that needs a collider.
##
##     godot --headless --path . --script tools/measure_footprints.gd
##
## ⭐ MEASURED, NOT TYPED. Colliders invented by eye are either too small --
## so Chuck's shoulder passes through a wall -- or too big, so he stops in
## mid-air a pace short of a tree. Both read as the same bug to a child.
##
## ⛔⛔ RUN `godot --headless --path . --import` FIRST. This reads meshes
## through the IMPORT CACHE, so a mesh rebuilt in Blender and measured
## without reimporting measures the PREVIOUS geometry, with a plausible size.
## That has caught this project out four separate times in one session.
##
## The output is a table meant to be pasted into a generator's footprint
## table, not read once and thrown away: re-run it whenever an asset is
## rebuilt and the numbers move.

const SCENES := [
	"res://storybook/cvc/woodshed.tscn",
	"res://storybook/cvc/handcart.tscn",
	"res://storybook/cvc/bell_lever.tscn",
	"res://storybook/cvc/pedestal.tscn",
	"res://storybook/foundation/tree.tscn",
	"res://storybook/village/tree_b.tscn",
	"res://storybook/village/bush.tscn",
	"res://storybook/village/blossom.tscn",
	"res://storybook/village/mushrooms.tscn",
	"res://storybook/village/well.tscn",
	"res://storybook/village/fingerpost.tscn",
	"res://storybook/village/bench.tscn",
	"res://storybook/village/planter.tscn",
	"res://storybook/village/annette.tscn",
	"res://storybook/village/bakery.tscn",
	"res://storybook/village/bookshop.tscn",
	"res://storybook/village/clock_house.tscn",
	"res://storybook/village/flower_shop.tscn",
	"res://storybook/village/workshop.tscn",
	"res://storybook/village/windmill.tscn",
]


func _initialize() -> void:
	call_deferred("run")


func run() -> void:
	print("%-24s %8s %8s %8s  %8s %8s  %s"
		% ["scene", "size_x", "size_y", "size_z", "ctr_x", "ctr_z", "radius"])
	for path in SCENES:
		var packed: PackedScene = load(path)
		if packed == null:
			print("FAIL: cannot load ", path)
			continue
		var node := packed.instantiate()
		# ⛔ IN THE TREE FIRST. `global_transform` on a node that was only
		# instantiated is not merely stale, it errors and returns identity --
		# so every part reports as though it sat at the origin and the whole
		# table comes out plausible and wrong.
		root.add_child(node)
		# ⛔ The AABB has to be built in the SCENE's space, not each mesh's
		# own: a prop whose parts are placed by transform (every one of
		# these) would otherwise report the size of a single plank.
		var box := AABB()
		var first := true
		for child in node.find_children("*", "MeshInstance3D", true, false):
			var mesh_instance := child as MeshInstance3D
			if mesh_instance.mesh == null:
				continue
			var local := mesh_instance.mesh.get_aabb()
			var world := mesh_instance.global_transform * local
			if first:
				box = world
				first = false
			else:
				box = box.merge(world)
		if first:
			print("FAIL: no mesh in ", path)
			root.remove_child(node)
			node.queue_free()
			continue
		var centre := box.get_center()
		# The radius a cylinder collider wants: half the larger ground span,
		# so a tree that is wider than it is deep still stops Chuck.
		var radius := maxf(box.size.x, box.size.z) * 0.5
		print("%-24s %8.2f %8.2f %8.2f  %8.2f %8.2f  %6.2f"
			% [path.get_file().get_basename(), box.size.x, box.size.y,
			   box.size.z, centre.x, centre.z, radius])
		root.remove_child(node)
		node.queue_free()
	quit(0)
