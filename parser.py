import os
class Program():
    def __init__(self):
        self.content = ""
        self.in_text = [0]
        self.out_text = -2
    def add_in(self, index):
        if index not in self.in_text: 
            self.in_text.append(index)
    def add_content(self, line):
        self.content+=line.replace('HOOKED',"LUMA")
    def set_out(self, index):
        self.out_text = index
class Parser():
    def __init__(self, algo):
        self.texture_name_list = ["HOOKED", "LUMA"]
        self.prog_list = []
        self.double = False
        self.highQ = False
        self.copy = False

        with open(os.path.dirname(os.path.realpath(__file__)) + '/' + algo, 'r') as fp:
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
                    tex_name = line.split()[1]
                    if not new_prog:
                        new_prog=True
                        if program != None: self.prog_list.append(program)
                        program = Program()
                    if line[3:7] == "BIND":
                        program.add_in(self.texture_name_list.index(tex_name))
                    elif line[3:7] == "HEIG":
                        self.double = True
                    elif line[3:7] == "QUAL":
                        self.highQ = True
                    elif line[3:7] == "COPY":
                        self.copy = True
                    elif line[3:7] == "SAVE":
                        if tex_name not in self.texture_name_list:
                            self.texture_name_list.append(tex_name)
                        program.set_out(self.texture_name_list.index(tex_name)) 

                else:
                    new_prog = False
                    if program: program.add_content(line)
            self.prog_list.append(program)

        for a in self.prog_list:
            a.in_text = list(set([k-1 if k>1 else 0 for k in a.in_text]))
            a.out_text = a.out_text-2
        self.texture_name_list = self.texture_name_list[1:]
        self.prog_list[-1].set_out(len(self.texture_name_list)-1)
        