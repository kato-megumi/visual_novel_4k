import moderngl
import numpy as np

import time, struct,os

class Shader():
    def __init__(self, width, height,algo='/Anime4K_Upscale_CNN_L_x2.glsl'):
        d = os.path.dirname(os.path.realpath(__file__))
        self.width = width
        self.height = height
        context = moderngl.create_standalone_context(require=430)
        self.buffer = context.buffer(reserve=8)
        self.buffer.bind_to_storage_buffer(20)
        tex = context.texture((self.width, self.height), 4)
        tex.bind_to_image(0)

        with open(d+"/Anime4K_Upscale_CNN_L_x2.glsl", 'r') as fp:
            content = fp.read()
        glsl = content.split('//////////////////////////////////////////////////////////////////')

        self.shader_list = []
        self.tex_list = [tex]

        self.shader_list.append(context.compute_shader(
        '''
        #version 430

        layout (local_size_x = 16, local_size_y = 16) in;
        layout(rgba8, binding=0) readonly uniform image2D inTex;
        layout(rgba16f, binding=1) writeonly uniform image2D destTex;
        layout(binding = 20) buffer pos
        {
            ivec2 p;
        };
        #define Kb 0.0722
        #define Kr 0.2126
        #define Kg 1.0 - Kr - Kb
        #define YUV(rgb)   ( mat3(0.2126,-0.09991,0.615,0.7152,-0.33609,-0.55861,0.0722,0.436,-0.05639)*rgb )
        #define InvYUV(yuv)   ( mat3(1,1,1,0,-0.21482,2.12798,1.28033,-0.38059,0)*yuv )
        void main() {
            ivec2 pt = ivec2(gl_GlobalInvocationID.xy);
            vec3 yuv = YUV(imageLoad(inTex,pt+p).rgb);
            imageStore(destTex,pt,vec4(yuv,1));
        }'''))

        self.tex_list.append(context.texture((self.width, self.height), 4,dtype='f2'))
        self.tex_list[-1].bind_to_image(1)
        for x in range(len(glsl)-1):
            self.shader_list.append(context.compute_shader(glsl[x]))
            self.tex_list.append(context.texture((self.width, self.height), 4,dtype='f2'))
            self.tex_list[-1].bind_to_image(2+x)

        self.shader_list.append(context.compute_shader(glsl[-1]))
        self.tex_list.append(context.texture((self.width*2, self.height*2), 4,dtype='f2'))
        self.tex_list[-1].bind_to_image(len(glsl)+1)

        self.shader_list.append(context.compute_shader(
        '''
        #version 430

        layout (local_size_x = 16, local_size_y = 16) in;
        layout(rgba16f, binding='''+str(len(glsl)+1)+''') uniform image2D inTex;
        layout(rgba8, binding='''+str(len(glsl)+2)+''') uniform image2D destTex;

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
        self.tex_list.append(context.texture((self.width*2, self.height*2), 4))
        self.tex_list[-1].bind_to_image(len(glsl)+2)
    def apply(self,string,width=0,height=0,pos=(0,0)):
        self.tex_list[0].write(string)
        self.buffer.write(struct.pack("<2I", *pos))
        if width==0:
            width=self.width
            height=self.height
        W,H = int(np.ceil(width/16)),int(np.ceil(height/16))
        W2,H2 = int(np.ceil(width/8)),int(np.ceil(height/8))
        for a in self.shader_list[:-1]:
            a.run(W,H,1)
        self.shader_list[-1].run(W2,H2,1)
        # print(W2,H2)
        # ret = self.tex_list[-1].read()
        # return ret,(W2*16,H2*16)
        return self.tex_list[-1].read()

def test(q=160,w=160):
    import pygame
    from PIL import Image
    img = Image.open('out.png').convert('RGBX')
    size2 = (img.size[0]*2,img.size[1]*2)
    imgbyte = img.tobytes()
    s = Shader(img.size[0],img.size[1])
    a = s.apply(imgbyte)

    screen = pygame.Surface(size2)
    screen.blit(pygame.image.fromstring(a,size2,'RGBX'),(0,0))

    a = s.apply(imgbyte,q,w,(1250,700))
    screen.blit(pygame.image.fromstring(a,size2,'RGBX'),(2500,1400),(0,0,70,70))
    img_out = Image.frombytes("RGBA",size2,screen.get_view('1').raw).convert("RGB")
    img_out2 = Image.frombytes("RGBA",size2,a).convert("RGB")
    img_out.show()
    img_out2.show()
if __name__ == '__main__':
    test()