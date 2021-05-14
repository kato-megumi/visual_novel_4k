#version 430
layout (local_size_x = 32, local_size_y = 24) in;
layout(rgba8, binding=0)  uniform image2D inTex;
layout(rgba8, binding=30)  uniform image2D destTex;
layout(binding = 40) buffer pos
{
    ivec4 p;
};
// GLSL debanding shader, use as: source-shader=path/to/deband.glsl
// (Loosely based on flash3kyuu_deband, but expanded to multiple iterations)

//------------ Configuration section ------------
// The threshold of difference below which a pixel is considered to be part of
// a gradient. Higher = more debanding, but setting it too high diminishes image
// details.
#define THRESHOLD 64

// The range (in source pixels) at which to sample for neighbours. Higher values
// will find more gradients, but lower values will deband more aggressively.
#define RANGE 10

// The number of debanding iterations to perform. Each iteration samples from
// random positions, so increasing the number of iterations is likely to
// increase the debanding quality. Conversely, it slows the shader down.
// (Each iteration will use a multiple of the configured RANGE, and a
// successively lower THRESHOLD - so setting it much higher has little effect)
#define ITERATIONS 3

// (Optional) Add some extra noise to the image. This significantly helps cover
// up remaining banding and blocking artifacts, at comparatively little visual
// quality. Higher = more grain. Setting it to 0 disables the effect.
#define GRAIN 0

// Note: If performance is too slow, try eg. RANGE=16 ITERATIONS=2. In general,
// an increase in the number of ITERATIONS should roughly correspond to a
// decrease in RANGE and perhaps an increase in THRESHOLD.
//------------ End of configuration ------------

// Wide usage friendly PRNG, shamelessly stolen from a GLSL tricks forum post
float mod289(float x)  { return x - floor(x / 289.0) * 289.0; }
float permute(float x) { return mod289((34.0*x + 1.0) * x); }
float rand(float x)    { return fract(x / 41.0); }

// Helper: Calculate a stochastic approximation of the avg color around a pixel
vec4 average(ivec2 pt, float range, inout float h){
    float dist = rand(h) * range;     h = permute(h);
    float dir  = rand(h) * 6.2831853; h = permute(h);
    vec2 o = dist * vec2(cos(dir), sin(dir));
    vec4 a = imageLoad(inTex,pt + ivec2( o.x, o.y));
    vec4 b = imageLoad(inTex,pt + ivec2( o.x,-o.y));
    vec4 c = imageLoad(inTex,pt + ivec2(-o.x, o.y));
    vec4 d = imageLoad(inTex,pt + ivec2(-o.x,-o.y));
    return (a+b+c+d)/4;
}

void main() {
    // Initialize the PRNG by hashing the position + a random uniform
    float h;
    ivec2 pt = ivec2(gl_GlobalInvocationID.xy);
    if ((pt.x < p.x) || (pt.y < p.y) || (pt.x > p.z) || pt.y > p.w) return;
    vec3 m = vec3(pt, 8.8) + vec3(1.0);
    h = permute(permute(permute(m.x)+m.y)+m.z);
    // Sample the source pixel
    vec4 col = imageLoad(inTex,pt);

    for (int i = 1; i <= ITERATIONS; i++) {
        vec4 avg = average(pt, i*RANGE, h);
        vec4 diff = abs(col - avg);
        col = mix(avg, col, greaterThan(diff, vec4(THRESHOLD/(i*16384.0))));
    }
    vec3 noise;
    noise.x = rand(h); h = permute(h);
    noise.y = rand(h); h = permute(h);
    noise.z = rand(h); h = permute(h);
    col.rgb += (GRAIN/8192.0) * (noise - vec3(0.5));

    imageStore(destTex,pt,col);
}
// vim: set ft=glsl:
