
"""RS-VISA Setup for Ubuntu can be downloaded and install at
https://www.rohde-schwarz.com/us/applications/r-s-visa-application-note_56280-148812.html

by @raphaelvalentin
"""

import unittest
import pyvisa
from pyvisa.constants import *

class Test1(unittest.TestCase):

    def test1(self):
        """ test create_link
        """
        rm = pyvisa.ResourceManager("/usr/lib/librsvisa.so")
        lib = rm.visalib
        visarmsession, statuscode = lib.open_default_resource_manager()
        try:
            visasession, statuscode = lib.open(visarmsession, "TCPIP0::127.0.0.1::inst0::INSTR")
            nbytes, statuscode = lib.write(visasession, "*IDN?\n")
            dbytes, statuscode = lib.read(visasession, 256)
            assert dbytes == b'my instrument zero', "has returned %r" % dbytes
        finally:
            lib.close(visasession)

    def test2(self):
        """ test create_link
        """
        rm = pyvisa.ResourceManager("/usr/lib/librsvisa.so")
        lib = rm.visalib
        visarmsession, statuscode = lib.open_default_resource_manager()
        try:
            visasession, statuscode = lib.open(visarmsession, "TCPIP0::127.0.0.1::inst1::INSTR")
            nbytes, statuscode = lib.write(visasession, "*IDN?\n")
            dbytes, statuscode = lib.read(visasession, 256)
            assert dbytes == b'my instrument one', "has returned %r" % dbytes
        finally:
            lib.close(visasession)

    def test3(self):
        """ test create_link twice
        """
        rm = pyvisa.ResourceManager("/usr/lib/librsvisa.so")
        lib = rm.visalib
        visarmsession, statuscode = lib.open_default_resource_manager()
        try:
            visasession1, statuscode = lib.open(visarmsession, "TCPIP0::127.0.0.1::inst0::INSTR", AccessModes.exclusive_lock, 10000)
            visasession2, statuscode = lib.open(visarmsession, "TCPIP0::127.0.0.1::inst1::INSTR", AccessModes.exclusive_lock, 10000)
            nbytes, statuscode = lib.write(visasession1, "*IDN?\n")
            dbytes, statuscode = lib.read(visasession1, 256)
            assert dbytes == b'my instrument zero', "has returned %r" % dbytes
            nbytes, statuscode = lib.write(visasession2, "*IDN?\n")
            dbytes, statuscode = lib.read(visasession2, 256)
            assert dbytes == b'my instrument one', "has returned %r" % dbytes
        finally:
            lib.close(visasession1)
            lib.close(visasession2)

    def test4(self):
        """ test create_link twice
        """
        rm = pyvisa.ResourceManager("/usr/lib/librsvisa.so")
        lib = rm.visalib
        visarmsession, statuscode = lib.open_default_resource_manager()
        try:
            visasession1, statuscode = lib.open(visarmsession, "TCPIP0::127.0.0.1::inst0::INSTR", AccessModes.exclusive_lock, 10000)
            visasession2, statuscode = lib.open(visarmsession, "TCPIP0::127.0.0.1::inst0::INSTR", AccessModes.exclusive_lock, 10000)
        finally:
            lib.close(visasession1)
            lib.close(visasession2)

    def test5(self):
        """ test create_link with not registered device name
        """
        rm = pyvisa.ResourceManager("/usr/lib/librsvisa.so")
        lib = rm.visalib
        visarmsession, statuscode = lib.open_default_resource_manager()
        try:
            with self.assertRaisesRegex(Exception, "error creating link: 3") as cm:
                lib.open(visarmsession, "TCPIP0::127.0.0.1::inst3::INSTR", AccessModes.exclusive_lock, 10000)
        finally:
            lib.close(visarmsession)

if __name__ == '__main__':
    unittest.main()
