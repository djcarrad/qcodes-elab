from qcodes import param_move
from qcodes.instrument.base import Instrument
from qcodes.instrument.channel import InstrumentChannel, ChannelList
import numpy as np
import time
from qcodes.utils import validators


class MultiplexerChannel(InstrumentChannel):
    """Used to automatically add gates/channels in a Multiplexer to itself"""
    def __init__(self, parent: 'Multiplexer', name: str,volt=0,curr=0):
        super().__init__(parent,name)
        self._name = name
        if volt==0:
            raise ValueError('Need to provide a volt paramater')
        else:
            self.volt=volt
        if curr!=0:
            self.curr=curr
        

class Multiplexer(Instrument):

    # Treat an on-chip analog multiplexer as a qcodes instrument. The driver assumes a multiplexer of the form in https://arxiv.org/abs/2304.12765.
    # That is, it consists of a number of levels (lvls) each with two sets of transistors that can be either open/on or closed/off.
    # Level 1 has two transistors, level 2 has four transistors, level 3 had eight and so on.
    # The number of gates is twice the number of levels. Since the voltages to these gates needs to be applied by a 'real' instrument(s), you need to tell this instrument what those parameters are via volt_source_list
    # volt_source_list should be a list of the full parameter used to connect the multiplexer, e.g. [qdac.ch01.volt,qdac.ch02.volt,qdac.ch03.volt....]
    # You can easily generate it by using e.g. [qdac.channel(i+1).volt for i in range(16)]
    # If your instrument has current-measuring capability you can also pass these parameters via curr_list in a similar manner to volt_source_list
    # You can provide the open_volt, close_volt and stepnum (the number of steps each gate takes between the close_volt and open_volt) during initialisation, or later by addressing them as any other qcodes parameter. 

    # IMPORTANT! Note that this is for only ONE multiplexer! If you have e.g. a multiplexer and de-multiplexer on the source and drain side, respectively, you need two of these instruments.
    # It's easy enough to make a function/parameter that controls both within your notebook, and doing it like this leaves a lot more room for flexibility.

    def __init__(self,name='MPX',volt_source_list=0,curr_list=0,open_volt=1,close_volt=-1,stepnum=101,**kwargs):


        super().__init__(name,**kwargs)

        self._volt_source_list=volt_source_list
        self._curr_list=curr_list

        #Check the user hasn't done anything silly. Automatically determine the number of levels from the shape of the volt_source_list
        if self._volt_source_list==0:
            raise ValueError('Need to provide volt_source_list. It should be a list of each of the entire parameter variables used to control the multiplexer, e.g. [qdac.ch01.volt,qdac.ch02.volt,qdac.ch03.volt....]')

        if np.shape(self._volt_source_list)[0] % 2 != 0:
            raise ValueError('Number of entries in volt_source_list needs to be even!')
        
        self.lvls=int(np.shape(self._volt_source_list)[0]/2)

        if self._curr_list!=0:
            if np.shape(self._curr_list)[0]/2 != self.lvls:
                raise ValueError('Number of entries in curr_list does not match number of entries in volt_source_list')

        #Generate a library which will store the voltages and currents for each gate. The library is stored in metadata and gets passed to snapshot.
        #Also generate channels where each gate of the multiplexer can be easily addressed by its identifier, e.g. 1_1, 1_2, 2_1, 2_2 etc

        self.gates={}
        for i in range(self.lvls):
            for j in range(2):
                gatename='lvl_{}_{}'.format(i+1,j+1)
                self.gates[gatename]={'volt':self._volt_source_list[2*i+j]}
                if self._curr_list!=0:
                    self.gates[gatename]['curr']=self._curr_list[2*i+j]
                    channel=MultiplexerChannel(self,name=gatename,volt=self._volt_source_list[2*i+j],curr=self._curr_list[2*i+j])
                else:
                    channel=MultiplexerChannel(self,name=gatename,volt=self._volt_source_list[2*i+j])
                self.add_submodule(gatename,channel)

        self.metadata['volt_sources']={}
        if curr_list!=0:
            self.metadata['curr_sources']={}
        for gate in self.gates:
            self.metadata['volt_sources'][gate]=self.gates[gate]['volt'].full_name
            if curr_list!=0:
                self.metadata['curr_sources'][gate]=self.gates[gate]['curr'].full_name

        self.add_parameter(name='open_volt',
                            initial_value=open_volt,
                            get_cmd=None,
                            set_cmd=None,
                            unit='V',
                            vals=validators.Numbers())


        self.add_parameter(name='close_volt',
                            initial_value=close_volt,
                            get_cmd=None,
                            set_cmd=None,
                            unit='V',
                            vals=validators.Numbers())

        self.add_parameter(name='stepnum',
                            initial_value=stepnum,
                            get_cmd=None,
                            set_cmd=None,
                            unit='',
                            vals=validators.Ints(min_value=1))

        self.add_parameter(name='output',
                            set_cmd=self._set_mpx_output,
                            get_cmd=self._get_mpx_output,
                            unit='#',
                            vals=validators.Ints(min_value=0,max_value=2**self.lvls))

    def _convert_to_binary(self,val,binary_len):
        binary_format = '0{}b'.format(binary_len)
        return format(val,binary_format)

    def _get_mpx_output(self):
        #Checks at each level which of the two gates is open compared to the other, constructs a binary string and returns an integer corresponding to that out.

        binary_string=''
        for lvl in range(self.lvls):
            if np.abs(self.gates['lvl_{}_1'.format(lvl+1)]['volt'].get_latest() - self.gates['lvl_{}_2'.format(lvl+1)]['volt'].get_latest())<(self.open_volt()-self.close_volt())*0.1:
                raise ValueError('Gates in level {} have almost the same voltage. The multiplexer is in an indeterminite state!!'.format(lvl+1))
            elif self.gates['lvl_{}_1'.format(lvl+1)]['volt'].get_latest() > self.gates['lvl_{}_2'.format(lvl+1)]['volt'].get_latest():
                binary_string=binary_string+'0'
            else:
                binary_string=binary_string+'1'
        return int(binary_string,2)


    def _set_mpx_output(self,out):

        gate_key = self._convert_to_binary(out,self.lvls)
        
        if self.stepnum()==1:
            # Move the gates instantly
            for n in range(len(gate_key)):
                if gate_key[n] == '0':
                    if np.abs(self.gates['lvl_{}_1'.format(n+1)]['volt'].get_latest()-self.open_volt())>(self.open_volt()-self.close_volt())*0.1:
                        self.gates['lvl_{}_1'.format(n+1)]['volt'](self.open_volt())
                    if np.abs(self.gates['lvl_{}_2'.format(n+1)]['volt'].get_latest()-self.close_volt())>(self.open_volt()-self.close_volt())*0.1:
                        self.gates['lvl_{}_2'.format(n+1)]['volt'](self.close_volt())

                else:
                    if np.abs(self.gates['lvl_{}_2'.format(n+1)]['volt'].get_latest()-self.open_volt())>(self.open_volt()-self.close_volt())*0.1:
                        self.gates['lvl_{}_2'.format(n+1)]['volt'](self.open_volt())
                    if np.abs(self.gates['lvl_{}_1'.format(n+1)]['volt'].get_latest()-self.close_volt())>(self.open_volt()-self.close_volt())*0.1:
                        self.gates['lvl_{}_1'.format(n+1)]['volt'](self.close_volt())


        else:
            # Step the gates using param_move
            for n in range(len(gate_key)):
                if gate_key[n] == '0':
                    if np.abs(self.gates['lvl_{}_1'.format(n+1)]['volt'].get_latest()-self.open_volt())>(self.open_volt()-self.close_volt())*0.1:
                        param_move(self.gates['lvl_{}_1'.format(n+1)]['volt'],self.open_volt(),self.stepnum())
                    if np.abs(self.gates['lvl_{}_2'.format(n+1)]['volt'].get_latest()-self.close_volt())>(self.open_volt()-self.close_volt())*0.1:
                        param_move(self.gates['lvl_{}_2'.format(n+1)]['volt'],self.close_volt(),self.stepnum())

                else:
                    if np.abs(self.gates['lvl_{}_2'.format(n+1)]['volt'].get_latest()-self.open_volt())>(self.open_volt()-self.close_volt())*0.1:
                        param_move(self.gates['lvl_{}_2'.format(n+1)]['volt'],self.open_volt(),self.stepnum())
                    if np.abs(self.gates['lvl_{}_1'.format(n+1)]['volt'].get_latest()-self.close_volt())>(self.open_volt()-self.close_volt())*0.1:
                        param_move(self.gates['lvl_{}_1'.format(n+1)]['volt'],self.close_volt(),self.stepnum())


    def mpx_element(self,element,lvl):

        gate_key=self._convert_to_binary(element,lvl)
        # Return a binary corresponding to the element, with length of the level.

        #Then set the multiplexer down to that level
        if self.stepnum()==1:
            #Move the gates instantly
            for n in range(len(gate_key)):
                if gate_key[n] == '0':
                    if np.abs(self.gates['lvl_{}_1'.format(n+1)]['volt'].get_latest()-self.open_volt())>(self.open_volt()-self.close_volt())*0.1:
                        self.gates['lvl_{}_1'.format(n+1)]['volt'](self.open_volt())
                    if np.abs(self.gates['lvl_{}_2'.format(n+1)]['volt'].get_latest()-self.close_volt())>(self.open_volt()-self.close_volt())*0.1:
                        self.gates['lvl_{}_2'.format(n+1)]['volt'](self.close_volt())

                else:
                    if np.abs(self.gates['lvl_{}_2'.format(n+1)]['volt'].get_latest()-self.open_volt())>(self.open_volt()-self.close_volt())*0.1:
                        self.gates['lvl_{}_2'.format(n+1)]['volt'](self.open_volt())
                    if np.abs(self.gates['lvl_{}_1'.format(n+1)]['volt'].get_latest()-self.close_volt())>(self.open_volt()-self.close_volt())*0.1:
                        self.gates['lvl_{}_1'.format(n+1)]['volt'](self.close_volt())


        else:
            # Step the gates using param_move
            for n in range(len(gate_key)):
                if gate_key[n] == '0':
                    if np.abs(self.gates['lvl_{}_1'.format(n+1)]['volt'].get_latest()-self.open_volt())>(self.open_volt()-self.close_volt())*0.1:
                        param_move(self.gates['lvl_{}_1'.format(n+1)]['volt'],self.open_volt(),self.stepnum())
                    if np.abs(self.gates['lvl_{}_2'.format(n+1)]['volt'].get_latest()-self.close_volt())>(self.open_volt()-self.close_volt())*0.1:
                        param_move(self.gates['lvl_{}_2'.format(n+1)]['volt'],self.close_volt(),self.stepnum())

                else:
                    if np.abs(self.gates['lvl_{}_2'.format(n+1)]['volt'].get_latest()-self.open_volt())>(self.open_volt()-self.close_volt())*0.1:
                        param_move(self.gates['lvl_{}_2'.format(n+1)]['volt'],self.open_volt(),self.stepnum())
                    if np.abs(self.gates['lvl_{}_1'.format(n+1)]['volt'].get_latest()-self.close_volt())>(self.open_volt()-self.close_volt())*0.1:
                        param_move(self.gates['lvl_{}_1'.format(n+1)]['volt'],self.close_volt(),self.stepnum())

        #Open everything below that level.
        openlevels=[i+lvl for i in range(self.lvls-lvl)] #Missing a plus one, yes, but that's because it appears when setting the gates below...
        if self.stepnum()==1:
            #Move the gates instantly
            for n in openlevels:
                if np.abs(self.gates['lvl_{}_1'.format(n+1)]['volt'].get_latest()-self.open_volt())>(self.open_volt()-self.close_volt())*0.1:
                    self.gates['lvl_{}_1'.format(n+1)]['volt'](self.open_volt())
                if np.abs(self.gates['lvl_{}_2'.format(n+1)]['volt'].get_latest()-self.open_volt())>(self.open_volt()-self.close_volt())*0.1:
                        self.gates['lvl_{}_2'.format(n+1)]['volt'](self.open_volt())

        else:
            # Step the gates using param_move
            for n in openlevels:
                if np.abs(self.gates['lvl_{}_1'.format(n+1)]['volt'].get_latest()-self.open_volt())>(self.open_volt()-self.close_volt())*0.1:
                    param_move(self.gates['lvl_{}_1'.format(n+1)]['volt'],self.open_volt(),self.stepnum())
                if np.abs(self.gates['lvl_{}_2'.format(n+1)]['volt'].get_latest()-self.open_volt())>(self.open_volt()-self.close_volt())*0.1:
                    param_move(self.gates['lvl_{}_2'.format(n+1)]['volt'],self.open_volt(),self.stepnum())

        if element%2 == 0:
            gate_to_sweep=self.gates['lvl_{}_1'.format(lvl)]['volt']
        else:
            gate_to_sweep=self.gates['lvl_{}_2'.format(lvl)]['volt']

        print('{} set to control element {} at level {}'.format(self.name,element,lvl))
        print('Remember to set the demultiplexer correctly if you have one')

        return gate_to_sweep


    def print_all_voltages(self):
        for gate in self.gates:
            print('{}: {} V'.format(gate,self.gates[gate]['volt']()))

    def print_all_currents(self):
        if self._curr_list != 0:
            for gate in self.gates:
                print('{}: {} A'.format(gate,self.gates[gate]['curr']()))
        else:
            print('No curr_list provided on inititation')

    def set_multiple_gates(self,voltage,gate_list=0,stepnum=101):
        if gate_list==0:
            gate_list=self.gates
        if stepnum==1:
            for gate in gate_list:
                self.gates[gate]['volt'](voltage)
        else:
            for gate in gate_list:
                param_move(self.gates[gate]['volt'],voltage,stepnum)
        
        
    def GrayCode(n):

        # base case
        if (n <= 0):
            return

        # 'arr' will store all generated codes
        arr = list()

        # start with one-bit pattern
        arr.append("0")
        arr.append("1")

        # Every iteration of this loop generates
        # 2*i codes from previously generated i codes.
        i = 2
        j = 0
        while(True):

            if i >= 1 << n:
                break
         
            # Enter the prviously generated codes
            # again in arr[] in reverse order.
            # Nor arr[] has double number of codes.
            for j in range(i - 1, -1, -1):
                arr.append(arr[j])

            # append 0 to the first half
            for j in range(i):
                arr[j] = "0" + arr[j]

            # append 1 to the second half
            for j in range(i, 2 * i):
                arr[j] = "1" + arr[j]
            i = i << 1

        return arr
