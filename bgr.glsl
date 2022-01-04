//!BIND HOOKED
vec4 hook() {
    vec3 rgb = HOOKED_tex(HOOKED_pos).bgr;
    return vec4(rgb, 0);
}