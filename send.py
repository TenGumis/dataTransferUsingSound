#!/usr/bin/env python
#Mateusz Pabian Jagiellonian University
#Python 2.7.12

import sys
import wave
from bitarray import bitarray
import binascii
import pulseaudio as pa
import numpy as np

sample_map = {
    1 : pa.SAMPLE_U8,
    2 : pa.SAMPLE_S16LE,
    4 : pa.SAMPLE_S32LE,
}

t=300
f0=3000
f1=6000
nchannels = 1
sampwidth = 2
framerate = 44100
nframes = int(44100 /t)
message=''
frm=1
to=2
msg='tmp'

if len(sys.argv)>=3:
    t=int(sys.argv[1])
    f0=int(sys.argv[2])
    f1=int(sys.argv[3])

bb={}
bb['']=''
bb["0000"]="11110"
bb["0001"]="01001"
bb["0010"]="10100"
bb["0011"]="10101"
bb["0100"]="01010"
bb["0101"]="01011"
bb["0110"]="01110"
bb["0111"]="01111"
bb["1000"]="10010"
bb["1001"]="10011"
bb["1010"]="10110"
bb["1011"]="10111"
bb["1100"]="11010"
bb["1101"]="11011"
bb["1110"]="11100"
bb["1111"]="11101"
bb["11110"]="0000"
bb["01001"]="0001"
bb["10100"]="0010"
bb["10101"]="0011"
bb["01010"]="0100"
bb["01011"]="0101"
bb["01110"]="0110"
bb["01111"]="0111"
bb["10010"]="1000"
bb["10011"]="1001"
bb["10110"]="1010"
bb["10111"]="1011"
bb["11010"]="1100"
bb["11011"]="1101"
bb["11100"]="1110"
bb["11101"]="1111"

def BB(X):   #4B5B encoding
    res=''
    for x in [X[i:i+4] for i in range(0,len(X),4)]:
        res+=bb[x]
        
    return res

def nrz(X):  #nrz encoding
    res=''
    state=1
    for i in X:
        if(i == '1'):
            state=1-state
            res+=str(state)
        else:
            res+=str(state)
    return res
    

def dectobin(X): 
    if X == 0: 
        return "0"
    s = ''
    while X:
        if (X & 1) == 1:
            s = "1" + s
        else:
            s = "0" + s
        X /= 2
    return s

def bintodec(X):
    k=2 ** (len(X)-1);
    res=0;
    for x in X:
	    if(x=='1'):
	        res+=k
	    k/=2
    
    return res;
    
def convert(A,B,M): #convert ascii to bits
    TMP=''
    for c in M:
        X=str(dectobin(ord(c)))
        while(len(X)<8):
            X='0'+X
        TMP=TMP+X
    M=TMP
    A=dectobin(int(A))
    B=dectobin(int(B))    
    while(len(A)<48):
        A='0'+A
        
    while(len(B)<48):
        B='0'+B
        
    while(len(M)%8!=0):
        M='0'+M
    
    L=len(M)/8
    L=dectobin(int(L))
    while(len(L)<16):
        L='0'+L

    S=binascii.crc32(bitarray(B+A+L+M))&0xffffffff
    S=dectobin(int(S))
    while(len(S)<32):
        S='0'+S
    
    TMP=nrz(BB(B+A+L+M+S))
    TMP='10101010'*7+'10101011'+TMP
    return TMP

def frame(k): #encode bit to sound
    if k =='0':
        frequency=f0
    else:
        frequency=f1
    L=[]
    for it in range( int(float(framerate/t)) ):
        L.append(22500*np.sin(2*np.pi*frequency*it/framerate)) 
    return L

msg=''
print("<from> <to> <message>")
with pa.simple.open(direction=pa.STREAM_PLAYBACK, format=sample_map[sampwidth], rate=framerate, channels=nchannels) as player:
    while 1:
        line = raw_input()
        if not line:
            break
        line=line.split(' ')
        if len(line)<3: 
            continue
        frm=line[0]
        to=line[1]
        msg=' '.join(line[2:])
        message=convert(frm,to,msg)
        for i in message:
            player.write(frame(i))
        player.drain()
