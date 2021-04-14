# srq test for keithley/tectronics 2604B

import sys
import os
import time
import logging

sys.path.append(os.path.abspath('..'))
import vxi11_server as vxi11

logging.basicConfig(level=logging.DEBUG)
_logging = logging.getLogger(__name__)

srq= False

def srq_intr_handler1():
    print("got SRQ for instrument")
    global srq
    srq=True

def asknprint( instr, q):
    print("send: %s"%q)
    print("answer: %s"% instr.ask(q))
    
instr = vxi11.Instrument("TCPIP::192.168.178.42::INSTR")
instr.write( "*cls")

asknprint( instr, "*IDN?")
asknprint( instr, "*stb?")
asknprint( instr, "*sre?")

print("init my srq handler")
instr.on_srq(srq_intr_handler1)

print("activate SRQ for errors")
instr.write("newbit = status.ERROR_AVAILABLE+ status.MESSAGE_AVAILABLE ") 
instr.write("status.request_enable=newbit")

asknprint( instr, "*sre?")

time.sleep(5)

try:
    print("write blabla? to provoke error")
    instr.write( "blabla?")

    while not srq:
        time.sleep(1)

    print("STB: hex %x"%instr.read_stb())
    #asknprint( instr, "*stb?")
       
except KeyboardInterrupt:
    pass
finally:
    instr.on_srq(None)
    instr.write( "*cls")

    print("srq was %s"%srq)

    instr.close()

