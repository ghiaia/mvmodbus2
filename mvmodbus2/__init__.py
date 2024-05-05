"""Modbus implementation as per
MODBUS.org
Modbus_Application_Protocol_V1_1b3.pdf
Modbus_Messaging_Implementation_Guide_V1_0b.pdf"""

import select
import socket
import struct
import time
import termios

# pylint: disable=invalid-name



class EFrame(BaseException):
    """Exception"""


class EAgain(BaseException):
    """Exception"""


class ETout(BaseException):
    """Exception"""


def crc16(msg):
    """Calcola il CRC16. Algoritmo di MODBUS.org
    per modbus su seriale"""
    register = 0xffff
    for c in msg:
        register = register ^ c
        for dummy_i in range(0, 8):
            flag = register & 1
            register >>= 1
            if flag:
                register = register ^ 0xA001
    return struct.pack('<H', register)


def modbus_build_TCP_message(mod_func):
    """Get from the initialized mod_func object the message and build the MBAP header"""
    mod_func.mkmsg()
    transaction_identifier = mod_func.transaction_identifier
    protocol_identifier = 0
    unit_identifier = mod_func.unit_identifier
    length = len(mod_func.msg) + 1 # 1: length of unit identifier

    mbap = struct.pack(
        '> H H H B', transaction_identifier, protocol_identifier,
            length,
            unit_identifier
        )
    return mbap + mod_func.msg


def modbus_build_RTU_message(mod_func):
    """Get from the initialized mod_func object the message and build the RTU frame"""
    mod_func.mkmsg()
    msg = struct.pack(
        f'> B {len(mod_func.msg)}s',
        mod_func.unit_identifier,
        mod_func.msg)
    crc = crc16(msg)
    return msg + crc


class modbus_udp:
    """UDP connection to server (slave)
    The implementation assumes that the slave (server)
    sends the response in a single packet.
    This is the WAGO PLC behaviour in a LAN
    """
    def __init__(self, clie_addr, port=502, timeout=4):
        self.timeout = timeout
        self.clie_addr = (clie_addr, port)
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.settimeout(timeout)

    def send(self, mod_func):
        """Chiede all'oggetto mod_func, gia inizializzato,
        il messaggio e lo invia"""
        msg = modbus_build_TCP_message(mod_func)
        self.sock.sendto(msg, self.clie_addr)

    def recv(self, mod_func):
        """Riceve i dati nella quantita massima prevista dall'oggetto MOD_FUNC
        e risponde la risposta decodificata.

        UDP risponde in un unico frame. Tutto o niente
        """
        return mod_func.answ(self.sock.recv(mod_func.ANSW_LEN)[7:])

    def chat(self, mod_func):
        """Esegue la sequenza invio, risposta"""
        self.send(mod_func)
        return self.recv(mod_func)


class modbus_tcp:
    """TCP connection to slave.
    L'implementazione prevede il caso che lo slave (server)
    invii la risposta frazionata in più pacchetti.
    Il metodo chat dunque non è bloccante
    """
    def __init__(self, clie_addr, port=502, timeout=4):
        """Assume i dati di collegamento e crea il socket TCP"""
        self.clie_addr = (clie_addr, port)
        self.timeout = timeout
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.settimeout(timeout)
        self.sock.connect(self.clie_addr)

    def send(self, mod_func):
        """Chiede all'oggetto mod_func,
        gia inizializzato, il messaggio e lo invia"""
        msg = modbus_build_TCP_message(mod_func)
        self.sock.send(msg)

    def recv(self, mod_func):
        """Riceve i dati nella quantita massima prevista dall'oggetto MOD_FUNC
        e risponde la risposta decodificata"""
        rcv_buf = b''
        next_read_len = mod_func.bytes_left(rcv_buf[7:]) + 7
        for _tentativi in range(0, 255): # tenta di soddisfare la richiesta.
            if ([], [], []) == select.select([self.sock], [], [], self.timeout):
                raise socket.timeout
            rcv_buf += self.sock.recv(next_read_len)
            next_read_len = mod_func.bytes_left(rcv_buf[7:])
            if next_read_len == 0:
                try:
                    return mod_func.answ(rcv_buf[7:])
                except struct.error:
                    pass
        raise ETout(repr(rcv_buf)) # dopo letture (senza timeout) ancora mancano dati.

    def chat(self, mod_func):
        """Esegue la sequenza invio, risposta"""
        self.send(mod_func)
        return self.recv(mod_func)


def prova():
    """Prova e test di funzionamento"""
    srv = modbus_tcp('10.36.20.25', port=26, timeout=2)
    msg = modbusf3(3022, 4, unit_identifier=11, transaction_identifier=0)
    recv = srv.chat(msg)
    print(recv)
    srv = modbus_udp('plcdev2.mrc.loc.ghiaia.net', timeout=2)
    msg = modbusf4(0, 10, unit_identifier=11, transaction_identifier=0)
    recv = srv.chat(msg)
    print(recv)


class modbus_serial(object):
    """Serial connection"""
    def __init__(self):
        # wait_answ vale:
        #    0: non si attende risposta
        #    1: avviare ricezione risposta
        #    2: ricevuto intestazione (byte count). In attesa del rimanente
        #    3: ricevuto
        self.wait_answ = 0
        self.fase = 0
        self.rcv_buf = b''
        self.start_chat = 0
        self.send_count = 0
        self.serial = None
        self.use_socket = None
        self.address = None

    def start_serial(self, name, speed=termios.B9600):
        """start serial con name device"""
        self.serial = open(name, 'rb+', 0)
        try:
            ts = termios.tcgetattr(self.serial)
            ts[0] = termios.IGNBRK | termios.IGNPAR
            ts[1] = 0
            ts[2] = (termios.CS8 | termios.CREAD | termios.HUPCL |
                     termios.CLOCAL)
            ts[3] = 0
            ts[4] = termios.B0
            ts[5] = termios.B0
            ts[6][termios.VMIN] = 0
            ts[6][termios.VTIME] = 0
            termios.tcsetattr(self.serial, termios.TCSANOW, ts)
            ts[4] = speed
            ts[5] = speed
            termios.tcsetattr(self.serial, termios.TCSANOW, ts)
        except termios.error:
            pass
        self.use_socket = False

    def tcp_start_serial(self, name, timeout=5):
        """Start e remote serial via TCP"""
        self.address = name
        self.serial = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.serial.settimeout(timeout)
        self.serial.connect(self.address)
        self.use_socket = True

    ###### Operazioni di invio e ricezione dal canale
    def flush_in(self, wait_for=0.1):
        """ Vuota il buffer di ricezione"""
        if self.serial in select.select([self.serial], [], [], wait_for)[0]:
            self.recv()
        self.rcv_buf = b''
        self.wait_answ = 0

    def send(self, msg):
        """Invia una richiesta e prepara per la risposta"""
        self.flush_in()
        if self.use_socket:
            self.serial.send(msg)
        else:
            self.serial.write(msg)
        self.wait_answ = 1

    def recv_ready(self):
        """something to receive"""
        return ([], [], []) != select.select([self.serial], [], [], 0.5)

    def recv(self, size=254):
        """receive wrapper"""
        if self.use_socket:
            return self.serial.recv(size)
        else:
            return self.serial.read()

    def sendmsg(self, mod_func):
        """Chiede all'oggetto mod_func, gia inizializzato,
        il messaggio e lo invia"""
        msg = modbus_build_RTU_message(mod_func)
        self.send(msg)
        self.start_chat = time.time()
        return msg

    def recvansw(self, mod_func):
        """Riceve i dati nella quantita massima prevista dall'oggetto MOD_FUNC
        e risponde la risposta decodificata"""
        if self.recv_ready():
            self.rcv_buf += self.recv()
            # expected (slave addr, func_num, byte count) in rcv_buf
            if len(self.rcv_buf) < 3:
                raise EAgain
            self.wait_answ = 2
            (dummy_fc, bc, dummy_s) = mod_func.chkansw(self.rcv_buf[1:])
            # expected (slave addr, func_num, byte count, data, CRC) in rcv_buf
            if len(self.rcv_buf) == (3 + bc + 2):
                crc = crc16(self.rcv_buf[:-2])
                if crc != self.rcv_buf[-2:]:
                    raise EFrame
                self.wait_answ = 3
                self.send_count = 0
                return mod_func.answ(self.rcv_buf[1:-2])
        raise EAgain()

    def chat(self, mod_func):
        """Esegue la sequenza invio, risposta"""
        if self.wait_answ == 3:
            self.wait_answ = 0
        if self.wait_answ == 0:
            self.sendmsg(mod_func)
            self.wait_answ = 1
        return self.recvansw(mod_func)

    def chat_blocking(self, mod_func, timeout=1, retry_max=10):
        """blocking sincronous chat"""
        while True:
            try:
                return self.chat(mod_func)
            except EAgain as exc:
                if (time.time() - self.start_chat) > timeout:
                    self.wait_answ = 1
                    self.send_count += 1
                    if self.send_count > retry_max:
                        raise ETout('modbus_serial.chat_blocking timeout') from exc


class modbus_func(object):
    """Gli oggetti modbus_func preparano la stringa Request PDU
    da inviare al client modbus
    Ricevono la parte Response PDU dal client modbus
    e ne eseguono il parsing"""

    MOD_FUNC = "subclass implementation dependent"

    def __init__(self, transaction_identifier, unit_identifier):
        """Init.
        """
        self.bus_err = None
        self.bytecount = 0
        self.msg = b''
        self.transaction_identifier = transaction_identifier or 0
        self.unit_identifier = unit_identifier or 1

    def chkansw_echo(self, response):
        """Analizza la parte di segnalazione errore del messaggio ricevuto
        per le funzioni che fanno solo echo (func5 e simili)
        Se la risposta non segnala errore restituisce il
        stringa seguente (s[1:])
        Se segnala errore emette eccezione
        Il chiamante garantisce che la stringa contenda almeno
        due byte (func num, primo byte o error code)
        """
        func_code, err_code = struct.unpack('> B B', response[:2])
        if func_code == self.MOD_FUNC:
            self.bus_err = 0
            self.bytecount = 0
            return (func_code, self.bytecount, response[1:])
        self.bus_err = func_code
        raise EFrame(
            f'Slave returned cod error {func_code:x} {err_code:x}')

    def chkansw(self, response):
        """Analizza la parte di segnalazione errore del messaggio ricevuto
        per le funzioni che restituiscono byte_count
        Se la risposta non segnala errore restituisce il
        byte byte_count (s[1]) e la stringa seguente (s[2:])
        Se segnala errore emette eccezione
        Il chiamante garantisce che la stringa contenga almeno
        due byte (func num, byte count)
        """
        function_code, self.bytecount = struct.unpack(
            '> B B', response[:2])
        if function_code == self.MOD_FUNC:
            self.bus_err = 0
            return (function_code, self.bytecount, response[2:])
        self.bus_err = function_code
        raise EFrame(
            f'Slave returned cod error {function_code:x} {self.bytecount}')

    def bytes_left_with_bytecount(self, bytestring):
        """How many bytes are still needed to get the answer.
        Function code with second byte as bytecount
        """
        if len(bytestring) < 2:
            return 2 - len(bytestring)
        _func_code, bytecount, _rest = self.chkansw(bytestring)
        return bytecount + 2 - len(bytestring) # 2 == i byte fc e bytecount

    def bytes_left_5byte_header(self, bytestring):
        """How many bytes are still needed to get the answer.
        Function code followed by "! H H"
        """
        if len(bytestring) < 2:
            return 2 - len(bytestring)
        _func_code, _varius_meaning, _rest = self.chkansw(bytestring)
        return 5 - len(bytestring)


class modbusf3(modbus_func):
    """Chiede il valore di registri"""
    MOD_FUNC = 3
    ANSW_LEN = 255

    def __init__(self, start_reg, num_regs, unit_identifier=None, transaction_identifier=None):
        """Riceve il numero di registro iniziale
        e il numero di registri da leggere"""
        super().__init__(
            unit_identifier=unit_identifier,
            transaction_identifier=transaction_identifier)
        self.start_reg = start_reg
        self.num_regs = num_regs

    def mkmsg(self):
        """build message"""
        self.msg = struct.pack(
            '> B H H', self.MOD_FUNC, self.start_reg, self.num_regs)
        return 0

    def answ(self, s):
        """decode answer"""
        dummy_fc, bc, s = self.chkansw(s)
        return struct.unpack(f'> {bc//2}H', s)

    def bytes_left(self, bytestring):
        """How many bytes are still needed to get the answer.
        """
        return self.bytes_left_with_bytecount(bytestring)

class modbusf4(modbus_func):
    """Chiede il valore di registri di input"""
    MOD_FUNC = 4
    ANSW_LEN = 255

    def __init__(self, start_reg, num_regs, unit_identifier=None, transaction_identifier=None):
        """Riceve il numero di registro iniziale
        e il numero di registri da leggere"""
        super().__init__(
            unit_identifier=unit_identifier,
            transaction_identifier=transaction_identifier)
        self.start_reg = start_reg
        self.num_regs = num_regs

    def mkmsg(self):
        """build message"""
        self.msg = struct.pack(
            '> B H H', self.MOD_FUNC, self.start_reg, self.num_regs)
        return 0

    def answ(self, s):
        """decode answer"""
        dummy_fc, bc, s = self.chkansw(s)
        return struct.unpack(f'> {bc//2}H', s)

    def bytes_left(self, bytestring):
        """How many bytes are still needed to get the answer.
        """
        return self.bytes_left_with_bytecount(bytestring)


class modbusf5(modbus_func):
    """Imposta un bit bit_index nel registro start_reg"""
    MOD_FUNC = 5
    ANSW_LEN = 1024

    def __init__(self, start_reg, bit_index, bit_value,
                unit_identifier=None, transaction_identifier=None):
        super().__init__(
            unit_identifier=unit_identifier,
            transaction_identifier=transaction_identifier)
        self.start_reg = start_reg
        self.bit_index = bit_index
        self.bit_value = 0xFF00 if bit_value else 0x0000

    def mkmsg(self):
        """build message"""
        pack_str = '! B H H'
        coil_number = self.start_reg * 16 + self.bit_index
        self.msg = struct.pack(
            pack_str, self.MOD_FUNC, coil_number, self.bit_value)
        return 0

    def answ(self, answ_buffer):
        """decode answer
        return coil index and modbus F5 encoded bit value"""
        (dummy_func_code, dummy_byte_count, data_string
        ) = self.chkansw_echo(answ_buffer)
        return struct.unpack("! H H", data_string)

    def bytes_left(self, bytestring):
        """How many bytes are still needed to get the answer.
        """
        return self.bytes_left_5byte_header(bytestring)


class modbusf16(modbus_func):
    """Scrive regs_data a partire dal registro start_reg"""
    MOD_FUNC = 16
    ANSW_LEN = 1024

    def __init__(self, start_reg, regs_data, unit_identifier=None, transaction_identifier=None):
        super().__init__(
            unit_identifier=unit_identifier,
            transaction_identifier=transaction_identifier)
        self.start_reg = start_reg
        self.regs_data = regs_data

    def mkmsg(self):
        """build message"""
        num_regs = len(self.regs_data)
        byte_count = num_regs * 2

        pack_str = '! B H H B'
        self.msg = struct.pack(
            pack_str, self.MOD_FUNC, self.start_reg, num_regs, byte_count)
        for i in self.regs_data:
            self.msg = self.msg + struct.pack('! H', i)
        return 0

    def answ(self, s):
        """decode answer"""
        dummy_fc, dummy_bc, dummy_s_rest = self.chkansw(s)
        return struct.unpack('! H H', s[1:])

    def bytes_left(self, bytestring):
        """How many bytes are still needed to get the answer.
        """
        return self.bytes_left_5byte_header(bytestring)


class modbusf23(modbus_func):
    """Scrive regs_data a partire dal registro wstart_reg.
    Legge num_regs a partire da rstart_reg"""
    MOD_FUNC = 23
    ANSW_LEN = 1024

    def __init__(self, rstart_reg, rnum_regs, wstart_reg, regs_data,
                unit_identifier=None, transaction_identifier=None):
        super().__init__(
            unit_identifier=unit_identifier,
            transaction_identifier=transaction_identifier)
        self.rstart_reg = rstart_reg
        self.rnum_regs = rnum_regs
        self.wstart_reg = wstart_reg
        self.regs_data = regs_data

    def mkmsg(self):
        """build message"""
        wnum_regs = len(self.regs_data)
        byte_count = wnum_regs * 2

        # MOD_FUNC B, rstart H, read num_regs H, wstart_reg H,
        # write word-count H, write word-count * 2 B, write regs_data
        self.msg = struct.pack(
            '! B H H H H B',
            self.MOD_FUNC, self.rstart_reg,
            self.rnum_regs, self.wstart_reg,
            wnum_regs, byte_count)
        for ndx in self.regs_data:
            self.msg = self.msg + struct.pack('! H', ndx)

        return 0

    def answ(self, s):
        """decode answer"""
        dummy_fc, bc, s = self.chkansw(s)
        return struct.unpack(f'! {bc}B', s)

    def bytes_left(self, bytestring):
        """How many bytes are still needed to get the answer.
        """
        return self.bytes_left_with_bytecount(bytestring)
