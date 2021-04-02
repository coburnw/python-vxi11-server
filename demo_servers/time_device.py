import sys
import signal
import time
import logging

#import .vxi11_server as Vxi11
import vxi11_server as Vxi11

#
# A simple instrument server.
#
# creates an InstrumentServer with the name INSTR
# adds a device handler with the name inst1
# this instrument simply responds with the current time when queried by
# a vxi11 client.
#
# 'TIME' may not be a legal vxi11 instrument name, but seems to work well.
# allowing some introspection on a device you havent used (and didnt document)
# in some time.
#

def signal_handler(signal, frame):
    logger.info('Handling Ctrl+C!')
    instr_server.close()
    sys.exit(0)
                                        
class TimeDevice(Vxi11.InstrumentDevice):
    def __init__(self, device_name):
        super().__init__(device_name)
        
    def device_read(self):
        '''respond to the device_read rpc: refer to section (B.6.4) 
        of the VXI-11 TCP/IP Instrument Protocol Specification''' 
        error = Vxi11.Error.NO_ERROR
        result = time.strftime("%H:%M:%S +0000", time.gmtime())
        return error, result.encode("ascii") # opaque_data is a bystes array, so encode correctly!

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    logger = logging.getLogger(__name__)

    signal.signal(signal.SIGINT, signal_handler)
    print('Press Ctrl+C to exit')
    logger.info('starting time_device')
    
    # create a server, attach a device, and start a thread to listen for requests
    instr_server = Vxi11.InstrumentServer()
    #name = 'TIME'
    name = 'inst1'
    instr_server.add_device_handler(TimeDevice, name)
    instr_server.listen()

    # sleep (or do foreground work) while the Instrument threads do their job
    while True:
        time.sleep(1)

        
