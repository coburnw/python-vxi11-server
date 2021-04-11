import sys
import os
import signal
import logging
import struct
import time

sys.path.append(os.path.abspath('..'))
import vxi11_server as vxi11

_logging = logging.getLogger(__name__)


def signal_handler(signal, frame):
    logger.info('Handling Ctrl+C!')
    instr_server.close()
    sys.exit(0)
                                        

class GPIBLikeDefaultDevice(vxi11.instrument_device.DefaultInstrumentDevice):
    def __init__(self, device_name):
        super().__init__(device_name)
        self.idn = 'ulda', 'gpib-bridge', '1', 'V1.0'
        self.result = 'empty'
        self.atn_enabled=False
        self.ren_enabled=False
        self.srq_active=False
        self.busaddr=0 # something

    def device_clear(self, flags, lock_timeout, io_timeout): # 15, generic params
        "The device_clear RPC is used to send a device clear to a device"
        _logging.debug("Device %s cleared",self.device_name)
        error = vxi11.Error.NO_ERROR
        return error

    def device_write(self, opaque_data):
        _logging.debug("Default device recieved: %r",opaque_data)
        return super().device_write(opaque_data)

    def device_docmd(self,flags, io_timeout, lock_timeout, cmd, network_order, data_size, opaque_data_in):
        # emulate some bus function commands
        error = vxi11.Error.NO_ERROR
        _logging.debug("Device %s docmd: %x",self.device_name,cmd)

        opaque_data_out=b""
        
        if cmd == 0x020000:
            # send command
            # do nothing but echo
            opaque_data_out=opaque_data_in
        elif cmd == 0x020001:
            # bus status
            subcmd=struct.unpack("!H",opaque_data_in)[0]
            _logging.debug("Device %s docmd_busstatus: %x", self.device_name, subcmd)
            if subcmd == 1:
                # get REN
                opaque_data_out=struct.pack("!H", 1 if self.ren_enabled else 0)
            elif subcmd == 2:
                # get SRQ
                opaque_data_out=struct.pack("!H", 1 if self.srq_active else 0)
            elif subcmd == 3:
                # get NDAC
                opaque_data_out=struct.pack("!H", 0 )
            elif subcmd == 4:
                # is system controller?
                opaque_data_out=struct.pack("!H", 1 )
            elif subcmd == 5:
                # is controller in charge?
                opaque_data_out=struct.pack("!H", 1 )
            elif subcmd == 6:
                # is talker?
                opaque_data_out=struct.pack("!H", 0 )
            elif subcmd == 7:
                # is listener?
                opaque_data_out=struct.pack("!H", 0 )
            elif subcmd == 8:
                # get bus address
                opaque_data_out=struct.pack("!H", self.busaddr )
        elif cmd == 0x020002:
            # ATN control
            val= struct.unpack("!H",opaque_data_in)[0]
            if val == 0:
                self.atn_enabled=False
            else:
                self.atn_enabled=True
            _logging.info("ATN set to %s", self.atn_enabled)
            opaque_data_out=opaque_data_in
        elif cmd == 0x020003:
            # REN control
            val= struct.unpack("!H",opaque_data_in)[0]
            if val == 0:
                self.ren_enabled=False
            else:
                self.ren_enabled=True
            _logging.info("REN set to %s", self.ren_enabled)
            opaque_data_out=opaque_data_in
        elif cmd == 0x020004:
            # pass control
            error=vxi11.Error.INVALID_ADDRESS
            opaque_data_out=opaque_data_in
        elif cmd == 0x02000a:
            # set bus address
            val= struct.unpack("!L",opaque_data_in)[0]
            if val>=0 and val <=30:
                self.busaddr=val
                _logging.info("Bus adress set to %i",val)
            else:
                error=vxi11.Error.PARAMETER_ERROR
            opaque_data_out=opaque_data_in
        elif cmd == 0x020010:
            # IFC control
            # res to be empty
            pass
        else:
            error = vxi11.Error.OPERATION_NOT_SUPPORTED

        return error, opaque_data_out

class GPIBLikeDevice(vxi11.InstrumentDevice):

    def __init__(self, device_name):
        super().__init__(device_name)

        self.response = ""

    def device_write(self, opaque_data):
        "The device_write RPC is used to write data to the specified device"
        error = vxi11.Error.NO_ERROR

        commands= opaque_data.decode("ascii").split(";")
        for cmd in commands:
            error= self._processCommand(cmd.strip())
            if error != vxi11.Error.NO_ERROR:
                break
            self.addResponse(";")#  add a separator to the end of response

        self.response=self.response.rstrip(";") # remove last separator
        return error

    def device_read(self): 
        "The device_read RPC is used to read data from the device to the controller"
        error = vxi11.Error.NO_ERROR
        aStr=self.response
        self.response=""
        # returns opaque_data!
        return error, aStr.encode("ascii","ignore")

    def device_clear(self, flags, lock_timeout, io_timeout): # 15, generic params
        "The device_clear RPC is used to send a device clear to a device"
        _logging.debug("Device %s cleared",self.device_name)
        error = vxi11.Error.NO_ERROR
        return error
    
    def _addResponse(self,aStr):
        self.response+=aStr

    def _processCommand(self, cmd ):
        error = vxi11.Error.NO_ERROR

        # commands ordered by usage rate
        if cmd.startswith("*IDN?"):
            self._addResponse("ulda,gpib-client,1,V1.0")
        else:
            _logging.debug("unsupported vxi11-cmd %s",cmd)
            error = vxi11.Error.OPERATION_NOT_SUPPORTED
        return error

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    _logging = logging.getLogger(__name__)

    signal.signal(signal.SIGINT, signal_handler)
    print('Press Ctrl+C to exit')

    _logging.info('starting gpib bridge device')

    # create instrument serve
    instr_server = vxi11.InstrumentServer(default_device_handler=GPIBLikeDefaultDevice,
                                          default_device_name="gpib0")
    # now register a server for this socket
    instr_server.add_device_handler(GPIBLikeDevice, "gpib0,1")

    instr_server.listen()

    # sleep (or do foreground work) while the Instrument threads do their job
    while True:
        time.sleep(1)
    
