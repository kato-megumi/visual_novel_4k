#version 440
#define tex1D texture
#define tex3D texture
#define LUT_POS(x, lut_size) mix(0.5 / (lut_size), 1.0 - 0.5 / (lut_size), (x))
out vec4 out_color;
in vec2 texcoord0;
layout(std140, binding=0) uniform UBO {
layout(offset=0) vec2 texture_size0;
layout(offset=16) mat2 texture_rot0;
layout(offset=48) vec2 texture_off0;
layout(offset=56) vec2 pixel_size0;
};
uniform sampler2D lut;
uniform sampler2D texture0;
void main() {
vec4 color = vec4(0.0, 0.0, 0.0, 1.0);
#undef tex
#undef texmap
#define tex texture0
#define texmap texmap0
vec2 pos = texcoord0;
vec2 size = texture_size0;
vec2 pt = pixel_size0;
// first pass
color = vec4(0.0);
{
vec2 dir = vec2(0.0, 1.0);
pt *= dir;
float fcoord = dot(fract(pos * size - vec2(0.5)), dir);
vec2 base = pos - fcoord * pt - pt * vec2(2.0);
vec4 c;
float ypos = LUT_POS(fcoord, 64.0);
float weights[6];
c = texture(lut, vec2(0.250000, ypos));
weights[0] = c[0];
weights[1] = c[1];
weights[2] = c[2];
weights[3] = c[3];
c = texture(lut, vec2(0.750000, ypos));
weights[4] = c[0];
weights[5] = c[1];
// scaler samples
c = texture(tex, base + pt * vec2(0.0));
color += vec4(weights[0]) * c;
c = texture(tex, base + pt * vec2(1.0));
color += vec4(weights[1]) * c;
c = texture(tex, base + pt * vec2(2.0));
color += vec4(weights[2]) * c;
c = texture(tex, base + pt * vec2(3.0));
color += vec4(weights[3]) * c;
c = texture(tex, base + pt * vec2(4.0));
color += vec4(weights[4]) * c;
c = texture(tex, base + pt * vec2(5.0));
color += vec4(weights[5]) * c;
}
color *= 1.000000;
out_color = color;
}