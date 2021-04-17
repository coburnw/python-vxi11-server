import sys
import os
import signal
import logging
from  threading import Timer
import time

sys.path.append(os.path.abspath('..'))
import vxi11_server as vxi11

_logging = logging.getLogger(__name__)


def signal_handler(signal, frame):
    _logging.info('Handling Ctrl+C!')
    instr_server.close()
    sys.exit(0)
                                        
class SRQTestDevice(vxi11.InstrumentDevice):

    def device_init(self):
        self.response = ""
        return
    
    def device_write(self, opaque_data, flags, io_timeout):
        "The device_write RPC is used to write data to the specified device"
        error = vxi11.Error.NO_ERROR

        commands= opaque_data.decode("ascii").split(";")
        for cmd in commands:
            error= self._processCommand(cmd.strip())
            if error != vxi11.Error.NO_ERROR:
                break
        return error

    def device_read(self, request_size, term_char, flags, io_timeout): 
        "The device_read RPC is used to read data from the device to the controller"
        error = vxi11.Error.NO_ERROR
        aStr=self.response
        self.response=""
        reason = vxi11.ReadRespReason.END
        # returns opaque_data!
        return error, reason, aStr.encode("ascii","ignore")
    
    def _addResponse(self,aStr):
        self.response+=aStr

    def _processCommand(self, cmd ):
        error = vxi11.Error.NO_ERROR

        # commands ordered by usage rate
        if cmd.startswith("*IDN?"):
            self._addResponse("ulda,srq-test,1,V1.0")
        elif cmd.startswith("SRQTIMER"):
            t= Timer(10, self.signal_srq )
            t.start()
            self._addResponse("OK")
        else:
            _logging.debug("unsupported vxi11-cmd %s",cmd)
            error = vxi11.Error.OPERATION_NOT_SUPPORTED
        return error

    def signal_srq(self):
        _logging.info("SRQ startet for instrument %s",self.name())
        super().signal_srq()
        

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    _logging = logging.getLogger(__name__)

    signal.signal(signal.SIGINT, signal_handler)
    print('Press Ctrl+C to exit')

    _logging.info('starting SRQ test device')

    instr_server = vxi11.InstrumentServer()
    instr_server.add_device_handler(SRQTestDevice, "inst1")
    instr_server.add_device_handler(SRQTestDevice, "inst2")

    instr_server.listen()

    # sleep (or do foreground work) while the Instrument threads do their job
    while True:
        time.sleep(1)
    
