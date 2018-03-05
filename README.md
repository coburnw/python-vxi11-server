## VXI-11 Server in Python

A VXI-11 Server implementation in Python that allows your BeagleBone Black or possibly Raspberry PI to apear as a VXI-11 device.

VXI-11 is an instrument control protocol for accessing laboratory devices such as signal generators, power meters, and oscilloscope, over ethernet.  Python-Vxi11-Server makes your Beagle Bone Black or other linux/python enabled device appear as a VXI-11 ethernet instrument.  Coupled with python-vxi11 on the client side, controlling your device is seamless with any other vxi-11 device.

Heavily inspired by sonium0's [pyvxi11server](https://github.com/sonium0/pyvxi11server)

### Requirements
  * developed and tested with Python2.7.9

### Dependencies
#### Server
    none

#### Client
[python-vxi11](https://github.com/python-ivi/python-vxi11) or some other VXI-11 client library that enables interaction with a VXI-11 Server.

Altho there are no dependencies for the server, the only client library that was used durring development was python-vxi11.

### Getting started
#### server side
Git clone into the development folder of your instrument. Run the simple demo clock_instr.py program to start an instrument server that responds to the DATE and TIME commands.

#### Client side
Copy clock_client.py to the client folder/computer, and edit the connect string to reflect domain names or ip addresses of your network.  Run clock_client.py to extract the date and time from the clock_instr.
clock_client.py relies on [python-vxi11](https://github.com/python-ivi/python-vxi11) for interacting with the instrument server.  

### Instrument Server development
The Vxi11DeviceHandler class is the template for each instrument device that resides in an instrument server instance and should be the boilerplate used for your instrument implementation.  The boilerplate should make a fully funtioning instrument that does absolutely nothing.  You only need to implement/override the methods necessary to make the instrument do something. 

  * Place a copy the Vxi11DeviceHandler class into your code and rename the class to, say, my_device_handler
  * class my_device_handler(Vxi11DeviceHandler)
  * Delete any 'device_xxx' methods you choose not to override and flesh out the ones remaining.
  * in your __main__ routine, instantiate an instance of the server defining its name, and a default device if deemed necessary
  ''my_instr = Vxi11InstrumentServer(instr_name='INSTR', default_device=None)
  * register your version of the Vxi11DeviceHandler class
  '' my_instr.register_device_class(device_name, my_device_handler) ''
  * start waiting for requests my_instr.listen()
  * busy loop while server handles request: while True: sleep(1)
  
### Notes
  * remember that register_device_class requires a class definition not a class instance as indicated by the lack of parenthesis.  The server instantiates a new instance of your device handler class with each connect request.
  * Write a [python-ivi](https://github.com/python-ivi/python-ivi) driver for your new device

### Todo
  * come up with a simple default locking strategy to place in the Vxi11DeviceHandler class
  * same for abort functionality
