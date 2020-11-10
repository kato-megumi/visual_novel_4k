#!/usr/bin/python
# from rfb import RFBClient, RFBFactory
from twisted.python import usage, log
from twisted.internet import protocol,reactor
from twisted.application import internet, service
from visual_novel_4k.shaders import Shader
from visual_novel_4k.rfb import *
import sys,os
import time 
import pygame
import subprocess
import signal
from pygame.locals import *

MODIFIERS = {
    K_NUMLOCK:          KEY_Num_Lock,
    K_CAPSLOCK:         KEY_Caps_Lock,
    K_SCROLLOCK:        KEY_Scroll_Lock,
    K_RSHIFT:           KEY_ShiftRight,
    K_LSHIFT:           KEY_ShiftLeft,
    K_RCTRL:            KEY_ControlRight,
    K_LCTRL:            KEY_ControlLeft,
    K_RALT:             KEY_AltRight,
    K_LALT:             KEY_AltLeft,
    K_RMETA:            KEY_MetaRight,
    K_LMETA:            KEY_MetaLeft,
    K_LSUPER:           KEY_Super_L,
    K_RSUPER:           KEY_Super_R,
    K_MODE:             KEY_Hyper_R,        #???
    #~ K_HELP:             
    #~ K_PRINT:            
    K_SYSREQ:           KEY_Sys_Req,
    K_BREAK:            KEY_Pause,          #???
    K_MENU:             KEY_Hyper_L,        #???
    #~ K_POWER:            
    #~ K_EURO:             
}                        
KEYMAPPINGS = {
    K_BACKSPACE:        KEY_BackSpace,
    K_TAB:              KEY_Tab,
    K_RETURN:           KEY_Return,
    K_ESCAPE:           KEY_Escape,
    K_KP0:              KEY_KP_0,
    K_KP1:              KEY_KP_1,
    K_KP2:              KEY_KP_2,
    K_KP3:              KEY_KP_3,
    K_KP4:              KEY_KP_4,
    K_KP5:              KEY_KP_5,
    K_KP6:              KEY_KP_6,
    K_KP7:              KEY_KP_7,
    K_KP8:              KEY_KP_8,
    K_KP9:              KEY_KP_9,
    K_KP_ENTER:         KEY_KP_Enter,
    K_UP:               KEY_Up,
    K_DOWN:             KEY_Down,
    K_RIGHT:            KEY_Right,
    K_LEFT:             KEY_Left,
    K_INSERT:           KEY_Insert,
    K_DELETE:           KEY_Delete,
    K_HOME:             KEY_Home,
    K_END:              KEY_End,
    K_PAGEUP:           KEY_PageUp,
    K_PAGEDOWN:         KEY_PageDown,
    K_F1:               KEY_F1,
    K_F2:               KEY_F2,
    K_F3:               KEY_F3,
    K_F4:               KEY_F4,
    K_F5:               KEY_F5,
    K_F6:               KEY_F6,
    K_F7:               KEY_F7,
    K_F8:               KEY_F8,
    K_F9:               KEY_F9,
    K_F10:              KEY_F10,
    K_F11:              KEY_F11,
    K_F12:              KEY_F12,
    K_F13:              KEY_F13,
    K_F14:              KEY_F14,
    K_F15:              KEY_F15,
}   
class Upscale(RFBClient):
    global screen,s,display
    """dummy client"""
    def vncConnectionMade(self):
        self.setEncodings([COPY_RECTANGLE_ENCODING,RAW_ENCODING])
        self.framebufferUpdateRequest()
        self.factory.event_handler.setp(self)
        # self.now = time.time()

    def updateRectangle(self, x, y, width, height, data):
        display.blit(
            pygame.image.fromstring(data, (width, height), 'RGBX'),     #TODO color format
            (x, y)
        )
    def commitUpdate(self, rectangles = None):
        """finish series of display updates"""
        # n = time.time()
        i = pygame.image.fromstring(s.apply(display.get_view('1')),(2560,1440),'RGBX')
        screen.blit(i,(0,0))
        # print(time.time()-n,end='\t')
        # n = time.time()
        pygame.display.update([tuple(y*2 for y in x) for x in rectangles])
        # print(time.time()-n)
        self.framebufferUpdateRequest(incremental=1)

class UpscaleFactory(protocol.ClientFactory):
    """test factory"""
    def __init__(self, event_handler,password = None, shared = 0):
        self.password = password
        self.shared = shared
        self.protocol = Upscale
        self.event_handler = event_handler
    def clientConnectionFailed(self, connector, reason):
        log.msg("cannot connect to server: %r\n" % reason.getErrorMessage())
        reactor.stop()

class Event(object):
    global app,screen
    def __init__(self):
        self.protocol=None
    def setp(self,p):
        self.protocol=p
    def event_handle(self):
        alive=1
        buttons=0
        seen_events = 0
        for e in pygame.event.get():
            seen_events = 1
            if e.type == QUIT:
                alive = 0
                os.system("killall xvfb-run")
                os.system("kill -9 `pgrep "+app+"`")
                reactor.stop()
                return 0
            if self.protocol is not None:
                if e.type == KEYDOWN:
                    if e.key in MODIFIERS:
                        self.protocol.keyEvent(MODIFIERS[e.key], down=1)
                    elif e.key in KEYMAPPINGS:
                        self.protocol.keyEvent(KEYMAPPINGS[e.key])
                    elif e.unicode:
                        self.protocol.keyEvent(ord(e.unicode))
                        time.sleep(0.01)
                        self.protocol.keyEvent(ord(e.unicode), down=0)
                    else:
                        print("warning: unknown key %r" % (e))
                elif e.type == KEYUP:
                    if e.key in MODIFIERS:
                        self.protocol.keyEvent(MODIFIERS[e.key], down=0)
                    elif e.key in KEYMAPPINGS:
                        self.protocol.keyEvent(KEYMAPPINGS[e.key], down=0)
                    else:
                        key = pygame.key.name(e.key)
                        if len(key)==1: self.protocol.keyEvent(ord(key), down=0)
                        if len(key)=="space": self.protocol.keyEvent(ord(" "), down=0)
                    #~ else:
                        #~ print "unknown key %r" % (e)
                elif e.type == MOUSEMOTION:
                    buttons  = e.buttons[0] and 1
                    buttons |= e.buttons[1] and 2
                    buttons |= e.buttons[2] and 4
                    self.protocol.pointerEvent(int(e.pos[0]/2), int(e.pos[1]/2), buttons)
                    #~ print e.pos
                elif e.type == MOUSEBUTTONUP:
                    if e.button == 1: buttons &= ~1
                    if e.button == 2: buttons &= ~2
                    if e.button == 3: buttons &= ~4
                    if e.button == 4: buttons &= ~8
                    if e.button == 5: buttons &= ~16
                    self.protocol.pointerEvent(int(e.pos[0]/2), int(e.pos[1]/2), buttons)
                elif e.type == MOUSEBUTTONDOWN:
                    scroll = 0
                    if e.button == 1: buttons |= 1
                    if e.button == 2: buttons |= 2
                    if e.button == 3: buttons |= 4
                    if e.button == 4: buttons |= 8 ;scroll=1
                    if e.button == 5: buttons |= 16;scroll=1
                    self.protocol.pointerEvent(int(e.pos[0]/2), int(e.pos[1]/2), buttons)
                    if scroll==1: 
                        buttons &= ~8
                        buttons &= ~16
                        self.protocol.pointerEvent(int(e.pos[0]/2), int(e.pos[1]/2), buttons)
                elif e.type == ACTIVEEVENT:
                    if e.gain ==1:
                        self.protocol.framebufferUpdateRequest()
                        pygame.display.update()
        pygame.event.clear()
        if alive:
            # reactor.callLater(0, self.event_handle)
            reactor.callLater((not seen_events) and 0.020, self.event_handle)

def main():
    from optparse import OptionParser
    parser = OptionParser()
    parser.add_option("-d","--display",type='int',dest='display',default=720, help='original width')
    parser.add_option("-s","--screen" ,type='int',dest='screen' ,default=1440,help='upscaled width')
    parser.add_option("-o",dest='old' ,action='store_true',default=False,help='For 3:4 game')
    parser.add_option("-v",dest='vgl' ,action='store_true',default=False,help='Use virtualgl')
    opt,arg = parser.parse_args()
    global screen,s,display,app
    if len(arg)>0:
        app = arg[0]
        if opt.vgl:
            os.system("VGL_FORCEALPHA=1 VGL_DRAWABLE=pixmap xvfb-run  -l --server-args=\"-screen 0 1280x720x24\" vglrun wine explorer /desktop=name,1280x720 "+app+ " &")
        else:
            os.system("xvfb-run  -l --server-args=\"-screen 0 1280x720x24\" wine explorer /desktop=name,1280x720 "+app+ " &")
            # os.system("xvfb-run  -l --server-args=\"-screen 0 1280x720x24\" vglrun wine explorer /desktop=name,1280x720 "+app+ " > /dev/null 2>&1 &")
        time.sleep(2)
    else:
        app = ""
    os.system("x11vnc -nocursor -multiptr -display :99  > /dev/null 2>&1 &")
    # subprocess.call('x11vnc','-display',':99')
    time.sleep(1)
    #TODO
    #fullscreen
    #moar res
    #moar algo
    pygame.init()
    display = pygame.Surface((1280,720))
    screen = pygame.display.set_mode((2560,1600), DOUBLEBUF| NOFRAME, 32)
    screen.fill(0)
    pygame.display.update()
    s = Shader(1280,720)
    v = Event()
    application = service.Application("rfb test") # create Application
    vncClient = internet.TCPClient('localhost', 5900, UpscaleFactory(v)) # create the service
    vncClient.setServiceParent(application)
    vncClient.startService()
    reactor.callLater(0.1, v.event_handle)
    reactor.run()
if __name__ == '__main__':
    main()
'''
cvt 1280 720                                             
xrandr --newmode "1280x720_60.00"   74.50  1280 1344 1472 1664  720 723 728 748 -hsync +vsync
xrandr --addmode DisplayPort-1 1280x720_60.00
xrandr --addmode DisplayPort-0 1280x720_60.00 --output DisplayPort-0 --mode 1280x720_60.00 --right-of eDP
x11vnc -display :0 -clip 1280x720+2560+0 -xrandr -forever -nonc -noxdamage -repeat 

xrandr --auto
'''