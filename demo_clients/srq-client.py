import sys
import os
import time

sys.path.append(os.path.abspath('..'))
import vxi11_server as vxi11

# with a default instrument, inst0 is implied.
default_instr = vxi11.Instrument("TCPIP::127.0.0.1::INSTR")
test1_instr = vxi11.Instrument("TCPIP::127.0.0.1::inst1::INSTR")
test2_instr = vxi11.Instrument("TCPIP::127.0.0.1::inst2::INSTR")

def asknprint( instr, q):
    print("send: %s"%q)
    print("answer: %s"% instr.ask(q))
    

asknprint( default_instr, "*IDN?")
asknprint( test1_instr, "*IDN?")
asknprint( test2_instr, "*IDN?")

def srq_intr_handler1():
    print("got SRQ for instrument 1")
    
def srq_intr_handler2():
    print("got SRQ for instrument 2")

print("registering srq handler")
test1_instr.on_srq(srq_intr_handler1)
test2_instr.on_srq(srq_intr_handler2)

print("asking instrument for SRQs")

asknprint(test1_instr, "SRQTIMER")
time.sleep(4)
asknprint(test2_instr, "SRQTIMER")

print('talking while waiting for srq')

for i in range(5):

    print (i)
    
    time.sleep(4)

    asknprint( test1_instr, "*IDN?")
    asknprint( test2_instr, "*IDN?")

print ("unregistering srq handler")
test1_instr.on_srq(None)
test2_instr.on_srq(None)
