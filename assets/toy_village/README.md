# Original wooden-toy geometry

`beveled_cube.obj` is a unit cube with chamfered edges, authored for Phonics Farm
by `tools/build_toy_village.py`. The six building scenes and bunting in
`village/buildings/` combine it with Godot primitive meshes and matte materials.
No external model, generated image, texture download, or new dependency is used.

The generator is an authoring aid, not a runtime requirement. Re-running it
overwrites the building scenes and cube, but never the village layout, collisions,
or spawn markers. Edit the static `.tscn` scenes directly in Godot if preferred.
