# coding=utf-8
"""Protocollo IME analizzatore di rete secondo PR106.pdf
Strumento: Nemo 96 HD
Interfaccia ETHERNET IF96015
"""

import sys
import mvmodbus2
import json

def UD_WORD(val):
    """Unsigned double word"""
    return val[0] * 65536 + val[1]

def U_WORD(val):
    """Unsigned word"""
    return val[0]

def S_WORD(val):
    """Signed word"""
    return val[0] if val[0] < 32768 else val[0] - 65536

def scala_misura(val, div):
    """Scala"""
    return 1.0 * val / div

CONST_SCALA_NOTA3 = 1


def scala_nota3(val):
    """Nota 3:
    val * 0.01 if KTA * KTU < 5000
    else val
    """
    return val * CONST_SCALA_NOTA3

CONST_SCALA_NOTA4 = 1


def scala_nota4(val):
    """vedi nota 4"""
    return val * CONST_SCALA_NOTA4

def scala_nota5(val):
    """vedi nota 5"""
    return [1, -1][val]

REGISTRI_MISURE106 = [
(0x1000, UD_WORD, 'Phase 1 : phase voltage', 'mV', lambda x: x),
(0x1002, UD_WORD, 'Phase 2 : phase voltage', 'mV', lambda x: x),
(0x1004, UD_WORD, 'Phase 3 : phase voltage', 'mV', lambda x: x),
(0x1006, UD_WORD, 'Phase 1 : current', 'mA', lambda x: x),
(0x1008, UD_WORD, 'Phase 2 : current', 'mA', lambda x: x),
(0x100a, UD_WORD, 'Phase 3 : current', 'mA', lambda x: x),
(0x100c, UD_WORD, 'Neutral current', 'mA', lambda x: x),
(0x100e, UD_WORD, 'Chained voltage : L1-L2', 'mV', lambda x: x),
(0x1010, UD_WORD, 'Chained voltage : L2-L3', 'mV', lambda x: x),
(0x1012, UD_WORD, 'Chained voltage : L3-L1', 'mV', lambda x: x),
(0x1014, UD_WORD, '3-phase :active power', ' W (3)', scala_nota3),
(0x1016, UD_WORD, '3-phase :reactive power', ' var (3)', scala_nota3),
(0x1018, UD_WORD, '3-phase :apparent power', ' VA (3)', scala_nota3),
(0x101a, U_WORD, '3-phase : sign of active power', '(5)', scala_nota5),
(0x101b, U_WORD, '3-phase : sign of reactive power', '(5)', scala_nota5),
(0x101c, UD_WORD, '3-phase : positive active energy', 'kWh (4)', scala_nota4),
(0x101e, UD_WORD, '3-phase : positive reactive energy', 'kVarh (4)', scala_nota4),
(0x1020, UD_WORD, '3-phase : negative active energy', 'kWh (4)', scala_nota4),
(0x1022, UD_WORD, '3-phase : negative reactive energy', 'KVarh (4)', scala_nota4),
(0x1024, S_WORD, '3-phase : power factor', '1/100 signed', lambda x: x),
(0x1025, U_WORD, '3-phase : sector of power factor (cap or ind)', '"0 : PF = 1, 1 : ind, 2 : cap"', lambda x: x),
(0x1026, U_WORD, 'Frequency', 'Hz/10', lambda x: x),
(0x1027, UD_WORD, '3-phase : average power', 'W (3)', scala_nota3),
(0x1029, UD_WORD, '3-phase : peak maximum demand', 'W (3)', scala_nota3),
(0x102b, U_WORD, 'Time counter for average power', 'minutes', lambda x: x),
(0x102c, UD_WORD, 'Phase 1 :active power', ' W (3)', scala_nota3),
(0x102e, UD_WORD, 'Phase 2 :active power', ' W (3)', scala_nota3),
(0x1030, UD_WORD, 'Phase 3 :active power', ' W (3)', scala_nota3),
(0x1032, U_WORD, 'Phase 1 : sign of active power', '(5)', scala_nota5),
(0x1033, U_WORD, 'Phase 2 : sign of active power', '(5)', scala_nota5),
(0x1034, U_WORD, 'Phase 3 : sign of active power', '(5)', scala_nota5),
(0x1035, UD_WORD, 'Phase 1 :reactive power', ' var (3)', scala_nota3),
(0x1037, UD_WORD, 'Phase 2 :reactive power', ' var (3)', scala_nota3),
(0x1039, UD_WORD, 'Phase 3 :reactive power', ' var (3)', scala_nota3),
(0x103b, U_WORD, 'Phase 1 : sign of reactive power', '(5)', scala_nota5),
(0x103c, U_WORD, 'Phase 2 : sign of reactive power', '(5)', scala_nota5),
(0x103d, U_WORD, 'Phase 3 : sign of reactive power', '(5)', scala_nota5),
(0x103e, UD_WORD, 'Phase 1 :apparent power', ' VA (3)', scala_nota3),
(0x1040, UD_WORD, 'Phase 2 :apparent power', ' VA (3)', scala_nota3),
(0x1042, UD_WORD, 'Phase 3 :apparent power', ' VA (3)', scala_nota3),
(0x1044, S_WORD, 'Phase 1 : power factor', '1/100 signed', lambda x: x),
(0x1045, S_WORD, 'Phase 2 : power factor', '1/100 signed', lambda x: x),
(0x1046, S_WORD, 'Phase 3 : power factor', '1/100 signed', lambda x: x),
(0x1047, U_WORD, 'Phase 1 : power factor sector', '"0 : PF = 1, 1 : ind, 2 : cap"', lambda x: x),
(0x1048, U_WORD, 'Phase 2 : power factor sector', '"0 : PF = 1, 1 : ind, 2 : cap"', lambda x: x),
(0x1049, U_WORD, 'Phase 3 : power factor sector', '"0 : PF = 1, 1 : ind, 2 : cap"', lambda x: x),
(0x104a, U_WORD, 'Phase 1 : THD V1', '1/10 %', lambda x: x),
(0x104b, U_WORD, 'Phase 2 : THD V2', '1/10 %', lambda x: x),
(0x104c, U_WORD, 'Phase 3 : THD V3', '1/10 %', lambda x: x),
(0x104d, U_WORD, 'Phase 1 : THD I1', '1/10 %', lambda x: x),
(0x104e, U_WORD, 'Phase 2 : THD I2', '1/10 %', lambda x: x),
(0x104f, U_WORD, 'Phase 3 : THD I3', '1/10 %', lambda x: x),
(0x1050, UD_WORD, 'Phase 1 : I1 average', 'mA', lambda x: x),
(0x1052, UD_WORD, 'Phase 2 : I2 average', 'mA', lambda x: x),
(0x1054, UD_WORD, 'Phase 3 : I3 average', 'mA', lambda x: x),
(0x1056, UD_WORD, 'Phase 1 : I1 peak maximum', 'mA', lambda x: x),
(0x1058, UD_WORD, 'Phase 2 : I2 peak maximum', 'mA', lambda x: x),
(0x105a, UD_WORD, 'Phase 3 : I3 peak maximum', 'mA', lambda x: x),
(0x105c, UD_WORD, '(I1+I2+I3)/3', 'mA', lambda x: x),
(0x105e, UD_WORD, 'Phase 1 : V1 min', 'mV', lambda x: x),
(0x1060, UD_WORD, 'Phase 2 : V2 min', 'mV', lambda x: x),
(0x1062, UD_WORD, 'Phase 3 : V3 min', 'mV', lambda x: x),
(0x1064, UD_WORD, 'Phase 1 : V1 max', 'mV', lambda x: x),
(0x1066, UD_WORD, 'Phase 2 : V2 max', 'mV', lambda x: x),
(0x1068, UD_WORD, 'Phase 3 : V3 max', 'mV', lambda x: x),
(0x106a, UD_WORD, '3-phase : active partial energy', 'kWh (4)', scala_nota4),
(0x106c, UD_WORD, '3-phase : reactive partial energy', 'kVarh (4)', scala_nota4),
(0x106e, U_WORD, 'Operating timer counter', 'H', lambda x: x),
(0x106f, U_WORD, 'Output relay status', '(2)', lambda x: x),
(0x1070, UD_WORD, '3-phase :active average power', ' W (3)', scala_nota3),
(0x1072, UD_WORD, '3-phase :reactive average power', ' var (3)', scala_nota3),
(0x1074, UD_WORD, '3-phase :apparent average power', ' VA (3)', scala_nota3),
(0x1076, UD_WORD, '3-phase :active PMD power', ' W (3)', scala_nota3),
(0x1078, UD_WORD, '3-phase :reactive PMD power', ' var (3)', scala_nota3),
(0x107a, UD_WORD, '3-phase :apparent PMD power', ' VA (3)', scala_nota3),

(0x1200, U_WORD, 'Current transformer ratio (KTA)', 'integer', lambda x: x),
(0x1201, U_WORD, 'Voltage transformer ratio (KTV)', '1/10 tenths e.g. KTV = 5 Reading = 50', lambda x: x/10.0),
(0x1202, UD_WORD, 'Device configuration', '(1)', lambda x: x),
(0x1204, U_WORD, 'Device identifier', '0x10', lambda x: x),
(0x1205, U_WORD, 'Voltages sequence diagnostic', '"1 : OK, 2 : error"', lambda x: x),
(0x1206, U_WORD, 'RFU', '', lambda x: x),
(0x1207, U_WORD, 'Voltage transformer ratio (KTV) 1/100', '1/100', lambda x: x/100.0),
]

REGISTRI_MISURE106_map = {
    reg[2]: dict(zip(('address', 'convert', 'name', 'unit', 'rescale'), reg))
        for reg in REGISTRI_MISURE106
}

def get_regs(slave, regs_list):
    """Get regs regs_list (part of REGISTRI_MISURE106) from slave_addr"""
    regs = {
        reg[2]: # denominazione registro
            reg[4]( # riscala
                reg[1]( # converti
                    slave.chat( # leggi
                        mvmodbus2.modbusf3( # funzione modbus 3
                            reg[0], 1 if reg[1] in (U_WORD, S_WORD) else 2,
                            unit_identifier=255)
                    )
                )
            )
        for reg in REGISTRI_MISURE106
        if reg[2] in regs_list
    }
    return regs


def get_k(slave):
    """Restituisce {KTV, KTA}"""
    tvta = get_regs(slave, ['Current transformer ratio (KTA)', 'Voltage transformer ratio (KTV)'])
    tvta['Voltage transformer ratio (KTV)']
    tvta['k'] = tvta['Voltage transformer ratio (KTV)'] * tvta['Current transformer ratio (KTA)']
    return tvta


def set_scala_nota3_4(slave):
    """Determina la scalatura delle misure"""
    global CONST_SCALA_NOTA3
    global CONST_SCALA_NOTA4
    tvta = get_k(slave)
    k = tvta['k']
    if k < 5000:
        CONST_SCALA_NOTA3 = 0.01
    
    # Nota 4
    # Esprimo tutto in kilo
    # Nella nota yy sono i decimali a display
    # moltiplico il valore di protocollo che è
    # per avere gli zeri mancanti a destra dopo yy
    if k < 10:  # il protocollo risponde in decine di W
        mult = 10 / 1000.0
    else:
        if k < 100:  # centinaia di W
            mult = 100 / 1000.0
        elif k < 1000:  # il protocollo risponde in kW
            mult = 1
        elif k < 10000:  # il protocollo risponde in decine di kW
            mult = 10
        elif k < 100000:  # centinaia di kW
            mult = 100
        else:  # migliaia di kW
            mult = 1000
    CONST_SCALA_NOTA4 = mult
    return tvta

def main_test():
    """Test"""
    slave_addr = 'pwrbl2.loc.ghiaia.net'
    slave = mvmodbus2.modbus_tcp(slave_addr)
    tvta = set_scala_nota3_4(slave)
    print(json.dumps(tvta, indent=2))
    regs = get_regs(slave, [reg[2] for reg in REGISTRI_MISURE106])
    print(json.dumps(regs, indent=2))
    print(json.dumps(
        {reg: regs[reg] for reg in regs if 'energ' in reg},
        indent=2))
    print(json.dumps(
        {reg + REGISTRI_MISURE106_map[reg]['unit'] : regs[reg] for reg in regs if 'power' in reg},
        indent=2))
    return regs

if __name__ == '__main__':
    main_test()


