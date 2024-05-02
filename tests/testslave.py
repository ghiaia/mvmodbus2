# coding=utf-8

"""unittest script"""

import struct
import time
import unittest
import mvmodbus2

IPPLC = 'plcdev.mrc.loc.ghiaia.net'


class UDPServerTest(unittest.TestCase):
    """Controlla il funzionamento end2end di alcune func modbus"""
    def setUp(self):
        """Prepara un remoto per il test"""
        self.slave = mvmodbus2.modbus_udp(IPPLC)

    def tearDown(self):
        self.slave.sock.close()
        del self.slave

    def test_write_read_areaplc_ok(self):
        """Scrive un valore e poi lo rilegge nell'area PLC
        Cio' che viene scritto è rileggibile offset 0x200 su WAGO"""
        address = 280
        registers = (0xA1A1, 0x1A1A)
        msg = mvmodbus2.modbusf16(address, registers)
        response = self.slave.chat(msg)
        self.assertEqual(response, (address, 2))
        msg = mvmodbus2.modbusf4(address + 0x200, 2)
        response = self.slave.chat(msg)
        self.assertEqual(msg.bus_err, 0)
        self.assertEqual(response, registers)

    def test_write_read_areamerker_ok(self):
        """Scrive un valore e poi lo rilegge nell'area flags WAGO"""
        address = 0x3100
        registers = (0xA1A1, 0x1A1A)
        msg = mvmodbus2.modbusf16(address, registers)
        response = self.slave.chat(msg)
        self.assertEqual(response, (address, 2))
        msg = mvmodbus2.modbusf4(address, 2)
        response = self.slave.chat(msg)
        self.assertEqual(msg.bus_err, 0)
        self.assertEqual(response, registers)
        msg = mvmodbus2.modbusf3(address, 2)
        response = self.slave.chat(msg)
        self.assertEqual(msg.bus_err, 0)
        self.assertEqual(response, registers)

    def test_write_out_bit_ok(self):
        """Scrive un bit 0, lo controlla. Ripete per bit 1"""
        start_reg = 0
        bit = 7
        msg = mvmodbus2.modbusf5(start_reg, bit, False)
        response = self.slave.chat(msg)
        self.assertEqual(response, (start_reg * 16 + bit, 0x0000))
        msg = mvmodbus2.modbusf4(start_reg + 0x200, 1)
        response = self.slave.chat(msg)
        response = response[0] & (1 << bit)
        self.assertEqual(response, 0)
        time.sleep(1)
        msg = mvmodbus2.modbusf5(start_reg, bit, True)
        response = self.slave.chat(msg)
        self.assertEqual(response, (start_reg * 16 + bit, 0xFF00))
        msg = mvmodbus2.modbusf4(start_reg + 0x200, 1)
        response = self.slave.chat(msg)
        response = response[0] & (1 << bit)
        self.assertEqual(response, (1 << bit))


class TCPServerTest(UDPServerTest):
    """test modbus per connessione TCP"""
    def setUp(self):
        """Prepara un remoto per il test"""
        self.slave = mvmodbus2.modbus_tcp(IPPLC)


class ModbusFuncTest(unittest.TestCase):
    """Test sui generatori di messaggi"""

    def test_func5_msg(self):
        """Test della func 5"""
        start_reg = 10
        bit_index = 12
        expected_msg = struct.pack('B B B B B', 0x5, 0x0, 0xAC, 0xFF, 0x00)
        msg = mvmodbus2.modbusf5(start_reg, bit_index, True)
        msg.mkmsg()
        self.assertEqual(msg.msg, expected_msg)
        # func 5 response is echo of request
        coil_index = msg.answ(expected_msg)
        self.assertEqual(coil_index, (172, 0xFF00))

    def test_func4_bytes_left(self):
        """Test della func4 bytes left"""
        msg = mvmodbus2.modbusf4(0, 0)
        bytes_left = msg.bytes_left(b'\x04\x02\x00\x00')
        self.assertEqual(bytes_left, 0)
        bytes_left = msg.bytes_left(b'\x04\x02')
        self.assertEqual(bytes_left, 2)
        bytes_left = msg.bytes_left(b'')
        self.assertEqual(bytes_left, 2)
        with self.assertRaises(mvmodbus2.modbus_func.EFrame):
            bytes_left = msg.bytes_left(b'\x84\x02')

    def test_func3_bytes_left(self):
        """Test della func3 bytes left"""
        msg = mvmodbus2.modbusf3(0, 0)
        bytes_left = msg.bytes_left(b'\x03\x02\x00\x00')
        self.assertEqual(bytes_left, 0)
        bytes_left = msg.bytes_left(b'\x03\x02')
        self.assertEqual(bytes_left, 2)
        bytes_left = msg.bytes_left(b'')
        self.assertEqual(bytes_left, 2)
        with self.assertRaises(mvmodbus2.modbus_func.EFrame):
            bytes_left = msg.bytes_left(b'\x83\x02')

    def test_func5_bytes_left(self):
        """Test della func5 bytes left"""
        msg = mvmodbus2.modbusf5(0, 0, 0)
        bytes_left = msg.bytes_left(b'\x05\x01\x02\x03\x04')
        self.assertEqual(bytes_left, 0)
        bytes_left = msg.bytes_left(b'\x05\x01')
        self.assertEqual(bytes_left, 3)
        bytes_left = msg.bytes_left(b'')
        self.assertEqual(bytes_left, 2) # minimo 2: il caso error response
        with self.assertRaises(mvmodbus2.modbus_func.EFrame):
            bytes_left = msg.bytes_left(b'\x85\x02')

    def test_func16_bytes_left(self):
        """Test della func16 bytes left"""
        msg = mvmodbus2.modbusf16(0, [0])
        bytes_left = msg.bytes_left(b'\x10\x01\x02\x03\x04')
        self.assertEqual(bytes_left, 0)
        bytes_left = msg.bytes_left(b'\x10\x01')
        self.assertEqual(bytes_left, 3)
        bytes_left = msg.bytes_left(b'')
        self.assertEqual(bytes_left, 2) # minimo 2: il caso error response
        with self.assertRaises(mvmodbus2.modbus_func.EFrame):
            bytes_left = msg.bytes_left(b'\x90\x02')

    def test_func23_bytes_left(self):
        """Test della func23 bytes left"""
        msg = mvmodbus2.modbusf23(0, 0, 0, [0])
        bytes_left = msg.bytes_left(b'\x17\x02\x00\x00')
        self.assertEqual(bytes_left, 0)
        bytes_left = msg.bytes_left(b'\x17\x02')
        self.assertEqual(bytes_left, 2)
        bytes_left = msg.bytes_left(b'')
        self.assertEqual(bytes_left, 2)
        with self.assertRaises(mvmodbus2.modbus_func.EFrame):
            bytes_left = msg.bytes_left(b'\x97\x02')



def maintest(verbosity):
    "Avvia i test con verbosity dichiarata"
    suite3 = unittest.TestLoader().loadTestsFromTestCase(TCPServerTest)
    suite2 = unittest.TestLoader().loadTestsFromTestCase(UDPServerTest)
    suite1 = unittest.TestLoader().loadTestsFromTestCase(ModbusFuncTest)
    suite = unittest.TestSuite([suite1, suite2, suite3])
    unittest.TextTestRunner(verbosity=verbosity).run(suite)

if __name__ == '__main__':
    maintest(2)
