import vxi11

default_instr = vxi11.Instrument("TCPIP::192.168.2.101::INSTR")
#time_instr = vxi11.Instrument("TCPIP::192.168.2.101::TIME::INSTR")
time_instr = vxi11.Instrument("TCPIP::192.168.2.101::inst0::INSTR")

print('The INSTR instrument:')

default_instr.write('*IDN?')
print(default_instr.read())

print('contains the following devices:')
default_instr.write('*DEVICE_LIST?')
print(default_instr.read())

print()
print('The TIME device has a current value of:')
print(time_instr.read())
