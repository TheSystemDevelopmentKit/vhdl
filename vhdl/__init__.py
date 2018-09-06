# Vhdl class 
# Provides vhdl-related properties and methods for other classes TheSDK
#
# Adding this class as a superclass enforces the definitions for vhdl in the
# subclasses
##############################################################################
# Last modification by Marko Kosunen, marko.kosunen@aalto.fi, 06.09.2018 14:26
import os
import sys
import subprocess
import shlex
from abc import * 
from thesdk import *
import numpy as np
import pandas as pd
from functools import reduce

class vhdl_iofile(thesdk):
    def __init__(self,parent=None,**kwargs):
        if parent==None:
            self.print_log({'type':'F', 'msg':"Parent of VHDL input file not given"})
        try:  
            rndpart=os.path.basename(tempfile.mkstemp()[1])
            self.name=kwargs.get('name') 
            self.file=parent._vhdlsimpath +'/' + self.name + '_' + rndpart +'.txt'
        except:
            self.print_log({'type':'F', 'msg':"VHDL IO file definition failed"})

        self.data=kwargs.get('data',[])
        self.simparam=kwargs.get('param','-g g_file_' + kwargs.get('name') + '=' + self.file)
        self.datatype=kwargs.get('datatype',int)
        self.dir=kwargs.get('dir','out')    #Files are output files by default, and direction is 
                                            # changed to 'in' when written 
        if hasattr(parent,'preserve_iofiles'):
            self.preserve=parent.preserve_iofiles
        else:
            self.preserve=False

        #TODO: Needs a check to eliminate duplicate entries to iofiles
        parent.iofiles.append(self)

    def write(self,**kwargs):
        self.dir='in'  # Only input files are written
        #Parse the rows to split complex numbers
        data=kwargs.get('data',self.data)
        datatype=kwargs.get('dtype',self.datatype)
        parsed=[]
        for i in range(data.shape[1]):
            if i==0:
               if np.iscomplex(data[0,i]) or np.iscomplexobj(data[0,i]) :
                   parsed=np.r_['1',np.real(data[:,i]).reshape(-1,1),np.imag(data[:,i].reshape(-1,1))]
               else:
                   parsed=np.r_['1',data[:,i].reshape(-1,1)]
            else:
               if np.iscomplex(data[0,i]) or np.iscomplexobj(data[0,i]) :
                   parsed=np.r_['1',parsed,np.real(data[:,i]).reshape(-1,1),np.imag(data[:,i].reshape(-1,1))]
               else:
                   parsed=np.r_['1',data[:,i].reshape(-1,1)]
                   parsed=np.r_['1',parsed,data[:,i].reshape(-1,1)]

        df=pd.DataFrame(parsed,dtype=datatype)
        df.to_csv(path_or_buf=self.file,sep="\t",index=False,header=False)
        time.sleep(10)
        
    def read(self,**kwargs):
        fid=open(self.file,'r')
        datatype=kwargs.get('dtype',self.datatype)
        readd = pd.read_csv(fid,dtype=object,sep='\t')
        self.data=readd.values
        fid.close()

    def remove(self):
        if self.preserve:
            self.print_log({'type':"I", 'msg':"Preserve_value is %s" %(self.preserve)})
            self.print_log({'type':"I", 'msg':"Preserving file %s" %(self.file)})
        else:
            try:
                os.remove(self.file)
            except:
                pass


class vhdl(thesdk,metaclass=abc.ABCMeta):
    #These need to be converted to abstact properties
    def __init__(self):
        self.model           =[]
        self._vhdlcmd        =[]
        self._name           =[]
        self._entitypath     =[] 
        self._vhdlsrcpath    =[]
        self._vhdlsimpath    =[]
        self._vhdlworkpath   =[]
        self._vhdlmodulefiles =list([])
        self._vhdlparameters =dict([])
        self._infile         =[]
        self._outfile        =[]

    @property
    @abstractmethod
    def _classfile(self):
        return os.path.dirname(os.path.realpath(__file__)) + "/"+__name__
    #This must be in every subclass file.
    #@property
    #def _classfile(self):
    #    return os.path.dirname(os.path.realpath(__file__)) + "/"+__name__

    @property
    def preserve_iofiles(self):
        if hasattr(self,'_preserve_iofiles'):
            return self._preserve_iofiles
        else:
            self._preserve_iofiles=False
        return self._preserve_iofiles

    @preserve_iofiles.setter
    def preserve_iofiles(self,value):
        self._preserve_iofiles=value

    @property
    def interactive_vhdl(self):
        if hasattr(self,'_interactive_vhdl'):
            return self._interactive_vhdl
        else:
            self._interactive_vhdl=False
        return self._interactive_vhdl

    @interactive_vhdl.setter
    def interactive_vhdl(self,value):
        self._interactive_vhdl=value
    
    # This property utilises vhdl_iofile class to maintain list of io-files
    # that  are automatically assigned to vhdlcmd
    @property
    def iofiles(self):
        if hasattr(self,'_iofiles'):
            return self._iofiles
        else:
            self._iofiles=list([])
            return self._iofiles

    @iofiles.setter
    def iofiles(self,value):
        self._iofiles=list[value]

    @iofiles.deleter
    def iofiles(self):
        for i in self.iofiles:
            if i.preserve:
                self.print_log({'type':"I", 'msg':"Preserve_value is %s" %(i.preserve)})
                self.print_log({'type':"I", 'msg':"Preserving file %s" %(i.file)})
            else:
                i.remove()
                self._iofiles=None

    def def_vhdl(self):
        if not hasattr(self, '_vhdlparameters'):
            self._vhdlparameters =dict([])
        if not hasattr(self, '_vhdlmodulefiles'):
            self._vhdlmodulefiles =list([])

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
        submission = ' bsub -K '  
        vhdllibcmd =  'vlib ' +  self._vhdlworkpath + ' && sleep 2'
        vhdllibmapcmd = 'vmap work ' + self._vhdlworkpath
        if (self.model is 'vhdl'):
            vhdlmodulesstring=' '.join([ self._vhdlsrcpath + '/'+ str(param) for param in self._vhdlmodulefiles])
            vhdlcompcmd = ( 'vcom -work work ' + self._vhdlsrcpath + '/' + self._name + '.vhd '
                           + self._vhdlsrcpath + '/tb_' + self._name +'.vhd' + ' ' + vhdlmodulesstring )
            gstring=' '.join([ ('-g ' + str(param) +'='+ str(val)) for param,val in iter(self._vhdlparameters.items()) ])
            if hasattr(self,'_infile') or hasattr(self,'_outfile'):
                self.print_log({'type':'W', 'msg':'OBSOLETE CODE: _infile and _outfile properties are\n'                    +'replaced by iofiles property enabling multiple files and '
                    +'automating the definitions. Use that instead.'})
                
                if not self.interactive_vhdl:
                    vhdlsimcmd = ( 'vsim -64 -batch -t 1ps -voptargs=+acc -g g_infile=' + self._infile
                              + ' -g g_outfile=' + self._outfile + ' ' + gstring 
                              +' work.tb_' + self._name  + ' -do "run -all; quit;"')
                else:
                    submission="" #Local execution
                    vhdlsimcmd = ( 'vsim -64 -t 1ps -novopt -g g_infile=' + self._infile
                              + ' -g g_outfile=' + self._outfile + ' ' + gstring 
                              +' work.tb_' + self._name)

            
            elif ( not ( hasattr(self,'_infile') or  hasattr(self,'_outfile') )) and hasattr(self,'iofiles'):
                #fileparams=reduce(lambda x,y:x.simparam+' '+y.simparam,self.iofiles)
                fileparams=''
                for file in self.iofiles:
                    fileparams=fileparams+' '+file.simparam

                if not self.interactive_vhdl:
                    vhdlsimcmd = ( 'vsim -64 -batch -t 1ps -voptargs=+acc ' + fileparams + ' ' + gstring
                              +' work.tb_' + self._name  + ' -do "run -all; quit;"')
                else:
                    submission="" #Local execution
                    vhdlsimcmd = ( 'vsim -64 -t 1ps -novopt ' + fileparams + ' ' + gstring
                              +' work.tb_' + self._name)

            vhdlcmd =  submission + vhdllibcmd  +  ' && ' + vhdllibmapcmd + ' && ' + vhdlcompcmd +  ' && ' + vhdlsimcmd
            if self.interactive_vhdl:
                self.print_log({'type':'F', 'msg':"Interactive vhdl not yet supported"})
                self.print_log({'type':'I', 'msg':"""Running vhdl simulation in interactive mode\n
                    Add the probes in the simulation as you wish.\n
                    To finish the simulation, run the simulation to end and exit."""})
        else:
            vhdlcmd=[]
        return vhdlcmd

    def run_vhdl(self):
        self._vhdlcmd=self.get_vhdlcmd()
        filetimeout=30 #File appearance timeout in seconds
        count=0
        #This is to ensure operation of obsoleted code, to be removed
        if hasattr(self,'_infile'):
            while not os.path.isfile(self._infile):
                count +=1
                if count >5:
                    self.print_log({'type':'F', 'msg':"VHDL infile writing timeout"})
                time.sleep(int(filetimeout/5))
        else:
            files_ok=False
            while not files_ok:
                count +=1
                if count >5:
                    self.print_log({'type':'F', 'msg':"VHDL infile writing timeout"})
                for file in list(filter(lambda x:x.dir=='in',self.iofiles)):
                    files_ok=True
                    files_ok=files_ok and os.path.isfile(file.file)
                time.sleep(int(filetimeout/5))

        #Remove existing output files before execution
        if hasattr(self,'_outfile'):
            try:
                os.remove(self._outfile)
            except:
                pass
        else:
            for file in list(filter(lambda x:x.dir=='out',self.iofiles)):
                try:
                    #Still keep the file in the infiles list
                    os.remove(file.name)
                except:
                    pass

        self.print_log({'type':'I', 'msg':"Running external command %s\n" %(self._vhdlcmd) })
        subprocess.check_output(shlex.split(self._vhdlcmd));
        #subprocess.run(shlex.split(self._vhdlcmd));
        
        count=0
        #This is to ensure operation of obsoleted code, to be removed
        if hasattr(self,'_outfile'):
            while not os.path.isfile(self._outfile):
                count +=1
                if count >5:
                    self.print_log({'type':'F', 'msg':"VHDL outfile timeout"})
                time.sleep(int(filetimeout/5))
            if not self.preserve_iofiles:
                os.remove(self._infile)
        else:
            files_ok=False
            while not files_ok:
                count +=1
                if count >5:
                    self.print_log({'type':'F', 'msg':"VHDL outfile timeout"})
                time.sleep(int(filetimeout/5))
                for file in list(filter(lambda x:x.dir=='out',self.iofiles)):
                    files_ok=True
                    files_ok=files_ok and os.path.isfile(file.file)

            for file in list(filter(lambda x:x.dir=='in',self.iofiles)):
                try:
                    file.remove()
                except:
                    pass

