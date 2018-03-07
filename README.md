## VXI-11 Server in Python

A VXI-11 Server implementation in Python that allows your BeagleBone Black or possibly Raspberry PI to apear as a VXI-11 device.

VXI-11 is an instrument control protocol for accessing laboratory devices such as signal generators, power meters, and oscilloscope, over ethernet.

python-vxi11-server makes your Beagle Bone Black or other linux/python enabled device work as a VXI-11 ethernet instrument.  Coupled with python-vxi11 on the client side, controlling your device is seamless with any other VXI-11 device.

Since VXI-11 specifies how instrument control and data messages transfer over ethernet, libraries such as this one and python-vxi11 do the hard work of setting up and tearing down the link, packing and unpacking the data, and getting the data to the proper endpoints. You and I can get on with our testing.

Inspired by sonium0's [pyvxi11server](https://github.com/sonium0/pyvxi11server)

### Requirements
  * developed and tested with Python2.7.9

### Dependencies
#### Server
none

#### Client
[python-vxi11](https://github.com/python-ivi/python-vxi11) or some other VXI-11 client library that enables interaction with a VXI-11 Server.

Altho there are no dependencies for the server, the only client library it was tested against was python-vxi11.  Other clients may expose various server bugs or protocol misunderstandings by this developer.  Lets address them as they come.

### Getting started
#### server side
Git clone into the development folder of your instrument. Run the simple demo clock_instr.py program to start an instrument server that responds to the DATE and TIME commands.

#### Client side
Copy clock_client.py to the client folder/computer, and edit the connect string to reflect domain names or ip addresses of your network.  Run clock_client.py to extract the date and time from the clock_instr.
clock_client.py relies on [python-vxi11](https://github.com/python-ivi/python-vxi11) for interacting with the instrument server.  

### Instrument Server development
The Vxi11DeviceHandler class is the template for each instrument device that resides in an instrument server instance and should be the boilerplate used for your instrument implementation.  The boilerplate should make a fully funtioning instrument that does absolutely nothing.  You need only implement/override the methods necessary to make the instrument do something. 

see TCP/IP Instrument Protocol Specification at [vxibus](http://www.vxibus.org/specifications.html) for help with the VXI-11 device_xxxx commands.

For instance here is a very simple VXI-11 time server device:

    import vxi11_server
    import time

    class TimeDeviceHandler(vxi11_server.Vxi11DeviceHandler):
        def __init__(self):
            super(TimeDeviceHandler, self).__init__()
            self.device_name = 'TIME'
        
        def device_read(self):
            error = 0
	    result = time.strftime("%H:%M:%S +0000", time.gmtime())
            return error, result

    if __name__ == '__main__':
        instr_server = vxi11_server.Vxi11InstrumentServer('INSTR')    
        instr_server.register_device_class('TIME', TimeDeviceHandler)
        instr_server.listen()

	# sleep (or do other work) while the server threads do their job
        while True:
    	    sleep(1)


To access the time server using python-vxi11 as the client library:

    import vxi11

    instr = vxi11.Instrument("TCPIP::192.168.0.9::TIME::INSTR")

    #read the current time value from the instruments TIME device
    instr.read()  

  
### Notes
  * be aware that register_device_class requires a class definition not a class instance as indicated by the lack of parenthesis.  The server instantiates a new instance of your device handler class with each connect request.
  * Write a [python-ivi](https://github.com/python-ivi/python-ivi) driver for your new device

### Todo
  * come up with a simple default locking strategy to place in the Vxi11DeviceHandler class
  * same for abort functionality
  * follow through on default_device
  * get rid of need for calling super.__init__()
