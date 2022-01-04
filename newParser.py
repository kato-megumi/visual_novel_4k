from dataclasses import dataclass
import os, uuid, hashlib

def md5(s):
    return hashlib.md5(s.encode('utf-8')).hexdigest()[:10]

@dataclass
class NamedTexture:
    name: str
    width: int
    height: int

class Program():
    def __init__(self):
        self.content = ""
        self.inTexture = []
        self.outTexture = ""
        self.replacePair = []
    def add_in(self, textureName):
        if textureName not in self.inTexture: 
            self.inTexture.append(textureName)
    def add_content(self, line):
        self.content += line
    def set_out(self, textureName):
        self.outTexture = textureName

class Parser():
    def __init__(self, w, h):
        self.width = w
        self.height = h
        self.textureList = [NamedTexture("FirstTex", w, h)] # input texture
        self.programList = []
        self.id = ord('a')

    def isInTextureList(self, name):
        for x in self.textureList:
            if x.name == name:
                return True
        return False

    def textureIndex(self, name):
        for index,x in enumerate(self.textureList):
            if x.name == name:
                return index
        return -1
    
    def textureFromName(self, name):
        for index,x in enumerate(self.textureList):
            if x.name == name:
                return x
        return -1

    def parse(self, algo):
        with open(os.path.dirname(os.path.realpath(__file__)) + '/' + algo, 'r') as fp:
            Id = chr(self.id)# 'a' + str(uuid.uuid4())[:7]
            self.id+=1
            inputTexture = self.textureList[-1].name
            new_prog = False
            comment = False
            program = None
            for line in fp:
                if comment:
                    if"*/" in line: comment = False
                    continue
                if "/*" in line: 
                    comment = True
                    continue 
                # not really work in every case

                if line[:3] == "//!":
                    if not new_prog:
                        new_prog = True
                        double = False
                        program = Program()
                        saveTextureName = Id
                        self.programList.append(program)
                    if line[3:7] == "BIND" or line[3:7] == "HOOK":
                        tempName = line.split()[1]
                        if tempName == "HOOKED" or tempName == "MAIN" or tempName == "LUMA":
                            program.add_in(inputTexture)
                            program.replacePair.append((tempName,inputTexture))
                        else:
                            program.add_in(f'{Id}_{md5(tempName)}')
                            program.replacePair.append((tempName,f'{Id}_{md5(tempName)}'))
                    elif line[3:7] == "HEIG" and "2 *" in line:
                        double = True
                    elif line[3:7] == "SAVE":
                        saveTextureName = f'{Id}_{md5(line.split()[1])}'

                else:
                    if new_prog:
                        new_prog = False
                        if double:
                            self.width *= 2
                            self.height *= 2
                        if not self.isInTextureList(saveTextureName):
                            self.textureList.append(NamedTexture(saveTextureName, self.width, self.height))
                        program.set_out(saveTextureName) 
                    
                    if program: 
                        for pair in program.replacePair:
                            line = line.replace(pair[0]+'_',pair[1]+'_')
                        program.add_content(line)
            

if __name__ == '__main__':
    parser = Parser(1280, 720)
    parser.parse('glsl/Upscale/Anime4K_Upscale_CNN_x2_S.glsl')
