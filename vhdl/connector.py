# Created by Marko Kosunen 20190801 marko.kosunen@aalto.fi

import os
from thesdk import *
from vhdl import *

## Class for storing signals in wide sense, including IO's
class vhdl_connector(thesdk):
    @property
    def _classfile(self):
        return os.path.dirname(os.path.realpath(__file__)) + "/"+__name__

    def __init__(self,**kwargs):
        self.name=kwargs.get('name','')
        self.cls=kwargs.get('cls','')   # in,out,inout,signal
        self.type=kwargs.get('type','') # e.g. std_logic_vector 
        self.ll=kwargs.get('ll',0)      # Bus range left limit 0 by default
        self.rl=kwargs.get('ll',0)      # Bus bus range right limit 0 by default
        self.init=kwargs.get('init','') # Initial value
        self.connect=kwargs.get('connect',None) # Can be vhdl connector, would be recursive
        self.ioformat=kwargs.get('ioformat','%d')# By default, connectors are handles as integers in file io.

    @property
    def width(self):
        self._width=self.ll-self.rl+1
        return self._width

    @property
    def definition(self):
        if self.width==1:
            self._definition='%s %s;\n' %(self.cls, self.name)
        elif self.type:
            self._definition='%s %s [%s:%s] %s;\n' %(self.cls, self.type, self.ll, self.rl, self.name)
        else:
            self._definition='%s [%s:%s] %s;\n' %(self.cls, self.ll, self.rl, self.name)
        return self._definition
    
    @property
    def assignment(self,**kwargs):
        self._assignment='assign %s = %s;\n' %(self.name,self.connect.name)
        return self._assignment

    def nbassign(self,**kwargs):
        time=kwargs.get('time','')
        value=kwargs.get('value',self.connect.name)
        if time:
            return '%s = #%s %s;\n' %(self.name,time, value)
        else:
            return '%s = %s;\n' %(self.name, value)

    def bassign(self):
        time=kwargs.get('time','')
        value=kwargs.get('value',self.connect.name)
        if time:
            return '%s <= #%s %s;\n' %(self.name,time, value)
        else:
            return '%s <= %s;\n' %(self.name, value)

class vhdl_connector_bundle(Bundle):
    def __init__(self,**kwargs):
        super(vhdl_connector_bundle,self).__init__(**kwargs)

    def new(self,**kwargs):
        name=kwargs.get('name','')
        cls=kwargs.get('cls','')           # Input,output,inout,reg,wire,reg,wire
        type=kwargs.get('type','')         # signed
        ll=kwargs.get('ll',0)              # Bus range left limit 0 by default
        rl=kwargs.get('ll',0)              # Bus bus range right limit 0 by default
        init=kwargs.get('init','')         # Initial value
        connect=kwargs.get('connect',None) # Can't be vhdl connector by default. Would be recursive
        self.Members[name]=vhdl_connector(name=name,cls=cls,type=type,ll=ll,rl=rl,init=init,connect=connect)

    def update(self,**kwargs):
        #[TODO]: Write sanity checks
        bundle=kwargs.get('bundle',None)
        self.Members.update(bundle)
    
    def mv(self,**kwargs):
        #[TODO]: Write sanity checks
        fro=kwargs.get('fro')
        to=kwargs.get('to')
        self.Members[to]=self.Members.pop(fro)
        self.Members[to].name=to

    def connect(self,**kwargs):
        #[TODO]: Write sanity checks
        match=kwargs.get('match',r".*")  #By default, connect all
        conname=kwargs.get('connect')
        for name, value in self.Members.items():
            if re.match(match,name):
                value.connect=self.Members[conname]

    def init(self,**kwargs):
        #[TODO]: Write sanity checks
        match=kwargs.get('match',r".*")  #By default, connect all
        initval=kwargs.get('init','')
        for name, value in self.Members.items():
            if re.match(match,name):
                value.init=initval

    def assign(self,**kwargs):
        #[TODO]: Write sanity checks
        match=kwargs.get('match',r".*") #By default, assign all
        assignments=''
        for name, value in self.Members.items():
            if re.match(match,name):
                assignments=assignments+value.assignment
        return intend(text=assignments, level=kwargs.get('level',0))

    def vhdl_inits(self,**kwargs):
        #[TODO]: Write sanity checks
        inits=''
        match=kwargs.get('match',r".*") #By default, assign all
        for name, val in self.Members.items():
            if re.match(match,name) and val.init:
                inits=inits+'%s = %s;\n' %(val.name,val.init)
        return intend(text=inits, level=kwargs.get('level',0))

    def list(self,**kwargs):
        #[TODO]: Write sanity checks
        names=kwargs.get('names','')
        connectors=[]
        if names:
            for name in names:
                connectors.append(self.Members[name])
        return connectors

#Helper to intend text blocks
def intend(**kwargs):
    textout=''
    nspaces=4
    for line in (kwargs.get('text')).splitlines():
        for _ in range(nspaces*kwargs.get('level')):
            line=line+' '
        textout=textout+line+'\n'
    return textout

if __name__=="__main__":
    pass

