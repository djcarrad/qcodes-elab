import qcodes as qc
from qcodes import param_move as device_move
from qcodes.instrument_drivers.QDev.QDac import QDac
import numpy as np
import time

def mpx_out(lvls, out, qdac):
    #convert to binary
    # 0 means gate 1 positive gate 2 negative
    # 1 menas gate 1 negative gate 2 positive
    
    # QDAC channel key #
    skey0 = [15,13,11,9,7,5,3,1]
    skey1 = [16,14,12,10,8,6,4,2]

    #dkey0 = [31,29,27,25,23,21,19,17]
    #dkey1 = [32,30,28,26,24,22,20,18]
    
    # open and close voltages for branches #
    open_volt = 1
    close_volt = -2
    
    
    binary_format = '0{}b'.format(lvls)
    gate_key = format(out,binary_format)
    gate_key = gate_key[::-1]
    
    for n in range(len(gate_key)):
        if gate_key[n] == '0':
            if not (open_volt-0.1*open_volt < qdac["ch{:02d}_v".format(skey0[n])]() < open_volt+0.1*open_volt):
                device_move(qdac["ch{:02d}_v".format(skey0[n])], open_volt,100)
            if not (close_volt-0.1*close_volt > qdac["ch{:02d}_v".format(skey1[n])]() > close_volt+0.1*close_volt):
                device_move(qdac["ch{:02d}_v".format(skey1[n])], close_volt,100)
            
            if not (open_volt-0.1*open_volt < qdac["ch{:02d}_v".format(dkey0[n])]() < open_volt+0.1*open_volt):
                device_move(qdac["ch{:02d}_v".format(dkey0[n])], open_volt,100)
            if not (close_volt-0.1*close_volt > qdac["ch{:02d}_v".format(dkey1[n])]() > close_volt+0.1*close_volt):
                device_move(qdac["ch{:02d}_v".format(dkey1[n])], close_volt,100)
        
        if gate_key[n] == '1':
            if not (close_volt-0.1*close_volt > qdac["ch{:02d}_v".format(skey0[n])]() > close_volt+0.1*close_volt):
                device_move(qdac["ch{:02d}_v".format(skey0[n])], close_volt,100)
            if not (open_volt-0.1*open_volt < qdac["ch{:02d}_v".format(skey1[n])]() < open_volt+0.1*open_volt):
                device_move(qdac["ch{:02d}_v".format(skey1[n])], open_volt,100)
            
            if not (close_volt-0.1*close_volt > qdac["ch{:02d}_v".format(dkey0[n])]() > close_volt+0.1*close_volt):
                device_move(qdac["ch{:02d}_v".format(dkey0[n])], close_volt,100)
            if not (open_volt-0.1*open_volt < qdac["ch{:02d}_v".format(dkey1[n])]() < open_volt+0.1*open_volt):
                device_move(qdac["ch{:02d}_v".format(dkey1[n])], open_volt,100)
                

def mpx_element(mpx_size, lvl, element, qdac):
    # QDAC channel key #
    skey0 = [15,13,11,9,7,5,3,1]
    skey1 = [16,14,12,10,8,6,4,2]

    dkey0 = [31,29,27,25,23,21,19,17]
    dkey1 = [32,30,28,26,24,22,20,18]
    
    key0 = dkey0[::-1] + skey0
    key1 = dkey1[::-1] + skey1
    
    off = 7-mpx_size
    key0 = key0[off:]
    key1 = key1[off:]
    
    # open and close voltages for branches #
    open_volt = 0.5
    close_volt = -0.8
    
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
                if not (open_volt-0.1*open_volt < qdac["ch{:02d}_v".format(key0[wh+n])]() < open_volt+0.1*open_volt):
                    device_move(qdac["ch{:02d}_v".format(skey0[n])], open_volt,50)
                if not (close_volt-0.1*close_volt > qdac["ch{:02d}_v".format(key1[wh+n])]() > close_volt+0.1*close_volt):
                    device_move(qdac["ch{:02d}_v".format(skey1[n])], close_volt,50)


            if gate_key[n] == '1':
                if not (close_volt-0.1*close_volt > qdac["ch{:02d}_v".format(key0[wh+n])]() > close_volt+0.1*close_volt):
                    device_move(qdac["ch{:02d}_v".format(skey0[n])], close_volt,50)
                if not (open_volt-0.1*open_volt < qdac["ch{:02d}_v".format(key1[wh+n])]() < open_volt+0.1*open_volt):
                    device_move(qdac["ch{:02d}_v".format(skey1[n])], open_volt,50)
            
    
    # open everything below the element #
    for n in range(wh):
        if not (open_volt-0.1*open_volt < qdac["ch{:02d}_v".format(key0[n])]() < open_volt+0.1*open_volt):
            device_move(qdac["ch{:02d}_v".format(key0[n])], open_volt,50)
        if not (open_volt-0.1*open_volt < qdac["ch{:02d}_v".format(key1[n])]() < open_volt+0.1*open_volt):
            device_move(qdac["ch{:02d}_v".format(key1[n])], open_volt,50)
            
#     device_move(qdac["ch24_v"],-0.8,50)
           
    if element%2 == 0:
        gate_to_sweep = key0[wh]
    else:
        gate_to_sweep = key1[wh]
        
    return gate_to_sweep 
    
    
def mpx_out_src(lvls, out, qdac):
    # QDAC channel key #
    skey0 = [15,13,11,9,7,5,3,1]
    skey1 = [16,14,12,10,8,6,4,2]
    
    # open and close voltages for branches #
    open_volt = 1
    close_volt = -2
    
    
    binary_format = '0{}b'.format(lvls)
    gate_key = format(out,binary_format)
    gate_key = gate_key[::-1]
    prep_time = time.time()
    
    for n in range(len(gate_key)):
        if gate_key[n] == '0':
            if not (open_volt-0.1*open_volt < qdac["ch{:02d}_v".format(skey0[n])]() < open_volt+0.1*open_volt):
                device_move(qdac["ch{:02d}_v".format(skey0[n])], open_volt,5)
            if not (close_volt-0.1*close_volt > qdac["ch{:02d}_v".format(skey1[n])]() > close_volt+0.1*close_volt):
                device_move(qdac["ch{:02d}_v".format(skey1[n])], close_volt,5)

        
        if gate_key[n] == '1':
            if not (close_volt-0.1*close_volt > qdac["ch{:02d}_v".format(skey0[n])]() > close_volt+0.1*close_volt):
                device_move(qdac["ch{:02d}_v".format(skey0[n])], close_volt,5)
            if not (open_volt-0.1*open_volt < qdac["ch{:02d}_v".format(skey1[n])]() < open_volt+0.1*open_volt):
                device_move(qdac["ch{:02d}_v".format(skey1[n])], open_volt,5)

                

def mpx_out_drn(lvls, out, qdac):
    
    # QDAC channel key #
    dkey0 = [31,29,27,25,23,21,19,17]
    dkey1 = [32,30,28,26,24,22,20,18]
    
    # open and close voltages for branches #
    open_volt = 1
    close_volt = -2
    
    
    binary_format = '0{}b'.format(lvls)
    gate_key = format(out,binary_format)
    gate_key = gate_key[::-1]
    
    for n in range(len(gate_key)):
        if gate_key[n] == '0':
            if not (open_volt-0.1*open_volt < qdac["ch{:02d}_v".format(dkey0[n])]() < open_volt+0.1*open_volt):
                device_move(qdac["ch{:02d}_v".format(dkey0[n])], open_volt,5)
            if not (close_volt-0.1*close_volt > qdac["ch{:02d}_v".format(dkey1[n])]() > close_volt+0.1*close_volt):
                device_move(qdac["ch{:02d}_v".format(dkey1[n])], close_volt,5)
        
        if gate_key[n] == '1':
            if not (close_volt-0.1*close_volt > qdac["ch{:02d}_v".format(dkey0[n])]() > close_volt+0.1*close_volt):
                device_move(qdac["ch{:02d}_v".format(dkey0[n])], close_volt,5)
            if not (open_volt-0.1*open_volt < qdac["ch{:02d}_v".format(dkey1[n])]() < open_volt+0.1*open_volt):
                device_move(qdac["ch{:02d}_v".format(dkey1[n])], open_volt,5)
                
            

def mpx_out_test(lvls, out, qdac):
    #convert to binary
    # 0 means gate 1 positive gate 2 negative
    # 1 menas gate 1 negative gate 2 positive
    
    # QDAC channel key #
    skey0 = [15,13,11,9,7,5,3,1]
    skey1 = [16,14,12,10,8,6,4,2]

    dkey0 = [31,29,27,25,23,21,19,17]
    dkey1 = [32,30,28,26,24,22,20,18]
    
    open_volt = 0.5
    close_volt = -0.5
    
    
    binary_format = '0{}b'.format(lvls)
    gate_key = format(out,binary_format)
    gate_key = gate_key[::-1]
    print(gate_key)
    
    for n in range(len(gate_key)):
        if gate_key[n] == '0':
            print("ch{:02d}_v ".format(skey0[n]) + str(open_volt))
            print("ch{:02d}_v ".format(skey1[n]) + str(close_volt))
            
            print("ch{:02d}_v ".format(dkey0[n]) + str(open_volt))
            print("ch{:02d}_v ".format(dkey1[n]) + str(close_volt))
            print(" ")
        
        if gate_key[n] == '1':
            print("ch{:02d}_v ".format(skey0[n]) + str(close_volt))
            print("ch{:02d}_v ".format(skey1[n]) + str(open_volt))
            
            print("ch{:02d}_v ".format(dkey0[n]) + str(close_volt))
            print("ch{:02d}_v ".format(dkey1[n]) + str(open_volt))
            print(" ")
            
def qdac_all_off(qdac):
    for n in range(1,49):
        if -0.01 < qdac["ch{:02d}_v".format(n)]() <0.01:
            qdac["ch{:02d}_v".format(n)](0)
        else:
            device_move(qdac["ch{:02d}_v".format(n)], 0, 100)
            
def qdac_all_set(value,qdac):
    for n in range(1,17):
        if value-0.01 < qdac["ch{:02d}_v".format(n)]() <value+0.01:
            0
        else:
            device_move(qdac["ch{:02d}_v".format(n)], value, 100)
            
def qdac_all_status(qdac):
    for n in range(1,49):
        val = qdac["ch{:02d}_v".format(n)]()
        print("ch{:02d}: {} V".format(n,val))


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
