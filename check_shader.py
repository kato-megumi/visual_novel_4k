import pygame
import sys
from pygame.locals import *
import moderngl
from enlarge import Shader
from PIL import Image

w,h = 1280,720

pygame.init()
screen = pygame.display.set_mode((2*w,2*h), DOUBLEBUF| NOFRAME | OPENGL, 32)
ctx = moderngl.create_context()

clock = pygame.time.Clock()
frametime = [0]*100

s = Shader(w,h,ctx,algos=['glsl/Restore/Anime4K_Restore_CNN_Soft_L.glsl','glsl/Upscale/Anime4K_Upscale_CNN_x2_L.glsl','nop.glsl'])

data = Image.open('/mnt/Nas/Drive/FileShare/UpscaleAlgoTest/Hapymaher2.png').convert("RGBX").tobytes()

s.blit(data, 0,0,w,h)
s.apply([0,0,w,h])
pygame.display.flip()

while 1:
    for event in pygame.event.get():
        if event.type == pygame.QUIT: sys.exit()
    s.apply([0,0,w,h])
    pygame.display.flip()
    frametime.pop(0)
    frametime.append(clock.tick())
    print(sum(frametime)/100,end="\r")

# 'glsl/Restore/Anime4K_Restore_CNN_Soft_VL.glsl','glsl/Upscale/Anime4K_Upscale_CNN_x2_L.glsl' 69.4
# 'glsl/Restore/Anime4K_Restore_CNN_Soft_L.glsl','glsl/Upscale/Anime4K_Upscale_CNN_x2_L.glsl'  46.9

# 'glsl/Restore/Anime4K_Restore_CNN_Soft_VL.glsl','glsl/Upscale/Anime4K_Upscale_CNN_x2_S.glsl  52.1
# 'glsl/Restore/Anime4K_Restore_CNN_Soft_L.glsl','glsl/Upscale/Anime4K_Upscale_CNN_x2_S.glsl'  30.3  
# 'glsl/Upscale/Anime4K_Upscale_CNN_x2_S.glsl                                                  8.36

# 'glsl/Restore/Anime4K_Restore_CNN_Soft_VL.glsl','glsl/Upscale/Anime4K_Upscale_CNN_x2_VL.glsl 94.5
# 'glsl/Restore/Anime4K_Restore_CNN_Soft_L.glsl','glsl/Upscale/Anime4K_Upscale_CNN_x2_VL.glsl' 71.2
# 'glsl/Upscale/Anime4K_Upscale_CNN_x2_VL.glsl                                                 51.61
