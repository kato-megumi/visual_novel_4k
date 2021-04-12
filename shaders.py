import moderngl
import numpy as np

import time, struct,os

class Shader():
    def __init__(self, width, height,ctx,algo='/Anime4K_Upscale_CNN_L_x2.glsl',scale=2):
        d = os.path.dirname(os.path.realpath(__file__))
        self.width = width
        self.height = height
        self.scale = scale
        context = ctx
        # context = moderngl.create_standalone_context(require=430)

        #deband shader 
        with open(d+"/deband.glsl", 'r') as fp:
            deband_glsl = fp.read()

        tex = context.texture((self.width, self.height), 4)
        tex.bind_to_image(0)

        with open(d+algo, 'r') as fp:
            content = fp.read()
        list_glsl = content.split('//////////////////////////////////////////////////////////////////')
        tex_num = int(list_glsl[0])
        list_glsl = list_glsl[1:]

        self.shader_list = []
        self.tex_list = []

        # deband
        self.shader_list.append(context.compute_shader(deband_glsl))
        self.deband_tex = context.texture((self.width, self.height), 4,dtype='f1')
        self.deband_tex.bind_to_image(30)

        for i in range(tex_num):
            tex = context.texture((self.width, self.height), 4,dtype='f1' if i==0 else 'f2')
            tex.bind_to_image(i)
            self.tex_list.append(tex)
        self.tex_list.append(context.texture((self.width*scale, self.height*scale), 4,dtype='f2'))
        self.tex_list.append(context.texture((self.width*scale, self.height*scale), 4,dtype='f1'))
        self.tex_list[-2].bind_to_image(tex_num) # second last texture
        self.tex_list[-1].bind_to_image(tex_num+1) # last texture


        self.shader_list.append(context.compute_shader(
        '''
        #version 430

        layout (local_size_x = 32, local_size_y = 24) in;
        layout(rgba8, binding=30) readonly uniform image2D inTex;
        layout(rgba16f, binding=1) writeonly uniform image2D destTex;

        #define Kb 0.0722
        #define Kr 0.2126
        #define Kg 1.0 - Kr - Kb
        #define YUV(rgb)   ( mat3(0.2126,-0.09991,0.615,0.7152,-0.33609,-0.55861,0.0722,0.436,-0.05639)*rgb )
        #define InvYUV(yuv)   ( mat3(1,1,1,0,-0.21482,2.12798,1.28033,-0.38059,0)*yuv )
        void main() {
            ivec2 pt = ivec2(gl_GlobalInvocationID.xy);
            vec3 yuv = YUV(imageLoad(inTex,pt).bgr);
            imageStore(destTex,pt,vec4(yuv,1));
        }'''))

        for x in list_glsl:
            self.shader_list.append(context.compute_shader(x))

        self.shader_list.append(context.compute_shader(
        '''
        #version 430

        layout (local_size_x = 32, local_size_y = 24) in;
        layout(rgba16f, binding='''+str(tex_num)+''') uniform image2D inTex;
        layout(rgba8, binding='''+str(tex_num+1)+''') uniform image2D destTex;

        #define Kb 0.0722
        #define Kr 0.2126
        #define Kg 1.0 - Kr - Kb
        #define YUV(rgb)   ( mat3(0.2126,-0.09991,0.615,0.7152,-0.33609,-0.55861,0.0722,0.436,-0.05639)*rgb )
        #define InvYUV(yuv)   ( mat3(1,1,1,0,-0.21482,2.12798,1.28033,-0.38059,0)*yuv )
        void main() {
            ivec2 pt = ivec2(gl_GlobalInvocationID.xy);
            vec3 rgb = InvYUV(imageLoad(inTex,pt).rgb);
            imageStore(destTex,pt,vec4(rgb,1));
        }'''))

        # https://blubberquark.tumblr.com/post/185013752945/using-moderngl-for-post-processing-shaders-with
        texture_coordinates = [0, 1,  1, 1, 0, 0,  1, 0]
        world_coordinates = [-1, -1,  1, -1, -1,  1,  1,  1]
        render_indices = [0, 1, 2,1, 2, 3]

        prog = ctx.program(vertex_shader='''
        #version 430
        in vec2 vert;
        in vec2 in_text;
        out vec2 v_text;
        void main() {
        gl_Position = vec4(vert, 0.0, 1.0);
        v_text = in_text;
        }
        ''',
        fragment_shader='''
        #version 430
        precision mediump float;
        uniform sampler2D Texture;
        in vec2 v_text;
        out vec3 f_color;
        vec4 cubic(float v){
            vec4 n = vec4(1.0, 2.0, 3.0, 4.0) - v;
            vec4 s = n * n * n;
            float x = s.x;
            float y = s.y - 4.0 * s.x;
            float z = s.z - 4.0 * s.y + 6.0 * s.x;
            float w = 6.0 - x - y - z;
            return vec4(x, y, z, w) * (1.0/6.0);
        }

        vec4 textureBicubic(sampler2D sampler, vec2 texCoords){

            ivec2 texSize = textureSize(sampler, 0);
            vec2 invTexSize = 1.0 / texSize;

            texCoords = texCoords * texSize - 0.5;


            vec2 fxy = fract(texCoords);
            texCoords -= fxy;

            vec4 xcubic = cubic(fxy.x);
            vec4 ycubic = cubic(fxy.y);

            vec4 c = texCoords.xxyy + vec2 (-0.5, +1.5).xyxy;

            vec4 s = vec4(xcubic.xz + xcubic.yw, ycubic.xz + ycubic.yw);
            vec4 offset = c + vec4 (xcubic.yw, ycubic.yw) / s;

            offset *= invTexSize.xxyy;

            vec4 sample0 = texture(sampler, offset.xz);
            vec4 sample1 = texture(sampler, offset.yz);
            vec4 sample2 = texture(sampler, offset.xw);
            vec4 sample3 = texture(sampler, offset.yw);

            float sx = s.x / (s.x + s.y);
            float sy = s.z / (s.z + s.w);

            return mix(
            mix(sample3, sample2, sx), mix(sample1, sample0, sx)
            , sy);
        }

        void main() {
        f_color = textureBicubic(Texture,v_text).rgb;
        }
        ''')

        vbo = ctx.buffer(struct.pack('8f', *world_coordinates))
        uvmap = ctx.buffer(struct.pack('8f', *texture_coordinates))
        ibo= ctx.buffer(struct.pack('6I', *render_indices))

        vao_content = [
            (vbo, '2f', 'vert'),
            (uvmap, '2f', 'in_text')
        ]
        self.vao = ctx.vertex_array(prog, vao_content, ibo)
        
    def apply(self):
        width=self.width
        height=self.height
        W,H = int(np.ceil(width/32)),int(np.ceil(height/24))
        W2,H2 = int(np.ceil(width/32*self.scale)),int(np.ceil(height/24*self.scale))
        for a in self.shader_list[:-1]:
            a.run(W,H,1)
        self.shader_list[-1].run(W2,H2,1)
        self.tex_list[-1].use()
        self.vao.render()


    def blit(self,data,x,y,width,height):
        self.tex_list[0].write(data,viewport=(x,y,width,height))

def test2(q=560,w=160):
    import pygame
    from PIL import Image
    img = Image.open('/tmp/out.png').convert('RGBX')
    size2 = (img.size[0]*2,img.size[1]*2)
    imgbyte = img.tobytes()
    s = Shader(img.size[0],img.size[1])
    a = s.apply(imgbyte)

    screen = pygame.Surface(size2)
    screen.blit(pygame.image.fromstring(a,size2,'RGBX'),(0,0))

    a = s.apply(imgbyte,q,w,(1050,300))
    screen.blit(pygame.image.fromstring(a,size2,'RGBX'),(2500,1400))
    img_out = Image.frombytes("RGBA",size2,screen.get_view('1').raw).convert("RGB")
    img_out2 = Image.frombytes("RGBA",size2,a).convert("RGB")
    img_out.show()
    img_out2.show()

def test(q=560,w=160):
    # import pygame
    from PIL import Image
    img = Image.open('/tmp/out.png').convert('RGBX')
    size2 = (img.size[0]*2,img.size[1]*2)
    imgbyte = img.tobytes()
    s = Shader(img.size[0],img.size[1])
    a = s.apply(imgbyte)

    img_out = Image.frombytes("RGBA",img.size,a).convert("RGB")
    img_out = Image.frombytes("RGBA",size2,a).convert("RGB")
    img_out.show()
if __name__ == '__main__':
    test()