# this unit test is tuned to the in-tree version of the vxi11.py library.
# The in tree version has the addition of a client lock_on_open option among others.

# adapted from work by @raphaelvalentin

import os
import sys
import unittest

sys.path.append(os.path.abspath('..'))
import vxi11_server as vxi11

class Test1(unittest.TestCase):

    def test1(self):
        """ Verify default (inst0) instrument
        """
        try:
            inst0 = vxi11.Instrument("TCPIP::127.0.0.1::INSTR")
            inst0.open()
            
            inst0.write("*IDN?\n")
            dbytes = inst0.read()
            assert dbytes == 'my instrument zero', "has returned %r" % dbytes
        finally:
            inst0.close()

    def test2(self):
        """ Verify inst1 instrument
        """
        try:
            inst1 = vxi11.Instrument("TCPIP::127.0.0.1::inst1::INSTR")
            inst1.open()

            inst1.write("*IDN?\n")
            dbytes = inst1.read()
            assert dbytes == 'my instrument one', "has returned %r" % dbytes
        finally:
            inst1.close()

    def test3(self):
        """ Verify multiple devices on the same server can be opened with locks
        """
        try:
            inst0 = vxi11.Instrument("TCPIP::127.0.0.1::inst0::INSTR", lock_on_open=True)
            inst0.open()
            
            inst1 = vxi11.Instrument("TCPIP::127.0.0.1::inst1::INSTR", lock_on_open=True)
            inst1.open()
            
            inst0.write("*IDN?\n")
            dbytes = inst0.read()
            assert dbytes == 'my instrument zero', "has returned %r" % dbytes

            inst1.write("*IDN?\n")
            dbytes = inst1.read()
            assert dbytes == 'my instrument one', "has returned %r" % dbytes
        finally:
            inst0.close()
            inst1.close()

    def test4(self):
        """ Verify only one instance of a specific device can be opened with a lock
        """
        try:
            inst0a = vxi11.Instrument("TCPIP::127.0.0.1::inst0::INSTR", lock_on_open=True)    
            inst0a.open()

            inst0b = vxi11.Instrument("TCPIP::127.0.0.1::inst0::INSTR", lock_on_open=True)
            with self.assertRaisesRegex(Exception, "Device locked by another link") as cm:
                inst0b.open()
        finally:
            inst0a.close()
            inst0b.close()

    def test5(self):
        """ test create_link with invalid device name
        """
        try:
            with self.assertRaisesRegex(Exception, "Device not accessible") as cm:
                inst0 = vxi11.Instrument("TCPIP::127.0.0.1::inst3::INSTR")            
                inst0.open()

                inst0.write("*IDN?\n")
                dbytes = inst0.read()
                assert dbytes == 'my instrument zero', "has returned %r" % dbytes
        finally:
            inst0.close()
            pass

    def test6(self):
        """ Verify multiple instances of a specific device can be accessed without a lock
        """
        try:
            inst0a = vxi11.Instrument("TCPIP::127.0.0.1::inst0::INSTR")            
            inst0a.open()

            inst0b = vxi11.Instrument("TCPIP::127.0.0.1::inst0::INSTR")            
            inst0b.open()

            inst0a.write("*IDN?\n")
            dbytes = inst0a.read()
            assert dbytes == 'my instrument zero', "has returned %r" % dbytes
            
            inst0b.write("*IDN?\n")
            dbytes = inst0b.read()
            assert dbytes == 'my instrument zero', "has returned %r" % dbytes
        finally:
            inst0a.close()
            inst0b.close()
            
if __name__ == '__main__':
    unittest.main()
