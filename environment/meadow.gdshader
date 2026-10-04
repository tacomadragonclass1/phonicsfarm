shader_type spatial;
render_mode specular_disabled;

uniform vec4 grass_color : source_color = vec4(0.40, 0.53, 0.32, 1.0);
uniform bool paths = true;
uniform vec4 path_color : source_color = vec4(0.64, 0.54, 0.37, 1.0);
varying vec2 board;

float hash(vec2 p) {
	return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453);
}
float noise(vec2 p) {
	vec2 i = floor(p);
	vec2 f = fract(p);
	f = f * f * (3.0 - 2.0 * f);
	return mix(mix(hash(i), hash(i + vec2(1, 0)), f.x),
		mix(hash(i + vec2(0, 1)), hash(i + vec2(1, 1)), f.x), f.y);
}
float lane(vec2 p, vec2 a, vec2 b) {
	vec2 v = b - a;
	return length(p - a - v * clamp(dot(p - a, v) / dot(v, v), 0.0, 1.0));
}
void vertex() {
	vec3 world = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
	board = vec2(world.x - world.z, world.x + world.z) * 0.70710678;
}
void fragment() {
	float broad = noise(board * 0.30);
	float grain = noise(board * 16.0);
	vec3 meadow = grass_color.rgb * (0.93 + broad * 0.13 + grain * 0.025);
	float dirt = 0.0;
	if (paths) {
		float d = lane(board, vec2(0, 3.8), vec2(0, -58.8));
		d = min(d, lane(board, vec2(-9.6, -58.8), vec2(1.4, -58.8)));
		d = min(d, lane(board, vec2(-9.6, -58.8), vec2(-9.6, -44.0)));
		d = min(d, lane(board, vec2(0, -42.6), vec2(6.1, -42.6)));
		d = min(d, lane(board, vec2(0, -46.5), vec2(-9.6, -46.5)));
		// A low-contrast oval gives the word-building station a place in the meadow.
		float square = (length((board - vec2(0, 0.3)) / vec2(6.1, 2.3)) - 1.0) * 2.0;
		d = min(d - 0.85, square);
		dirt = 1.0 - smoothstep(-0.12, 0.18, d + (noise(board * 2.0) - 0.5) * 0.18);
	}
	vec3 sand = path_color.rgb * (0.97 + broad * 0.05 + grain * 0.025);
	ALBEDO = mix(meadow, sand, dirt * 0.87);
	ROUGHNESS = 1.0;
}
