# Vhdl class 
# Provides vhdl-related properties and methods for other classes TheSDK
#
# Adding this class as a superclass enforces the definitions for vhdl in the
# subclasses
##############################################################################
# Last modification by Marko Kosunen, marko.kosunen@aalto.fi, 22.01.2018 12:53
import os
import sys
if not (os.path.abspath('../../thesdk') in sys.path):
    sys.path.append(os.path.abspath('../../thesdk'))
from thesdk import *
import subprocess
import shlex

class vhdl(thesdk):
    #Subclass of TheSDK for logging method
    #These need to be converted to abstact properties
    def __init__(self):
        self.model           =[]
        self.classfile       =[]
        self._vhdlcmd        =[]
        self._name           =[]
        self._entitypath     =[] 
        self._vhdlsrcpath    =[]
        self._vhdlsimpath    =[]
        self._vhdlworkpath   =[]
        self._vhdlparameters =dict([])
        self._infile         =[]
        self._outfile        =[]
        #To define the vhdl model and simulation paths

    def def_vhdl(self): 
        #These could be in TheSDK
        self._name=os.path.splitext(os.path.basename(self._classfile))[0]
        self._entitypath= os.path.dirname(os.path.dirname(self._classfile))

        if (self.model is 'vhdl'):
            self._vhdlsrcpath  =  self._entitypath + '/' + self.model 
        if not (os.path.exists(self._entitypath+'/Simulations')):
            os.mkdir(self._entitypath + '/Simulations')
        
        self._vhdlsimpath  = self._entitypath +'/Simulations/vhdlsim'

        if not (os.path.exists(self._vhdlsimpath)):
            os.mkdir(self._vhdlsimpath)
        self._vhdlworkpath    =  self._vhdlsimpath +'/work'

    def get_vhdlcmd(self):
        #the could be gathered to vhdl class in some way but they are now here for clarity
        submission = ' bsub -K '  
        vhdllibcmd =  'vlib ' +  self._vhdlworkpath + ' && sleep 2'
        vhdllibmapcmd = 'vmap work ' + self._vhdlworkpath
        if (self.model is 'vhdl'):
            vhdlcompcmd = ( 'vcom -work work ' + self._vhdlsrcpath + '/' + self._name + '.vhd '
                           + self._vhdlsrcpath + '/tb_' + self._name +'.vhd ')
            gstring=' '.join([ ('-g ' + str(param) +'='+ str(val)) for param,val in iter(self._vhdlparameters.items()) ])
            vhdlsimcmd = ( 'vsim -64 -batch -t 1ps -voptargs=+acc -g g_infile=' + self._infile
                          + ' -g g_outfile=' + self._outfile + ' ' + gstring 
                          +' work.tb_' + self._name  + ' -do "run -all; quit;"')

            
            vhdlcmd =  submission + vhdllibcmd  +  ' && ' + vhdllibmapcmd + ' && ' + vhdlcompcmd +  ' && ' + vhdlsimcmd
        else:
            vhdlcmd=[]
        return vhdlcmd

    def run_vhdl(self):
        self._vhdlcmd=self.get_vhdlcmd()
        while not os.path.isfile(self._infile):
            self.print_log({'type':'I', 'msg':"Wait infile to appear"})
            time.sleep(5)
        try:
            os.remove(self._outfile)
        except:
            pass
        self.print_log({'type':'I', 'msg':"Running external command %s\n" %(self._vhdlcmd) })
        subprocess.call(shlex.split(self._vhdlcmd));
        
        while not os.path.isfile(self._outfile):
            self.print_log({'type':'I', 'msg':"Wait outfile to appear"})
            time.sleep(5)
        os.remove(self._infile)
        #This must be in every subclass file. Works also with __init__.py files
        #self._classfile=os.path.dirname(os.path.realpath(__file__)) + "/"+__name__


