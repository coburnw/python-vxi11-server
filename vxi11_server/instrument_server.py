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


from . import rpc
from . import vxi11

import os
import logging
import threading
import socketserver

from . import instrument_device as Instrument

MAX_RECEIVE_SIZE = 1024

logger = logging.getLogger(__name__)

class Error(object):
    '''vxi11 specification error constants'''
    NO_ERROR = vxi11.ERR_NO_ERROR
    SYNTAX_ERROR = vxi11.ERR_SYNTAX_ERROR
    DEVICE_NOT_ACCESSIBLE = vxi11.ERR_DEVICE_NOT_ACCESSIBLE
    INVALID_LINK_IDENTIFIER = vxi11.ERR_INVALID_LINK_IDENTIFIER
    PARAMETER_ERROR = vxi11.ERR_PARAMETER_ERROR
    CHANNEL_NOT_ESTABLISHED = vxi11.ERR_CHANNEL_NOT_ESTABLISHED
    OPERATION_NOT_SUPPORTED = vxi11.ERR_OPERATION_NOT_SUPPORTED
    OUT_OF_RESOURCES = vxi11.ERR_OUT_OF_RESOURCES
    DEVICE_LOCKED_BY_ANOTHER_LINK = vxi11.ERR_DEVICE_LOCKED_BY_ANOTHER_LINK
    NO_LOCK_HELD_BY_THIS_LINK = vxi11.ERR_NO_LOCK_HELD_BY_THIS_LINK
    IO_TIMEOUT = vxi11.ERR_IO_TIMEOUT
    IO_ERROR = vxi11.ERR_IO_ERROR
    INVALID_ADDRESS = vxi11.ERR_INVALID_ADDRESS
    ABORT = vxi11.ERR_ABORT
    CHANNEL_ALREADY_ESTABLISHED = vxi11.ERR_CHANNEL_ALREADY_ESTABLISHED
    
class LockedIncrementer(object):
    _value = 0 #private global.

    #contain a list of active sessions also?
    #client_id = random.getrandbits(31)
    def __init__(self, start_value):
        self.lock = threading.Lock()
        self._value = start_value
                
    def next(self):
        self.lock.acquire()
        try:
            self._value = self._value + 1
            return self._value
        finally:
            self.lock.release()
            
# Packers unique to this project
class Packer(vxi11.Packer):
    def pack_device_error(self, error):
        self.pack_int(0)        #fill in opaque_results in RPC accepted_reply
        self.pack_int(error)

    def pack_destroy_link_resp(self, error):
        self.pack_device_error(error)
        
class Unpacker(vxi11.Unpacker):
    def unpack_destroy_link_parms(self):
        link = self.unpack_int()
        return link

class Registry(object):
    def __init__(self):
        registry = {}
        return
    
    def add(self, key, item):
        self._device_class_registry[key] = item
        return
    
    def remove(self, key):
        del self._device_class_registry[key]
        return
    
    def list(self):
        return self.registry.keys()
    
    
class Vxi11Server(socketserver.ThreadingMixIn, rpc.TCPServer):
    _next_device_index = 0
    _device_class_registry = {}
    _link_registry = {}

    def __init__(self, host, prog, vers, port, handler_class):
        rpc.TCPServer.__init__(self, host, prog, vers, port, handler_class)
        self.lid_gen = LockedIncrementer(200)
        return

    # move device_class_registry, link_create/delete to CoreHandler?
    def link_create(self, device_name):        
        # create and initialize an instance of the device handler registered to device_name
        device_instance = self._device_class_registry[device_name](device_name)
        
        # and register it to a new link_id
        link_id = self.lid_gen.next()
        self._link_registry[link_id] = device_instance
        
        return link_id, self._link_registry[link_id]
        
    def link_delete(self, link_id):
        del self._link_registry[link_id]
        return

    #def link_name(self, link_id):
    #    return self._link_registry[link_id]
    
    def link_abort(self, link_id):
        try:
            device_instance =  self._link_registry[link_id]
            logger.debug('AbortServer: ABORT_LINK_ID %s to %s', link_id, self._link_registry[link_id])
            error = device_instance.device_abort()
        except KeyError :
            logger.debug('AbortServer: ABORT_LINK_ID %s. link_id does not exist.', link_id)
            error = vxi11.ERR_INVALID_LINK_IDENTIFIER

        return

    # should the device registry be moved to the core server?
    def device_register(self, name, device_class):
        if name is None:
            while 'inst' +  str(self._next_device_index) in self._device_class_registry:
                self._next_device_index += 1
            name = 'inst' +  str(self._next_device_index)

        if name in self._device_class_registry:
            raise KeyError
        self._device_class_registry[name] = device_class
        
    def device_unregister(self, name):
        del self._device_class_registry[name]

    def device_list(self):
        return self._device_class_registry.keys()
    
class Vxi11Handler(rpc.RPCRequestHandler):
    def addpackers(self):
        # amend rpc packers with our vxi11 packers
        self.packer = Packer()
        self.unpacker = Unpacker('')
        return
    
class Vxi11AbortServer(Vxi11Server):
    def __init__(self):
        Vxi11Server.__init__(self, '', vxi11.DEVICE_ASYNC_PROG, vxi11.DEVICE_ASYNC_VERS, 0, Vxi11AbortHandler)
        return
    
class Vxi11AbortHandler(Vxi11Handler):
    def handle_1(self):
        params = self.unpacker.unpack_device_link()
        link_id = params
        self.server.link_abort(link_id)

        self.packer.pack_device_error(0)
        return
    
class Vxi11CoreServer(Vxi11Server):
    def __init__(self, abort_port):
        Vxi11Server.__init__(self, '', vxi11.DEVICE_CORE_PROG, vxi11.DEVICE_CORE_VERS, 0, Vxi11CoreHandler)
        self.abort_port = abort_port
        return
    
class Vxi11CoreHandler(Vxi11Handler):
        
    def handle_10(self):
        '''The create_link RPC creates a new link. 
        This link is identified on subsequent RPCs by the lid returned from the network instrument server.'''
        
        params = self.unpacker.unpack_create_link_parms()
        client_id, lock_device, lock_timeout, device_name = params

        logger.debug('****************************')
        logger.debug('CREATE_LINK %s' ,params)

        self.link_id = 0
        abort_port = 0
        #maxlen = 1024
        error = vxi11.ERR_NO_ERROR
        
        try:
            logger.debug("Device name \"%s\"", device_name)
            self.link_id, self.device = self.server.link_create(device_name)
            if device_name == 'inst0':
                self.device.device_list = self.server.device_list
            abort_port = self.server.abort_port
        except KeyError:
            error = vxi11.ERR_DEVICE_NOT_ACCESSIBLE
            logger.debug("Create link failed")
        
        result = (error, self.link_id, abort_port, MAX_RECEIVE_SIZE)
        self.packer.pack_create_link_resp(result)
        return
    
    def handle_23(self):
        "The destroy_link call is used to close the identified link.  The network instrument server recovers resources associated with the link"
        
        params = self.unpacker.unpack_destroy_link_parms()
        link_id = params

        error = vxi11.ERR_NO_ERROR
        if link_id != self.link_id:
            error = vxi11.ERR_INVALID_LINK_IDENTIFIER
        else:
            logger.debug('DESTROY_LINK %s to %s', link_id, self.device.device_name)
            self.server.link_delete(self.link_id)
            error = vxi11.ERR_NO_ERROR
            
        self.packer.pack_destroy_link_resp(error)
        return
    
    def handle_11(self):
        "The device_write RPC is used to write data to the specified device"
        
        params = self.unpacker.unpack_device_write_parms()
        logger.debug('DEVICE_WRITE %s', params)
        link_id, io_timeout, lock_timeout, flags, opaque_data = params

        if link_id != self.link_id:
            error = vxi11.ERR_INVALID_LINK_IDENTIFIER
        elif len(opaque_data) > MAX_RECEIVE_SIZE:
            error = vxi11.ERR_PARAMETER_ERROR
        else:
            error = self.device.device_write(opaque_data)
            
        if error != 0:
            result = (error, 0)
        else:
            result = (error, len(opaque_data))
        self.packer.pack_device_write_resp(result)
        return
    
    def handle_12(self):
        "The device_read RPC is used to read data from the device to the controller"
        
        params = self.unpacker.unpack_device_read_parms()
        logger.debug('DEVICE_READ %s', params)
        link_id, request_size, io_timeout, lock_timeout, flags, termChar = params

        opaque_data = ''
        if link_id != self.link_id:
            error = vxi11.ERR_INVALID_LINK_IDENTIFIER
        else:
            error, opaque_data = self.device.device_read()
            
        reason = vxi11.RX_END
        result = (error, reason, opaque_data)
        self.packer.pack_device_read_resp(result)
        return
    
    def handle_13(self):
        "The device_readstb RPC is used to read a device's status byte."
        
        params = self.unpacker.unpack_device_generic_parms()
        logger.debug('DEVICE_READSTB %s', params)
        link_id, flags, lock_timeout, io_timeout = params

        error = vxi11.ERR_NO_ERROR
        if link_id != self.link_id:
            error = vxi11.ERR_INVALID_LINK_IDENTIFIER
        else:
            error = self.device.device_readstb(link_id, flags, lock_timeout, io_timeout)
            
        opaque_data = 0
        result = (error, opaque_data)
        self.packer.pack_device_read_stb_resp(result)
        return
    
    def handle_14(self):
        "The device_trigger RPC is used to send a trigger to a device."
        
        params = self.unpacker.unpack_device_generic_parms()
        logger.debug('DEVICE_TRIGGER %s', params)
        link_id, flags, lock_timeout, io_timeout = params

        error = vxi11.ERR_NO_ERROR
        if link_id != self.link_id:
            error = vxi11.ERR_INVALID_LINK_IDENTIFIER
        else:
            error = self.device.device_trigger(flags, lock_timeout, io_timeout)
            
        self.packer.pack_device_error(error)
        return
    
    def handle_15(self):
        "The device_clear RPC is used to send a device clear to a device"
        
        params = self.unpacker.unpack_device_generic_parms()
        logger.debug('DEVICE_CLEAR %s', params)
        link_id, flags, lock_timeout, io_timeout = params

        error = vxi11.ERR_NO_ERROR
        if link_id != self.link_id:
            error = vxi11.ERR_INVALID_LINK_IDENTIFIER
        else:
            error = self.device.device_clear(flags, lock_timeout, io_timeout)
            
        self.packer.pack_device_error(error)
        return
    
    def handle_16(self):
        "The device_remote RPC is used to place a device in a remote state wherein all programmable local controls are disabled"
        
        params = self.unpacker.unpack_device_generic_parms()
        logger.debug('DEVICE_REMOTE %s', params)
        link_id, flags, lock_timeout, io_timeout = params

        error = vxi11.ERR_NO_ERROR
        if link_id != self.link_id:
            error = vxi11.ERR_INVALID_LINK_IDENTIFIER
        else:
            error = self.device.device_remote(flags, lock_timeout, io_timeout)
            
        self.packer.pack_device_error(error)
        return
    
    def handle_17(self):
        "The device_local RPC is used to place a device in a local state wherein all programmable local controls are enabled"
        
        params = self.unpacker.unpack_device_generic_parms()
        logger.debug('DEVICE_LOCAL %s', params)
        link_id, flags, lock_timeout, io_timeout = params

        error = vxi11.ERR_NO_ERROR
        if link_id != self.link_id:
            error = vxi11.ERR_INVALID_LINK_IDENTIFIER
        else:
            error = self.device.device_local(flags, lock_timeout, io_timeout)
            
        self.packer.pack_device_error(error)
        return
    
    def handle_18(self):
        "The device_lock RPC is used to acquire a device's lock"
        
        params = self.unpacker.unpack_device_lock_parms()
        logger.debug('DEVICE_LOCK %s', params)
        link_id, flags, lock_timeout = params

        error = vxi11.ERR_NO_ERROR
        if link_id != self.link_id:
            error = vxi11.ERR_INVALID_LINK_IDENTIFIER
        else:
            error = self.device.device_lock(flags, lock_timeout)
            
        self.packer.pack_device_error(error)
        return
    
    def handle_19(self):
        "The device_unlock RPC is used to release locks acquired by the device_lock RPC"
        
        params = self.unpacker.unpack_device_generic_parms()
        logger.debug('DEVICE_UNLOCK %s', params)
        link_id, flags, lock_timeout, io_timeout = params

        error = vxi11.ERR_NO_ERROR
        if link_id != self.link_id:
            error = vxi11.ERR_INVALID_LINK_IDENTIFIER
        else:
            error = self.device.device_unlock(flags, lock_timeout, io_timeout)
            
        self.packer.pack_device_error(error)
        return
    
    def handle_25(self):
        "The create_intr_chan RPC is used to inform the network instrument server to establish an interrupt channel"
        
        params = self.unpacker.unpack_device_create_intr_chan_parms()
        logger.debug('DEVICE_CREATE_INTR_CHAN %s', params)
        host_addr, host_port, prog_num, prog_vers, prog_family = params

        error = vxi11.ERR_CHANNEL_NOT_ESTABLISHED
        self.packer.pack_device_error(error)
        return
    
    def handle_26(self):
        "The destroy_intr_chan RPC is used to inform the network instrument server to close its interrupt channel"
        
        #params = self.unpacker.unpack_device_generic_parms()
        logger.debug('DEVICE_DESTROY_INTR_CHAN %s', params)

        error = vxi11.ERR_NO_ERROR
        self.packer.pack_device_error(error)
        return
        
    def handle_20(self):
        "The device_enable_srq RPC is used to enable or disable the sending of device_intr_srq RPCs by thenetwork instrument server"
        
        params = self.unpacker.unpack_device_enable_srq_parms()
        logger.debug('DEVICE_ENABLE_SRQ %s', params)
        link_id, enable, handle = params

        error = vxi11.ERR_NO_ERROR
        if link_id != self.link_id:
            error = vxi11.ERR_INVALID_LINK_IDENTIFIER
        else:
            error = vxi11.ERR_NO_ERROR

        self.packer.pack_device_error(error)
        return
    
    def handle_22(self):
        "The device_docmd RPC allows a variety of operations to be executed"
        
        params = self.unpacker.unpack_device_generic_parms()
        logger.debug('DEVICE_DOCMD %s', params)
        link_id, flags, io_timeout, lock_timeout, cmd, network_order, data_size, opaque_data_in = params

        error = vxi11.ERR_NO_ERROR
        opaque_data_out = ""
        if link_id != self.link_id:
            error = vxi11.ERR_INVALID_LINK_IDENTIFIER
        else:
            error, opaque_data_out = self.device.device_docmd(flags, io_timeout, lock_timeout, cmd, network_order, data_size, opaque_data_in)
            
        result = error, opaque_data_out
        self.packer.pack_device_docmd(result)
        return
    

class InstrumentServer():
    '''Maintains a registry of device handlers and routes incoming client RPC's to appropriate handler.
    '''
    def __init__(self, default_device_handler=None):
        '''Initialize the instrument and start a default device handler on inst0.
        
        default_device_handler: (optional) a device_handler class to be use
            as the default devive handler registered as "inst0".
        '''
        self.abortServer = Vxi11AbortServer()

        abort_host, abort_port = self.abortServer.server_address
        self.coreServer = Vxi11CoreServer(abort_port)

        if default_device_handler is None:
            default_device_handler = Instrument.DefaultInstrumentDevice

        self.add_device_handler(default_device_handler, 'inst0')
        return

    def add_device_handler(self, device_handler, device_name=None ):
        '''registers a device handler to serve client requests.

        device_handler: device handler class to handle incoming requests on device_name.
        device_name: (optional) name of device to be used in clients connect string. 
              if none supplied, next available "inst" used
        '''
        self.coreServer.device_register(device_name, device_handler)
        return(True)
    
    def close(self):
        logger.info('Closing...')
        self.coreServer.unregister()
        self.coreServer.shutdown()
        self.coreServer.server_close()

        self.abortServer.shutdown()
        self.abortServer.server_close()
        logger.info('Closed.')
        return(True)
        
    def listen(self, loglevel = 'DEBUG'): # 'INFO'
        #self.ch.setLevel(getattr(logging, loglevel))

        abortThread = threading.Thread(target=self.abortServer.serve_forever)
        abortThread.setDaemon(True) # don't hang on exit
        abortThread.start()
        logger.info('abortServer started...')

        self.coreServer.register()
        coreThread = threading.Thread(target=self.coreServer.serve_forever)
        coreThread.setDaemon(True)
        coreThread.start()
        logger.info('coreServer started...')
        return(True)
    
