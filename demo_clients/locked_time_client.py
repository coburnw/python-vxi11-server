import time

import vxi11

# with a default instrument, inst0 is implied.
default_instr = vxi11.Instrument("TCPIP::127.0.0.1::INSTR")
time_instr = vxi11.Instrument("TCPIP::127.0.0.1::inst1::INSTR")
#time_instr = vxi11.Instrument("TCPIP::192.168.2.101::TIME::INSTR")

print('The INSTR instrument:')

default_instr.write('*IDN?')
print(default_instr.read())

print('contains the following devices:')
default_instr.write('*DEVICE_LIST?')
print(default_instr.read())

print()
print('The TIME device has a current value of:')
while True:
    try:
        result = time_instr.lock()
    except Exception as ex:
        print(ex)
    else:
        is_locked = True
        while is_locked:
            try:
                print(time_instr.read())
            except Exception as ex:
                print(ex)
                is_locked = False
            time.sleep(1)
    time.sleep(1)
    
