"""
====
VHDL
====

Simulation interface package for The System Development Kit

Provides utilities to import VHDL entities to python environment and 
automatically generate testbenches for the most common simulation cases.

Initially written by Marko Kosunen, marko.kosunen@aalto.fi, 2017.

"""
import os
import sys
import subprocess
import shlex
from abc import * 
from thesdk import *
import numpy as np
import pandas as pd
from functools import reduce

class vhdl(thesdk,metaclass=abc.ABCMeta):
    """Adding this class as a superclass enforces the definitions 
    for vhdl simulations in the subclasses.
    
    """

    def __init__(self):
        #These need to be converted to abstact properties
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
        """This must be in every subclass of thesdk"""
        return os.path.dirname(os.path.realpath(__file__)) + "/"+__name__

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
    def iofile_bundle(self):
        if not hasattr(self,'_iofile_bundle'):
            self._iofile_bundle=Bundle()
        return self._iofile_bundle

    @iofile_bundle.setter
    def iofile_bundle(self,value):
        self._iofile_bundle=value

    @iofile_bundle.deleter
    def iofile_bundle(self):
        for name, val in self.iofile_bundle.Members.items():
            if val.preserve:
                self.print_log(type="I", msg="Preserve_value is %s" %(val.preserve))
                self.print_log(type="I", msg="Preserving file %s" %(val.file))
            else:
                val.remove()
        self.iofile_bundle.Members.clear()
        self.iofile_bundle=None

    @property 
    def vhdl_submission(self):
        if not hasattr(self, '_vhdl_submission'):
            try:
                self._vhdl_submission=thesdk.GLOBALS['LSFSUBMISSION']+' '
            except:
                self.print_log(type='W',msg='Variable thesdk.GLOBALS incorrectly defined. _vhdl_submission defaults to empty string and simulation is ran in localhost.')
                self._vhdl_submission=''

        if hasattr(self,'_interactive_vhdl'):
            return self._vhdl_submission

        return self._vhdl_submission

    @property
    def name(self):
        if not hasattr(self, '_name'):
            #_classfile is an abstract property that must be defined in the class.
            self._name=os.path.splitext(os.path.basename(self._classfile))[0]
        return self._name
    #No setter, no deleter.

    @property
    def entitypath(self):
        if not hasattr(self, '_entitypath'):
            #_classfile is an abstract property that must be defined in the class.
            self._entitypath= os.path.dirname(os.path.dirname(self._classfile))
        return self._entitypath
    #No setter, no deleter.

    @property
    def vhdlsrcpath(self):
        if not hasattr(self, '_vhdlsrcpath'):
            #_classfile is an abstract property that must be defined in the class.
            self._vhdlsrcpath  =  self.entitypath + '/vhdl'
        return self._vhdlsrcpath
    #No setter, no deleter.

    @property
    def vhdlsimpath(self):
        if not hasattr(self, '_vhdlsimpath'):
            #_classfile is an abstract property that must be defined in the class.
            if not (os.path.exists(self.entitypath+'/Simulations')):
                os.mkdir(self.entitypath + '/Simulations')
        self._vhdlsimpath  = self.entitypath +'/Simulations/vhdlsim'
        if not (os.path.exists(self._vhdlsimpath)):
            os.mkdir(self._vhdlsimpath)
        return self._vhdlsimpath
    #No setter, no deleter.

    @property
    def vhdlworkpath(self):
        if not hasattr(self, '_vhdlworkpath'):
            self._vhdlworkpath    =  self.vhdlsimpath +'/work'
        return self._vhdlworkpath

    @property
    def vhdlparameters(self): 
        if not hasattr(self, '_vhdlparameters'):
            self._vhdlparameters =dict([])
        return self._vhdlparameters
    @vhdlparameters.setter
    def vhdlparameters(self,value): 
            self._vhdlparameters = value
    @vhdlparameters.deleter
    def vhdlparameters(self): 
            self._vhdlparameters = None

    @property
    def vhdlmodulefiles(self):
        if not hasattr(self, '_vhdlmodulefiles'):
            self._vhdlmodulefiles =list([])
        return self._vhdlmodulefiles
    @vhdlmodulefiles.setter
    def vhdlmodulefiles(self,value): 
            self._vhdlmodulefiles = value
    @vhdlmodulefiles.deleter
    def vhdlmodulefiles(self): 
            self._vhdlmodulefiles = None 

    #This is obsoleted
    def def_vhdl(self):
        self.print_log(type='I',msg='Command def_vhdl() is obsoleted. It does nothing.')

    @property
    def vhdlcmd(self):
        submission=self.vhdl_submission
        if not hasattr(self, '_vhdlcmd'):
            vhdllibcmd =  'vlib ' +  self.vhdlworkpath + ' && sleep 2'
            vhdllibmapcmd = 'vmap work ' + self.vhdlworkpath
            vhdlmodulesstring=' '.join([ self.vhdlsrcpath + '/'+ str(param) for param in self.vhdlmodulefiles])
            vhdlcompcmd = ( 'vcom -work work ' + self.vhdlsrcpath + '/' + self.name + '.vhd '
                           + self.vhdlsrcpath + '/tb_' + self.name +'.vhd' + ' ' + vhdlmodulesstring )

            gstring=' '.join([ ('-g ' + str(param) +'='+ str(val)) for param,val in iter(self.vhdlparameters.items()) ])
            
            fileparams=''
            for name, file in self._iofile_bundle.Members.items():
                fileparams=fileparams+' '+file.simparam

            if not self.interactive_vhdl:
                vhdlsimcmd = ( 'vsim -64 -batch -t 1ps -voptargs=+acc ' + fileparams + ' ' + gstring
                          +' work.tb_' + self.name  + ' -do "run -all; quit;"')
            else:
                submission="" #Local execution
                vhdlsimcmd = ( 'vsim -64 -t 1ps -novopt ' + fileparams + ' ' + gstring
                          +' work.tb_' + self.name)

            self._vhdlcmd =   vhdllibcmd  +  ' && ' + vhdllibmapcmd + ' && ' + vhdlcompcmd +  ' && ' + submission + vhdlsimcmd
        return self._vhdlcmd
    # Just to give the freedom to set this if needed
    @vhdlcmd.setter
    def vhdlcmd(self,value):
        self._vhdlcmd=value
    @vhdlcmd.deleter
    def vhdlcmd(self):
        self._vhdlcmd=None

    def run_vhdl(self):
        filetimeout=60 #File appearance timeout in seconds
        count=0
        files_ok=False
        while not files_ok:
            count +=1
            if count >5:
                self.print_log(type='F', msg="VHDL infile writing timeout")
            for name, file in self.iofile_bundle.Members.items(): 
                if file.dir=='in':
                    files_ok=True
                    files_ok=files_ok and os.path.isfile(file.file)
            time.sleep(int(filetimeout/5))

        #Remove existing output files before execution
        for name, file in self.iofile_bundle.Members.items(): 
            if file.dir=='out':
                try:
                    #Still keep the file in the infiles list
                    os.remove(file.name)
                except:
                    pass

        self.print_log(type='I', msg="Running external command %s\n" %(self.vhdlcmd) )

        if self.interactive_vhdl:
            self.print_log(type='I', msg="""Running vhdl simulation in interactive mode.
                Add the probes in the simulation as you wish.
                To finish the simulation, run the simulation to end and exit.""")

        subprocess.check_output(self.vhdlcmd, shell=True);

        count=0
        files_ok=False
        while not files_ok:
            count +=1
            if count >5:
                self.print_log(type='F', msg="VHDL outfile timeout")
            time.sleep(int(filetimeout/5))
            for name, file in self.iofile_bundle.Members.items(): 
                if file.dir=='out':
                    files_ok=True
                    files_ok=files_ok and os.path.isfile(file.file)

        #for name, file in self.iofile_bundle.Members.items(): 
        #    if file.dir=='in':
        #        try:
        #            file.remove()
        #        except:
        #            pass


