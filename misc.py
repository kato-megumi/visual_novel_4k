import numpy as np

vertexShader = '''
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

def fragmentShader(names, index, content):
    define = '''#version 450\nout vec4 color;\nin vec2 texcoord;'''
    for name in names:
        define += f'''
            precision highp sampler2D;
            uniform sampler2D {name};
            #define {name}_pos texcoord
            #define {name}_tex(pos) texture({name}, pos)
            #define {name}_pt pt
            #define {name}_size size
            #define {name}_texOff(off) {name}_tex({name}_pos + {name}_pt * vec2(off))
            '''
    define += '''
        layout(binding = ''' + str(index) + ''') buffer data
        {
            vec2 pt;
            vec2 size;
        };
        '''
    return define + content + "\nvoid main() {color = hook();}"

def calculate_vbo(bound: tuple, size: tuple, vbo, vbox, padding = 8):
    x1, y1, x2, y2 = bound
    w, h = size

    vbox.write(np.array([
        # x    y     u  v
        2 * x1 / w - 1, 1 - 2 * y2 / h, x1 / w, y2 / h,  # lower left
        2 * x1 / w - 1, 1 - 2 * y1 / h, x1 / w, y1 / h,  # upper left
        2 * x2 / w - 1, 1 - 2 * y2 / h, x2 / w, y2 / h,  # lower right
        2 * x2 / w - 1, 1 - 2 * y1 / h, x2 / w, y1 / h,  # upper right
    ], dtype="f4"))

    x1, y1, x2, y2 = max(x1 - padding, 0), h - max(y1 - padding, 0), min(x2 + padding, w), h - min(y2 + padding, h)
    vbo.write(np.array([
        # x    y     u  v
        2 * x1 / w - 1, 1 - 2 * y2 / h, x1 / w, 1 - y2 / h,  # lower left
        2 * x1 / w - 1, 1 - 2 * y1 / h, x1 / w, 1 - y1 / h,  # upper left
        2 * x2 / w - 1, 1 - 2 * y2 / h, x2 / w, 1 - y2 / h,  # lower right
        2 * x2 / w - 1, 1 - 2 * y1 / h, x2 / w, 1 - y1 / h,  # upper right
    ], dtype="f4"))
