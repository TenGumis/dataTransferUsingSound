#!/usr/bin/env python
# vim:ts=4:sts=4:sw=4:expandtab

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

t=int(sys.argv[1])
f0=int(sys.argv[2])
f1=int(sys.argv[3])
nchannels = 1
sampwidth = 2
framerate = 44100
nframes = int(44100 /t)
sampformat=pa.SAMPLE_S16LE
message=''
msg=''


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

def BB(X):
    res=''
    for x in [X[i:i+4] for i in range(0,len(X),4)]:
        res+=bb[x]
        
    return res

def nrz2(X):
    res=''
    state=1
    for i in X:
        if(i == '1'):
            state=1-state
            res+=str(state)
        else:
            res+=str(state)
    return res
def BB2(X):
    res=''
    for x in [ X[i:i+5] for i in range(0,len(X),5) ]:
        res+=bb[x]

    return res
        
def nrz1(X):
    res=''
    state=1
    for i in X:
        if(str(state) == i):
            res+='0'
        else:
            res+='1'
            state=1-state
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

def getMsgLen(K):
    K=nrz1(K)
    while (len(K)%5 != 0):
        K=K[:-1]          
    K=BB2(K)
    B=K[:8*6]
    A=K[8*6:8*6*2]
    L=K[8*6*2:8*6*2+8*2]
    L=bintodec(L)
    return (int(L)+14+4)*10

def decode(K):
    if (len(K)>=18*8):
        #P=K[:8*8]
        #if(P != ('10'*31 + '11') ):
        #    return None
        #K=K[8*8:]
        K=nrz1(K)
        while (len(K)%5 != 0):
            K=K[:-1]            
            #return None
        K=BB2(K)
	    B=K[:8*6]
	    A=K[8*6:8*6*2]
	    L=K[8*6*2:8*6*2+8*2]
	    L=bintodec(L)
	    if(len(K)!=(18+L)*8):        
            pass
            #return None
	    M=K[8*6*2+8*2:8*6*2+8*2+8*L]
	    S=K[8*6*2+8*2+8*L:8*6*2+8*2+8*L+8*4]
	    if((binascii.crc32(bitarray(K[:8*6*2+8*2+8*L]))&0xffffffff)!=bintodec(S)):
		    return None
	    TMP=''
	    for i in range(L):
		    #print(chr(bintodec(M[i*8:(i+1)*8])))
		    TMP+=chr(bintodec(M[i*8:(i+1)*8]))
	    M=TMP
	    A=bintodec(A)
	    B=bintodec(B)
        return str(A)+" "+str(B)+" "+M
    return None
    

def frame(k):
    if k =='0':
        frequency=f0
    else:
        frequency=f1
    L=[]
    for it in range( int(float(frequency/t)) ):
        x=(2*np.pi)/(framerate/int(frequency));
        while(x<(2*np.pi)):
            x+=(2*np.pi)/(framerate/int(frequency))
            L.append( 25000*np.sin(x) )
    return L

def cos(x):
    res1=0
    res2=0
    maxx=x[0]
    for i in range(len(x)):
        if(maxx<x[i]):
            res2=res1
            res1=i
            maxx=x[i]
    return (res1,res2)

with pa.simple.open(direction=pa.STREAM_RECORD, format=sampformat, rate=framerate, channels=nchannels) as recorder:

    nframes = int(recorder.rate/t)
    endOfInput=False
    synchronized=False

    while endOfInput==False:       
        frameMax=0
        tmp=0
        tmp1=0
        preambula=True
        msgLen=-1
        message=''
        while synchronized:
            data = recorder.read(nframes)
            if(len(data) == 0):
                break;
            x= np.fft.fft(data)
            x=x[0:x.size/2]
            value=int(np.argmax(np.absolute(x))*t)
            if preambula:
                if(value == f1 and tmp1):
                    preambula=False
                    
                elif value == f1: 
                    tmp1=1
                else:
                    tmp1=0
            else:
                if(value == f1):
                    message+='1'
                elif (value == f0):
                    message+='0'
            #print(value)
            if len(message)==14*10:
                msgLen=getMsgLen(message)
            if len(message)==msgLen:
                print(decode(message))
                synchronized=False
                break
            
        else:
            for i in range(5):
                data = recorder.read(nframes)
                if(len(data) == 0):
                    endOfInput=True
                    break;
                x= np.fft.fft(data)
                x=x[0:x.size/2]
                x=np.absolute(x)
                if(len(x) == 0):
                    endOfInput=True
                    break;
                if x[np.argmax(np.absolute(x))]*t>frameMax:
                    tmp=i
                    frameMax=x[np.argmax(np.absolute(x))]*t
                value=int(np.argmax(np.absolute(x))*t)
                #print(value)
                if value < f0:
                    break;
                data = recorder.read(nframes/5)
            else:
                for i in range(tmp):
                    data = recorder.read(nframes/5)
                synchronized=True
