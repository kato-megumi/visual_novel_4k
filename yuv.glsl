//!QUALITY HIGH

#define YUV(rgb)   ( mat3(0.2126,-0.09991,0.615,0.7152,-0.33609,-0.55861,0.0722,0.436,-0.05639)*rgb )
#define InvYUV(yuv)   ( mat3(1,1,1,0,-0.21482,2.12798,1.28033,-0.38059,0)*yuv )
vec4 hook() {
    vec3 rgb = YUV(HOOKED_tex(HOOKED_pos).bgr);
    return vec4(rgb,1);
}