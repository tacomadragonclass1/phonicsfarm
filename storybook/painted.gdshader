shader_type spatial;

// The PAINTED surface model -- the first lever out of the low-poly look.
//
// ⛔ What it replaces: every storybook asset reaches the engine as a
// StandardMaterial3D carrying one albedo texture at roughness ~0.92, metallic
// 0, no normal map and no custom shading. A roof, a tree and the ground all
// shade identically, so the only thing separating two objects is hue. That is
// the asset-pack recipe exactly, and remodelling never escapes it.
//
// ⛔⛔ DO NOT WRITE A CUSTOM light(). The first version of this file did, to
// get a shaped terminator and a tinted shadow, and in the COMPATIBILITY
// renderer -- which this project ships, because the web export is WebGL2 --
// it silently produced near-flat output. Measured, not guessed: NORMAL varied
// correctly inside light() and LIGHT was correctly constant for a directional
// light, yet dot(NORMAL, LIGHT) came back in a 0.10..0.18 band across every
// surface in the scene, and all cast shadows disappeared even though
// ATTENUATION on its own rendered them perfectly. The conventions do not hold
// there. Everything below is built on Godot's OWN lighting instead, which is
// why shadows work.
//
// So the three painted qualities are got a different way:
//
//   1. A SHAPED TERMINATOR -- `diffuse_toon`, a built-in, which does band in
//      Compatibility. Verified by render.
//   2. A SHADOW THAT IS A DIFFERENT COLOUR, not the same colour darker. Done
//      with LIGHT, not with shader maths: a warm key against a cool ambient
//      means the unlit side is lit by the sky and goes cool on its own. It is
//      also the physically true reason shadows are blue.
//   3. SURFACE INFORMATION. The real complaint about this set is that a
//      painted thing has marks in it and these have none -- the terrain
//      carries 16 texels per metre against a 142 px/m camera, so it CANNOT
//      hold detail no matter what is baked into it. The grain below is added
//      per-pixel in world space, so it is independent of texel density and
//      costs no rebake. It is a stopgap that happens to be a real fix.
render_mode blend_mix, depth_draw_opaque, cull_back, specular_disabled, diffuse_toon;

uniform sampler2D albedo_tex : source_color, filter_linear_mipmap;

group_uniforms Grain;
// Scale is in world metres, so a wall and the ground get the SAME size of
// mark -- which is what makes it read as one painted world rather than as
// per-object noise.
uniform float grain_scale = 5.5;
uniform float grain_strength : hint_range(0.0, 1.5) = 0.085;
uniform float grain_warm : hint_range(0.0, 1.0) = 0.35;

// 0 = PATINA: isotropic marks. Weathering -- rain, moss, wear. It belongs to
//     the object and says how long the object has been standing there.
// 1 = BRUSHWORK: marks with a DIRECTION. It belongs to the picture, not to
//     the object, and says somebody painted this.
//
// ⛔ The failure mode of brushwork is "slapdash", and slapdash is not caused
// by strokes being visible -- it is caused by strokes being INCONSISTENT.
// Random per-object directions, mixed stroke lengths and marks that ignore
// the form all read as mess. So the direction here is DERIVED from the
// surface rather than chosen: every vertical face is stroked horizontally
// around the form, the way a trowel or a loaded brush actually moves, and
// every horizontal face is stroked along one fixed world axis. Two surfaces
// meeting at a corner agree about where the strokes go, because they are
// both asking the same question of their own normal.
uniform int grain_mode : hint_range(0, 1) = 0;
uniform float grain_stretch : hint_range(1.0, 12.0) = 6.0;

group_uniforms Rim;
// The sky catching a top edge. Small -- seasoning, not a feature.
uniform float rim_power : hint_range(0.5, 8.0) = 3.0;
uniform float rim_strength : hint_range(0.0, 1.0) = 0.16;
uniform vec3 rim_tint : source_color = vec3(0.72, 0.82, 1.0);

varying vec3 world_pos;
varying vec3 world_normal;

void vertex() {
	world_pos = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
	world_normal = normalize((MODEL_MATRIX * vec4(NORMAL, 0.0)).xyz);
}

float hash13(vec3 p) {
	p = fract(p * 0.1031);
	p += dot(p, p.zyx + 31.32);
	return fract((p.x + p.y) * p.z);
}

float vnoise(vec3 p) {
	vec3 i = floor(p);
	vec3 f = fract(p);
	f = f * f * (3.0 - 2.0 * f);
	float n000 = hash13(i);
	float n100 = hash13(i + vec3(1, 0, 0));
	float n010 = hash13(i + vec3(0, 1, 0));
	float n110 = hash13(i + vec3(1, 1, 0));
	float n001 = hash13(i + vec3(0, 0, 1));
	float n101 = hash13(i + vec3(1, 0, 1));
	float n011 = hash13(i + vec3(0, 1, 1));
	float n111 = hash13(i + vec3(1, 1, 1));
	return mix(mix(mix(n000, n100, f.x), mix(n010, n110, f.x), f.y),
	           mix(mix(n001, n101, f.x), mix(n011, n111, f.x), f.y), f.z);
}

void fragment() {
	// ⛔ MANUAL sRGB DECODE, and it is not optional. Godot's glTF import does
	// not mark an embedded base-colour texture as sRGB, which is why every
	// asset carries `storybook_surface.gd` to force it on a
	// StandardMaterial3D. A ShaderMaterial has no such flag, so without this
	// the whole scene comes out a gamma too bright -- measured before as
	// meadow green reading (254, 255, 179) instead of (149, 203, 89).
	vec3 base = texture(albedo_tex, UV).rgb;
	vec3 lo = base / 12.92;
	vec3 hi = pow((base + 0.055) / 1.055, vec3(2.4));
	base = mix(lo, hi, step(vec3(0.04045), base));

	float n;
	if (grain_mode == 1) {
		// A frame that lies IN the surface. `tangent` runs horizontally
		// around a wall and along world X on a floor; `bitangent` crosses
		// it. Stretching the lookup along the tangent turns round marks
		// into strokes without any per-object authoring.
		vec3 nrm = normalize(world_normal);
		vec3 tangent = cross(nrm, vec3(0.0, 1.0, 0.0));
		// ⛔ Degenerate on a level floor, where the normal IS up. Falling
		// back to a fixed axis keeps the ground's strokes consistent with
		// each other instead of spinning wherever the cross product
		// collapses.
		tangent = length(tangent) < 0.05 ? vec3(1.0, 0.0, 0.0)
		                                 : normalize(tangent);
		vec3 bitangent = normalize(cross(nrm, tangent));
		float u = dot(world_pos, tangent);
		float v = dot(world_pos, bitangent);
		// Long and thin: the along-stroke frequency is divided down, the
		// across-stroke frequency is not.
		float body = vnoise(vec3(u * grain_scale / grain_stretch,
		                         v * grain_scale, 0.0));
		// A second, finer pass along the SAME direction -- bristle marks
		// inside the stroke. Crossing it with a different direction is what
		// makes procedural brushwork look like static.
		float bristle = vnoise(vec3(u * grain_scale / grain_stretch * 2.3,
		                            v * grain_scale * 2.6, 7.7));
		n = (body * 0.74 + bristle * 0.26 - 0.5) * 2.0;
		// Shape the mark so it has edges. A stroke is laid down and lifted;
		// a gradient is a stain.
		n = sign(n) * smoothstep(0.08, 0.72, abs(n));
	} else {
		// Two octaves, the second offset and finer: one gives a wash, two
		// give something that reads as weathering rather than as dirt.
		n = vnoise(world_pos * grain_scale) * 0.65
		  + vnoise(world_pos * grain_scale * 2.7 + 11.3) * 0.35;
		n = (n - 0.5) * 2.0;
	}
	// ⭐ A painted mark changes HUE as well as value. Lightening and
	// darkening alone reads as noise; warming where it lifts and cooling
	// where it sinks reads as pigment.
	vec3 shift = mix(vec3(1.0), vec3(1.06, 1.0, 0.93), grain_warm * n);
	ALBEDO = clamp(base * (1.0 + n * grain_strength) * shift, vec3(0.0), vec3(1.0));

	ROUGHNESS = 1.0;
	METALLIC = 0.0;

	float rim = pow(1.0 - clamp(dot(normalize(NORMAL), normalize(VIEW)),
	                            0.0, 1.0), rim_power);
	// Only on upward-facing edges: the sky is above, so a rim light under a
	// sill is a mistake the eye catches immediately.
	rim *= clamp(world_normal.y * 0.5 + 0.5, 0.0, 1.0);
	EMISSION = rim_tint * rim * rim_strength;
}
