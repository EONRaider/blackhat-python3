from immlib import *

class cc_hook(LogBpHook):
    
    def __init__(self):
        
        LogBpHook.__init__(self)
        self.imm = Debugger()
        
    def run(self,regs):

        self.imm.log("%08x" % regs['EIP'],regs['EIP'])
        self.imm.deleteBreakpoint(regs['EIP'])    
        
        return 
    
def main(args):
    
    imm = Debugger()

    calc = imm.getModule("calc.exe")
    imm.analyseCode(calc.getCodebase())

    functions = imm.getAllFunctions(calc.getCodebase())

    hooker = cc_hook()
    
    for function in functions:
        hooker.add("%08x" % function, function)
            
    return "Tracking %d functions." % len(functions)
