## VXI-11 Server in Python

A VXI-11 Server implementation in Python that allows your BeagleBone Black or Raspberry PI appear as a VXI-11 device.

VXI-11 is an instrument control protocol for accessing laboratory devices such as signal generators, power meters, and oscilloscopes over ethernet.

python-vxi11-server makes your Beagle Bone Black or other linux/python enabled device work as a VXI-11 ethernet instrument.  Coupled with python-vxi11 on the client side, controlling your device over ethernet is seamless with your other VXI-11 devices.

Since VXI-11 specifies how instrument control and data messages transfer over ethernet, libraries such as this one and python-vxi11 do the hard work of setting up and tearing down the link, packing and unpacking the data, and getting the data to the proper endpoints.

Inspired by sonium0's [pyvxi11server](https://github.com/sonium0/pyvxi11server)

### Requirements
  * Ported to Python 3 and tested on the RPi

### Dependencies
#### Server
  * rpcbind package
  On a systemd os, use the command ```systemctl status rpcbind``` to verify run status.

#### Client
  * [python-vxi11](https://github.com/python-ivi/python-vxi11) or some other VXI-11 client library that enables interaction with VXI-11 devices.

The only client library tested against is python-vxi11.  Other clients may expose various server bugs or protocol misunderstandings by the developer.  Lets address them as they come.

### Getting started
Unlike a client library, this 'package' is not installed.  Simply clone and copy into the source tree of your project.

#### server side
Run the simple demo clock_device.py program to start an instrument server that responds to a read command with the current time.  Address any portmapper (rpcbind?) issues that may occur.

#### Client side
Copy clock_client.py to the client folder/computer and edit the connect string to reflect domain names or ip addresses of your network.  Run clock_client.py to extract the time from the server's clock_device.
clock_client.py relies on [python-vxi11](https://github.com/python-ivi/python-vxi11) for interacting with the instrument server.  Install python-vxi11 or adapt to your client library.

### Instrument Device development
The InstrumentDevice base class is the handler for each instrument device that resides in an instrument server and should be the base class for your instrument implementation.  The base class alone should make a fully functioning instrument that does absolutely nothing, the right way.  Only override the methods necessary to make your instrument respond to the VXI-11 requests that are important for your instrument.

See 'TCP/IP Instrument Protocol Specification' at [vxibus](http://www.vxibus.org/specifications.html) for help with the VXI-11 device_xxxx commands.

For instance here is a very simple VXI-11 time server device that defines an InstrumentDevice handler and overrides just the device_read() function of the base class:

    import time
    import vxi11_server as Vxi11

    class TimeDevice(Vxi11.InstrumentDevice):
        def __init__(self, device_name):
            super().__init__(device_name)

        def device_read(self):
            '''respond to the device_read rpc: refer to section (B.6.4)
               of the VXI-11 TCP/IP Instrument Protocol Specification'''
            error = Vxi11.Error.NO_ERROR
            result = time.strftime("%H:%M:%S +0000", time.gmtime())
            return error, result

    if __name__ == '__main__':
        # create a server, attach a device, and start a thread to listen for requests
        instr_server = Vxi11.InstrumentServer()
        instr_server.add_device_handler(TimeDevice, 'inst1')
        instr_server.listen()

        # sleep (or do foreground work) while the Instrument threads do their job
        while True:
       	    time.sleep(1)


To access the time server using python-vxi11 as the client library:

    import vxi11

    instr = vxi11.Instrument("TCPIP::127.0.0.1::inst1::INSTR")

    #read the current time value from the instruments TimeDevice
    instr.read()

  
### Notes
  * be aware that add_device_handler requires a class definition not a class instance as indicated by the lack of parenthesis.  The server instantiates a new instance of your device handler class with each connect request.
  * Write a [python-ivi](https://github.com/python-ivi/python-ivi) driver for your new device
  * no attempt to harden or benchmark the code has been made.  use at own risk.

### Examples Projects
  * [GPIB Bridge](https://git.loetlabor-jena.de/thasti/tcpip2instr)
  
### Todo
  * come up with a simple default locking strategy to place in the InstrumentDevice base class
  * same for abort functionality
  * get rid of need for calling super.__init__()
