import qcodes as qc
from qcodes import param_move as device_move
import numpy as np
import time

def mpx_out(lvls, out, instruments,keys=0,open_volt=1,close_volt=-2,stepnum=101):
    #convert to binary
    # 0 means gate 1 positive gate 2 negative
    # 1 menas gate 1 negative gate 2 positive
    
    # QDAC channel key #
    if keys==0:
        ins1=instruments[0]
        ins2=instruments[1]
        keys={'skey0': [ins1.channel(17).volt,ins1.channel(15).volt,ins1.channel(13).volt,ins1.channel(11).volt,ins1.channel(9).volt,ins1.channel(7).volt,ins1.channel(5).volt,ins1.channel(3).volt,ins1.channel(1).volt],
        'skey1': [ins1.channel(18).volt,ins1.channel(16).volt,ins1.channel(14).volt,ins1.channel(12).volt,ins1.channel(10).volt,ins1.channel(8).volt,ins1.channel(6).volt,ins1.channel(4).volt,ins1.channel(2).volt],
        'dkey0': [ins2.channel(11).volt,ins2.channel(9).volt,ins2.channel(7).volt,ins2.channel(5).volt,ins2.channel(3).volt,ins2.channel(1).volt,ins1.channel(23).volt,ins1.channel(21).volt,ins1.channel(19).volt],
        'dkey1': [ins2.channel(12).volt,ins2.channel(10).volt,ins2.channel(8).volt,ins2.channel(6).volt,ins2.channel(4).volt,ins2.channel(2).volt,ins1.channel(24).volt,ins1.channel(22).volt,ins1.channel(20).volt]}
    
    binary_format = '0{}b'.format(lvls)
    gate_key = format(out,binary_format)
    gate_key = gate_key[::-1]
    
    for n in range(len(gate_key)):
        if gate_key[n] == '0':
            if not (open_volt-0.1*open_volt < keys['skey0'][n]() < open_volt+0.1*open_volt):
                device_move(keys['skey0'][n], open_volt,stepnum)
            if not (close_volt-0.1*close_volt > keys['skey1'][n]() > close_volt+0.1*close_volt):
                device_move(keys['skey1'][n], close_volt,stepnum)
            
            if not (open_volt-0.1*open_volt < keys['dkey0'][n]() < open_volt+0.1*open_volt):
                device_move(keys['dkey0'][n], open_volt,stepnum)
            if not (close_volt-0.1*close_volt > keys['dkey1'][n]() > close_volt+0.1*close_volt):
                device_move(keys['dkey1'][n], close_volt,stepnum)
        
        if gate_key[n] == '1':
            if not (close_volt-0.1*close_volt > keys['skey0'][n]() > close_volt+0.1*close_volt):
                device_move(keys['skey0'][n], close_volt,stepnum)
            if not (open_volt-0.1*open_volt < keys['skey1'][n]() < open_volt+0.1*open_volt):
                device_move(keys['skey1'][n], open_volt,stepnum)
            
            if not (close_volt-0.1*close_volt > keys['dkey0'][n]() > close_volt+0.1*close_volt):
                device_move(keys['dkey0'][n], close_volt,stepnum)
            if not (open_volt-0.1*open_volt < keys['dkey1'][n]() < open_volt+0.1*open_volt):
                device_move(keys['dkey1'][n], open_volt,stepnum)

def mpx_out_src(lvls, out, instruments,keys=0,open_volt=1,close_volt=-2,stepnum=101):
    #convert to binary
    # 0 means gate 1 positive gate 2 negative
    # 1 menas gate 1 negative gate 2 positive
    
    # QDAC channel key #
    if keys==0:
        ins1=instruments[0]
        ins2=instruments[1]
        keys={'skey0': [ins1.channel(17).volt,ins1.channel(15).volt,ins1.channel(13).volt,ins1.channel(11).volt,ins1.channel(9).volt,ins1.channel(7).volt,ins1.channel(5).volt,ins1.channel(3).volt,ins1.channel(1).volt],
        'skey1': [ins1.channel(18).volt,ins1.channel(16).volt,ins1.channel(14).volt,ins1.channel(12).volt,ins1.channel(10).volt,ins1.channel(8).volt,ins1.channel(6).volt,ins1.channel(4).volt,ins1.channel(2).volt]}
    
    binary_format = '0{}b'.format(lvls)
    gate_key = format(out,binary_format)
    gate_key = gate_key[::-1]
    
    for n in range(len(gate_key)):
        if gate_key[n] == '0':
            if not (open_volt-0.1*open_volt < keys['skey0'][n]() < open_volt+0.1*open_volt):
                device_move(keys['skey0'][n], open_volt,stepnum)
            if not (close_volt-0.1*close_volt > keys['skey1'][n]() > close_volt+0.1*close_volt):
                device_move(keys['skey1'][n], close_volt,stepnum)
        
        if gate_key[n] == '1':
            if not (close_volt-0.1*close_volt > keys['skey0'][n]() > close_volt+0.1*close_volt):
                device_move(keys['skey0'][n], close_volt,stepnum)
            if not (open_volt-0.1*open_volt < keys['skey1'][n]() < open_volt+0.1*open_volt):
                device_move(keys['skey1'][n], open_volt,stepnum)

def mpx_out_drn(lvls, out, instruments,keys=0,open_volt=1,close_volt=-2,stepnum=101):
    #convert to binary
    # 0 means gate 1 positive gate 2 negative
    # 1 menas gate 1 negative gate 2 positive
    
    # QDAC channel key #
    if keys==0:
        ins1=instruments[0]
        ins2=instruments[1]
        keys={'dkey0': [ins2.channel(11).volt,ins2.channel(9).volt,ins2.channel(7).volt,ins2.channel(5).volt,ins2.channel(3).volt,ins2.channel(1).volt,ins1.channel(23).volt,ins1.channel(21).volt,ins1.channel(19).volt],
        'dkey1': [ins2.channel(12).volt,ins2.channel(10).volt,ins2.channel(8).volt,ins2.channel(6).volt,ins2.channel(4).volt,ins2.channel(2).volt,ins1.channel(24).volt,ins1.channel(22).volt,ins1.channel(20).volt]}
    
    binary_format = '0{}b'.format(lvls)
    gate_key = format(out,binary_format)
    gate_key = gate_key[::-1]
    
    for n in range(len(gate_key)):
        if gate_key[n] == '0':
            if not (open_volt-0.1*open_volt < keys['dkey0'][n]() < open_volt+0.1*open_volt):
                device_move(keys['dkey0'][n], open_volt,stepnum)
            if not (close_volt-0.1*close_volt > keys['dkey1'][n]() > close_volt+0.1*close_volt):
                device_move(keys['dkey1'][n], close_volt,stepnum)
        
        if gate_key[n] == '1':
            if not (close_volt-0.1*close_volt > keys['dkey0'][n]() > close_volt+0.1*close_volt):
                device_move(keys['dkey0'][n], close_volt,stepnum)
            if not (open_volt-0.1*open_volt < keys['dkey1'][n]() < open_volt+0.1*open_volt):
                device_move(keys['dkey1'][n], open_volt,stepnum)
  
def mpx_out_test(lvls, out, instruments,keys=0,open_volt=1,close_volt=-2,stepnum=101):
    #convert to binary
    # 0 means gate 1 positive gate 2 negative
    # 1 menas gate 1 negative gate 2 positive
    
    # QDAC channel key #
    if keys==0:
        ins1=instruments[0]
        ins2=instruments[1]
        keys={'skey0': [ins1.channel(17).volt,ins1.channel(15).volt,ins1.channel(13).volt,ins1.channel(11).volt,ins1.channel(9).volt,ins1.channel(7).volt,ins1.channel(5).volt,ins1.channel(3).volt,ins1.channel(1).volt],
        'skey1': [ins1.channel(18).volt,ins1.channel(16).volt,ins1.channel(14).volt,ins1.channel(12).volt,ins1.channel(10).volt,ins1.channel(8).volt,ins1.channel(6).volt,ins1.channel(4).volt,ins1.channel(2).volt],
        'dkey0': [ins2.channel(11).volt,ins2.channel(9).volt,ins2.channel(7).volt,ins2.channel(5).volt,ins2.channel(3).volt,ins2.channel(1).volt,ins1.channel(23).volt,ins1.channel(21).volt,ins1.channel(19).volt],
        'dkey1': [ins2.channel(12).volt,ins2.channel(10).volt,ins2.channel(8).volt,ins2.channel(6).volt,ins2.channel(4).volt,ins2.channel(2).volt,ins1.channel(24).volt,ins1.channel(22).volt,ins1.channel(20).volt]}
    
    binary_format = '0{}b'.format(lvls)
    gate_key = format(out,binary_format)
    gate_key = gate_key[::-1]
    print(gate_key)
    
    for n in range(len(gate_key)):
        if gate_key[n] == '0':
            print(str(keys['skey0'][n]) + '='+str(open_volt))
            print(str(keys['skey1'][n]) + '='+str(close_volt))
            
            print(str(keys['dkey0'][n]) + '='+str(open_volt))
            print(str(keys['dkey1'][n]) + '='+str(close_volt))
            print(" ")
        
        if gate_key[n] == '1':
            print(str(keys['skey0'][n]) + '='+str(close_volt))
            print(str(keys['skey1'][n]) + '='+str(open_volt))
            
            print(str(keys['dkey0'][n]) + '='+str(close_volt))
            print(str(keys['dkey1'][n]) + '='+str(open_volt))
            print(" ")


def mpx_element(mpx_size, lvl, element, instruments,keys=0,open_volt=1,close_volt=-2,stepnum=101):

    # QDAC channel key #
    # if you're not using two qdacs with the keys as listed below, you'll have to provide your own keys (skey0,skey1,dkey0,dkey1) in a dictionary as below.
    # Each element of the key must be the full parameter.
    if keys==0:
        ins1=instruments[0]
        ins2=instruments[1]
        keys={'skey0': [ins1.channel(17).volt,ins1.channel(15).volt,ins1.channel(13).volt,ins1.channel(11).volt,ins1.channel(9).volt,ins1.channel(7).volt,ins1.channel(5).volt,ins1.channel(3).volt,ins1.channel(1).volt],
        'skey1': [ins1.channel(18).volt,ins1.channel(16).volt,ins1.channel(14).volt,ins1.channel(12).volt,ins1.channel(10).volt,ins1.channel(8).volt,ins1.channel(6).volt,ins1.channel(4).volt,ins1.channel(2).volt],
        'dkey0': [ins2.channel(11).volt,ins2.channel(9).volt,ins2.channel(7).volt,ins2.channel(5).volt,ins2.channel(3).volt,ins2.channel(1).volt,ins1.channel(23).volt,ins1.channel(21).volt,ins1.channel(19).volt],
        'dkey1': [ins2.channel(12).volt,ins2.channel(10).volt,ins2.channel(8).volt,ins2.channel(6).volt,ins2.channel(4).volt,ins2.channel(2).volt,ins1.channel(24).volt,ins1.channel(22).volt,ins1.channel(20).volt]}

        skey0 = keys['skey0']
        skey1 = keys['skey1']

        dkey0 = keys['dkey0']
        dkey1 = keys['dkey1']
    
    key0 = dkey0[::-1] + skey0
    key1 = dkey1[::-1] + skey1
    
    off = 7-mpx_size
    key0 = key0[off:]
    key1 = key1[off:]
    
     # level key #
#     lvlkey = np.array([-7,-6,-5,-4,-3,-2,-1,1,2,3,4,5,6,7])
    lvlkey1 = np.linspace(1,mpx_size,mpx_size)
    lvlkey2 = lvlkey1[::-1]
    lvlkey = np.concatenate((lvlkey1*-1,lvlkey2))
    
    wh = np.where(lvlkey == lvl)
    wh = wh[0][0]
    
    if lvl > 0:
        binary_format = '0{}b'.format(np.abs(lvl))
        gate_key = format(element,binary_format)
        gate_key = gate_key[::-1]
        for n in range(len(gate_key)):
            if gate_key[n] == '0':
                if not (open_volt-0.1*open_volt < key0[wh+n]() < open_volt+0.1*open_volt):
                    device_move(skey0[n], open_volt,stepnum)
                if not (close_volt-0.1*close_volt > key1[wh+n]() > close_volt+0.1*close_volt):
                    device_move(skey1[n], close_volt,stepnum)


            if gate_key[n] == '1':
                if not (close_volt-0.1*close_volt > key0[wh+n]() > close_volt+0.1*close_volt):
                    device_move(skey0[n], close_volt,stepnum)
                if not (open_volt-0.1*open_volt < key1[wh+n]() < open_volt+0.1*open_volt):
                    device_move(skey1[n], open_volt,stepnum)
            
    
    # open everything below the element #
    for n in range(wh):
        if not (open_volt-0.1*open_volt < key0[n]() < open_volt+0.1*open_volt):
            device_move(key0[n], open_volt,stepnum)
        if not (open_volt-0.1*open_volt < key1[n]() < open_volt+0.1*open_volt):
            device_move(key1[n], open_volt,stepnum)
            
#     device_move(qdac["ch24_v"],-0.8,50)
           
    if element%2 == 0:
        gate_to_sweep = key0[wh]
    else:
        gate_to_sweep = key1[wh]
        
    return gate_to_sweep
    
    
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
