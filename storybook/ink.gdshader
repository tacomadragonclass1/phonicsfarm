shader_type spatial;

// INK — an inverted-hull outline, run as a `next_pass` on the painted shader.
//
// ⭐ The one thing in the set that no renderer supplies: DRAWING. The Cycles
// control has no line work either, which is part of why a path-traced render
// of these assets still reads as an asset pack. An outline is the cheapest
// mark-making available and it is the only lever here that changes what the
// art IS rather than how it is lit.
//
// ⛔ Inverted hull, NOT a screen-space depth edge. The project ships the
// Compatibility renderer for its WebGL2 browser build, where DEPTH_TEXTURE
// support cannot be relied on; a hull is plain geometry and works anywhere.
//
// ⛔ The known weakness is split normals. These assets are finished at a 38
// degree smoothing angle, so every hard corner carries several normals and a
// hull pushed along them tears open at exactly those corners. `width_screen`
// exists to keep the line a constant thickness on screen rather than in
// metres -- a 0.012 m line is invisible on a cottage and fat on a letter die.
render_mode cull_front, unshaded, depth_draw_opaque, shadows_disabled;

// In PIXELS now, not metres-times-a-fudge.
uniform float width_screen : hint_range(0.0, 12.0) = 3.4;
uniform vec3 ink : source_color = vec3(0.13, 0.10, 0.09);
uniform float ink_mix : hint_range(0.0, 1.0) = 0.94;

// ⭐ A DRAWN LINE IS NOT A CONSTANT WIDTH. A line of perfectly even weight
// reads as a computer-generated edge, which is the thing this is meant to
// escape. Varying the ink slightly along the line, in world space so it does
// not crawl when the camera moves, is the difference between an outline and
// a drawing.
uniform float ink_variation : hint_range(0.0, 1.0) = 0.30;

varying vec3 hull_world;

void vertex() {
	// Push along the normal in VIEW space, scaled by distance so the line
	// holds its width on screen. The camera is orthographic, so there is no
	// perspective divide to compensate for -- the scale is constant and the
	// line stays even across the whole frame, which is exactly what a drawn
	// line does and what a world-space hull fails to do.
	hull_world = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
	// ⛔⛔ THE OFFSET IS IN CLIP SPACE, NOT MODEL SPACE, and this is not a
	// refinement -- a model-space push is a FIXED NUMBER OF METRES, so the
	// same setting that draws a clean line on a 4 m cottage is wider than a
	// 5 cm berry is round. It also scales with whatever scale a prop is
	// instanced at, so two copies of one tree at 0.9 and 1.15 would carry
	// visibly different line weights.
	//
	// Pushing in clip space by a pixel count instead gives ONE line weight
	// for the whole world, which is what a drawn line is: the pen does not
	// get thicker for bigger subjects.
	POSITION = PROJECTION_MATRIX * MODELVIEW_MATRIX * vec4(VERTEX, 1.0);
	vec3 view_normal = normalize((MODELVIEW_MATRIX * vec4(NORMAL, 0.0)).xyz);
	vec2 screen_normal = (PROJECTION_MATRIX * vec4(view_normal, 0.0)).xy;
	if (length(screen_normal) > 0.0001) {
		screen_normal = normalize(screen_normal);
		POSITION.xy += screen_normal * width_screen * POSITION.w
		             / VIEWPORT_SIZE * 2.0;
	}
}

float ink_hash(vec3 p) {
	p = fract(p * 0.1031);
	p += dot(p, p.zyx + 31.32);
	return fract((p.x + p.y) * p.z);
}

void fragment() {
	// ⛔ NO ALPHA. Writing ALPHA < 1 turns this pass transparent, which in
	// the Compatibility renderer drops it out of the opaque queue and the
	// line silently never draws. The softness has to come from the ink
	// COLOUR, not from blending.
	vec3 cell = floor(hull_world * 9.0);
	float wobble = mix(1.0 - ink_variation, 1.0, ink_hash(cell));
	ALBEDO = mix(vec3(0.55, 0.55, 0.52), ink, ink_mix * wobble);
}
