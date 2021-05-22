# adapted from work by @raphaelvalentin

import sys
import os
import logging
import signal
import time

#sys.path.append(os.path.abspath('./python-vxi11-server'))
sys.path.append(os.path.abspath('..'))
import vxi11_server as Vxi11
from vxi11_server import vxi11


def signal_handler(signal, frame):
    logger.info('Handling Ctrl+C!')
    instr_server.close()
    sys.exit(0)


class InstrumentRemote(Vxi11.InstrumentDevice):
    def device_write(self, opaque_data, flags, io_timeout):
        error = vxi11.ERR_NO_ERROR

        cmd=opaque_data.decode("ascii")
        self.result = None

        if cmd.strip() == '*IDN?':
            self.result = "{}".format(self.idn)
        else:
            self.result = 'invalid'

        logger.info("%s: device_write(): %s", self.name(), cmd)
        return error

    def device_read(self, request_size, term_char, flags, io_timeout):
        error = Vxi11.Error.NO_ERROR
        reason = Vxi11.ReadRespReason.END

        logger.info("%s: device_write(): %s", self.name(), self.result.strip())

        opaque_data = self.result.encode("ascii")
        return error, reason, opaque_data

class InstrumentRemote_0(InstrumentRemote):
    def device_init(self):
        "Set the devices idn string etc here.  Called immediately after instance creation."
        self.idn = 'my instrument zero'
        self.result = 'empty'
        return

class InstrumentRemote_1(InstrumentRemote):
    def device_init(self):
        "Set the devices idn string etc here.  Called immediately after instance creation."
        self.idn = 'my instrument one'
        self.result = 'empty'
        return

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    logger = logging.getLogger(__name__)

    signal.signal(signal.SIGINT, signal_handler)
    print('Press Ctrl+C to exit')
    logger.info('starting time_device')

    # create a server, attach a device, and start a thread to listen for requests
    instr_server = Vxi11.InstrumentServer(InstrumentRemote_0)
    instr_server.add_device_handler(InstrumentRemote_1, 'inst1')
    instr_server.listen()
    
    # sleep (or do foreground work) while the Instrument threads do their job
    while True:
        time.sleep(1)
