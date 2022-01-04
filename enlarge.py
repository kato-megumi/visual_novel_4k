import moderngl,struct
import numpy as np
from parser import Parser
import moderngl
import numpy as np
import struct

from parser import Parser


class Shader():
    def __init__(self, width, height, context, algos=['yuv.glsl','ACNet.glsl','rgb.glsl']):
        self.width=width
        self.height=height
        self.context=context
        t = context.texture((width, height), 4, dtype = 'f1')
        t.repeat_y = False
        t.repeat_x = False
        self.texture_list = [t]
        self.fbo_list = []
        self.fbo_use = []
        self.vao_list = []
        w,h = width,height
        self.vbo = vbo = context.buffer(np.array([
                    # x    y     u  v
                    -1.0, -1.0,  0.0, 0.0,  # lower left
                    -1.0,  1.0,  0.0, 1.0,  # upper left
                    1.0,  -1.0,  1.0, 0.0,  # lower right
                    1.0,   1.0,  1.0, 1.0,  # upper right
                ], dtype="f4"))

        self.vbox = vbox = context.buffer(np.array([
                    # x    y     u  v
                    -1.0,  1.0,  0.0, 0.0,  # lower left
                    -1.0, -1.0,  0.0, 1.0,  # upper left
                    1.0,   1.0,  1.0, 0.0,  # lower right
                    1.0,  -1.0,  1.0, 1.0,  # upper right
                ], dtype="f4"))
        ver_sha = '''
        #version 450
        precision highp float;
        in vec2 vert;
        in vec2 in_text;
        out vec2 texcoord;
        void main() {
        gl_Position = vec4(vert, 0.0, 1.0);
        texcoord = in_text;
        }
        '''

        tex_num = 0
        currentH = height
        currentW = width
        data_index = 0
        for algo_index, algo in enumerate(algos):
            p = Parser(algo)
            for tex_name in p.texture_name_list[1:]:
                t = context.texture((currentW, currentH), 4, dtype = 'f2')
                t.repeat_y = False
                t.repeat_x = False
                self.fbo_list.append(context.framebuffer(t))
                self.texture_list.append(t)
            currentH *= 2 if p.double else 1
            currentW *= 2 if p.double else 1
            t = context.texture((currentW, currentH), 4, dtype = 'f2') 
            t.repeat_y = False
            t.repeat_x = False
            self.texture_list.append(t)
            self.fbo_list.append(context.framebuffer(t) if algo_index != len(algos)-1  else context.screen)
            for prog in p.prog_list:
                define = '''#version 450\nout vec4 color;\nin vec2 texcoord;'''
                for t in prog.in_text:
                    name = p.texture_name_list[t]
                    define+=f'''
                        precision highp sampler2D;
                        uniform sampler2D {name};
                        #define {name}_pos texcoord
                        #define {name}_tex(pos) texture({name}, pos)
                        #define {name}_pt pt
                        #define {name}_size size
                        #define {name}_texOff(off) {name}_tex({name}_pos + {name}_pt * vec2(off))
                        '''
                define += '''
                layout(binding = ''' + str(4 + data_index) + ''') buffer data
                {
                    vec2 pt;
                    vec2 size;
                };
                '''
                fra_sha = define + prog.content + "\nvoid main() {color = hook();}"
                program = context.program(vertex_shader=ver_sha,fragment_shader=fra_sha)
                vao = context.simple_vertex_array(program, vbo if algo_index != len(algos)-1 else vbox, 'vert', 'in_text')
                self.vao_list.append(vao)
                for t in prog.in_text:
                    name = p.texture_name_list[t]
                    try: 
                        program[name] = tex_num + t
                    except: pass
                self.fbo_use.append(prog.out_text + tex_num)
            tex_num += len(p.texture_name_list)
            if p.double: data_index += 1

        for t in range(len(self.texture_list)):
            self.texture_list[t].use(t)


        for i in range(4):
            w = width*(2**(i))
            h = height*(2**(i))
            context.buffer(struct.pack('4f',*[1/w,1/h,w,h])).bind_to_storage_buffer(i+4)
        self.size = (currentW, currentH)


    def apply(self,bound):
        w,h = self.width,self.height
        x1,y1,x2,y2 = bound
        padding = 8
        x1,y1,x2,y2 = max(x1-padding,0),h-max(y1-padding,0),min(x2+padding,w),h-min(y2+padding,h)
        self.vbo.write(np.array([
                    # x    y     u  v
                    2*x1/w-1, 1-2*y2/h,  x1/w, 1-y2/h,  # lower left
                    2*x1/w-1, 1-2*y1/h,  x1/w, 1-y1/h,  # upper left
                    2*x2/w-1, 1-2*y2/h,  x2/w, 1-y2/h,  # lower right
                    2*x2/w-1, 1-2*y1/h,  x2/w, 1-y1/h,  # upper right
                ], dtype="f4"))
        
        x1,y1,x2,y2 = bound
        self.vbox.write(np.array([
                    # x    y     u  v
                    2*x1/w-1, 1-2*y2/h,  x1/w, y2/h,  # lower left
                    2*x1/w-1, 1-2*y1/h,  x1/w, y1/h,  # upper left
                    2*x2/w-1, 1-2*y2/h,  x2/w, y2/h,  # lower right
                    2*x2/w-1, 1-2*y1/h,  x2/w, y1/h,  # upper right
                ], dtype="f4"))
        
        for i in range(len(self.vao_list)):
            self.fbo_list[self.fbo_use[i]].use()
            for t in range(len(self.texture_list)):
                self.texture_list[t].use(t)
            # if i==len(self.vao_list)-2: self.texture_list[-2].use(len(self.texture_list)-2)
            self.vao_list[i].render(moderngl.TRIANGLE_STRIP)



    def blit(self,data,x,y,width,height):
        self.texture_list[0].write(data,viewport=(x,y,width,height))
