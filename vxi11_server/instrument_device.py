# MIT License

# Copyright (c) [2019] [Coburn Wightman]

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import logging
import ipaddress

from . import vxi11

logger = logging.getLogger(__name__)

class ReadRespReason():
    END = vxi11.RX_END
    CHR = vxi11.RX_CHR
    REQCNT = vxi11.RX_REQCNT
    
class InstrumentDevice(object):
    '''Base class for Instrument Devices.

    All devices should inherit from this class overriding the methods
    that make sense for the intended device. Since each method of this base class is
    expected to respond rationally, a very simple device might override one method only.

    See the "VXI-11 TCP/IP Instrument Protocol Specification" for details on
    each device_xxx procedure.  The procedures are from the host perspective, ie
    a device write is a write to the device and device read is a read from the device.
    '''

    def __init__(self, device_name, device_lock):
        self.device_name = device_name
        self.lock = device_lock

        self.intr_client = None
        self.srq_enabled = False
        self.srq_handle = None
        self.srq_active = False
        
        return

    def create_intr_chan(self,host_addr, host_port, prog_num, prog_vers, prog_family):
        if self.intr_client is not None:
            return vxi11.ERR_CHANNEL_ALREADY_ESTABLISHED

        if prog_num != vxi11.DEVICE_INTR_PROG or prog_vers!= vxi11.DEVICE_INTR_VERS or prog_family != vxi11.DEVICE_TCP:
            return  vxi11.ERR_OPERATION_NOT_SUPPORTED

        try:
            self.intr_client=vxi11.TCPIntrClient(str(ipaddress.IPv4Address(host_addr)), host_port)
            #self.intr_client.connect() # done in __init__
            return vxi11.ERR_NO_ERROR
        except Exception as e:
            logger.info("exception in create_intr_chan: %s",str(e))
            return vxi11.ERR_CHANNEL_NOT_ESTABLISHED

    def destroy_intr_chan(self):
        error = vxi11.ERR_CHANNEL_NOT_ESTABLISHED
        try:
            if self.intr_client is not None:
                self.intr_client.close()
                error=vxi11.ERR_NO_ERROR
        finally:
            self.intr_client=None
        return  error

    def device_readstb(self, flags, io_timeout): # 13, generic params
        "The device_readstb RPC is used to read a device's status byte."
        error = vxi11.ERR_NO_ERROR
        stb = 0

        #STB Status Byte Register
        # 0b_1000_0000 instrument specific
        # 0b_0100_0000 RQS - request service (send SRQ on rising edge)
        # 0b_0010_0000 ESB = (ESR >0)
        # 0b_0001_0000 Message avaliable
        # 0b_0000_1000 instrument specific 
        # 0b_0000_0100 Error avaliable
        # 0b_0000_0010 instrument specific
        # 0b_0000_0001 instrument specific
        
        # set bit 6 (of 0..7)  if srq is activated
        if self.srq_active:
            stb |= 0b_0100_0000
            # reset SRQ after read according to spec
            self.srq_active=False

        return error, stb

    def signal_srq(self):
        if self.srq_enabled and self.intr_client is not None:
            self.srq_active=True
            self.intr_client.signal_intr_srq(self.srq_handle)
        else:
            raise vxi11.Vxi11Exception(vxi11.ERR_CHANNEL_NOT_ESTABLISHED,
                                       "channel not enabled to signal SRQ")
    
    def name(self):
        return self.device_name

    # functions to overwrite when subclassing start here
    
    def device_init(self):
        "Set the devices idn string etc here.  Called immediately after instance creation."
        return
    
    def device_abort(self):
        "The device_abort RPC stops an in-progress call."
        error = vxi11.ERR_NO_ERROR
        return error
    
    def device_write(self, opaque_data, flags, io_timeout): # 11
        "The device_write RPC is used to write data to the specified device"
        error = vxi11.ERR_NO_ERROR

        if False:
            error = vxi11.ERR_IO_TIMEOUT
        elif False:
            error = vxi11.ERR_IO_ERROR
        elif False:
            error = vxi11.ERR_ABORT
        else:
            error = vxi11.ERR_OPERATION_NOT_SUPPORTED
            
        return error
    
    def device_read(self, request_size, term_char, flags, io_timeout): #= 12
        "The device_read RPC is used to read data from the device to the controller"
        error = vxi11.ERR_NO_ERROR
        opaque_data = b""
        
        if False:
            error = vxi11.ERR_IO_TIMEOUT
        elif False:
            error = vxi11.ERR_IO_ERROR
        elif False:
            error = vxi11.ERR_ABORT
        else:
            error = vxi11.ERR_OPERATION_NOT_SUPPORTED

        reason = ReadRespReason.END
        result = error, reason, opaque_data
        return result

    def device_trigger(self, flags, io_timeout): # 14, generic params
        "The device_trigger RPC is used to send a trigger to a device."
        error = vxi11.ERR_NO_ERROR
        
        if False:
            error = vxi11.ERR_IO_TIMEOUT
        elif False:
            error = vxi11.ERR_IO_ERROR
        elif False:
            error = vxi11.ERR_ABORT
        else:
            error = vxi11.ERR_OPERATION_NOT_SUPPORTED
            
        return error

    def device_clear(self, flags, io_timeout): # 15, generic params
        "The device_clear RPC is used to send a device clear to a device"
        error = vxi11.ERR_NO_ERROR
        
        if False:
            error = vxi11.ERR_IO_TIMEOUT
        elif False:
            error = vxi11.ERR_IO_ERROR
        elif False:
            error = vxi11.ERR_ABORT
        else:
            error = vxi11.ERR_OPERATION_NOT_SUPPORTED
            
        return error

    def device_remote(self, flags, io_timeout): # 16, generic params
        "The device_remote RPC is used to place a device in a remote state wherein all programmable local controls are disabled"
        error = vxi11.ERR_NO_ERROR
        
        if False:
            error = vxi11.ERR_IO_TIMEOUT
        elif False:
            error = vxi11.ERR_IO_ERROR
        elif False:
            error = vxi11.ERR_ABORT
        else:
            error = vxi11.ERR_OPERATION_NOT_SUPPORTED
            
        return error

    def device_local(self, flags, io_timeout): # 17, generic params
        "The device_local RPC is used to place a device in a local state wherein all programmable local controls are enabled"
        error = vxi11.ERR_NO_ERROR
        
        if False:
            error = vxi11.ERR_IO_TIMEOUT
        elif False:
            error = vxi11.ERR_IO_ERROR
        elif False:
            error = vxi11.ERR_ABORT
        else:
            error = vxi11.ERR_OPERATION_NOT_SUPPORTED
            
        return error

    def device_enable_srq(self, enable, handle): # = 20
        "The device_enable_srq RPC is used to enable or disable the sending of device_intr_srq RPCs by thenetwork instrument server"
        error = vxi11.ERR_NO_ERROR
        
        if enable == True:
            self.srq_handle = handle
            self.srq_enabled = True
        else:
            self.srq_enabled = False
            
        return error

    def device_docmd(self, flags, io_timeout, cmd, network_order, data_size, opaque_data_in): # = 22
        "The device_docmd RPC allows a variety of operations to be executed"
        error = vxi11.ERR_NO_ERROR
        
        if False:
            error = vxi11.ERR_IO_TIMEOUT
        elif False:
            error = vxi11.ERR_IO_ERROR
        elif False:
            error = vxi11.ERR_ABORT
        else:
            error = vxi11.ERR_OPERATION_NOT_SUPPORTED

        opaque_data_out = b""
        return error, opaque_data_out
        
class DefaultInstrumentDevice(InstrumentDevice):
    '''The default device is the device registered with the name of "inst0".

    The vxi-11 spec expects the default device to respond to the *IDN? command.
    If a custom default_device_handler is not specified when the InstrumentServer is
    initialized, this is the one that will be used.

    Many instruments have only one device, the "inst0" device.  copy this class 
    to YourDeviceHandler, use as boilerplate, and register it when the InstrumentServer
    is initialized.
    '''

    def device_init(self):
        self.idn = 'python-vxi11-server', 'bbb', '1234', '567'
        self.result = 'empty'
        return
    
    def device_write(self, opaque_data, flags, io_timeout):
        error = vxi11.ERR_NO_ERROR

        #opaque_data is a bytes array, so decode it correctly
        cmd=opaque_data.decode("ascii").strip()
        
        if cmd == '*IDN?':
            mfg, model, sn, fw = self.idn
            self.result = "{},{},{},{}".format(mfg, model, sn, fw)
        elif cmd  == '*DEVICE_LIST?':
            devs = self.device_list
            self.result = ''
            isFirst = True
            for dev in devs:
                if isFirst:
                    self.result = '{}'.format(dev)
                    isFirst = False
                else:
                    self.result = '{}, {}'.format(self.result, dev)
        else:
            self.result = 'invalid'
            
        logger.info("%s: device_write(): %s %s", self.name(), cmd , self.result)
        return error
    
    def device_read(self, request_size, term_char, flags, io_timeout):
        error = vxi11.ERR_NO_ERROR
        reason = ReadRespReason.END

        #device-read returns opaque_data so encode it correctly
        opaque_data = self.result.encode("ascii")
        
        return error, reason, opaque_data
