"""
https://www.socomec.co.uk/en-gb/reference/48250404
https://www.socomec.co.uk/sites/default/files/2024-03/DIRIS-A-30---MULTI-FUNCTION-METERS_COMMUNICATION-TABLE_2018-01_CMT_EN_0.html
"""

# TODO: porta tutto in unità di misura standard aziendali
# come in ime106.py

# pylint: disable=invalid-name
from pprint import pprint
from mvmodbus2 import modbus_tcp, modbusf3

def U8(val):
    """Adattatore di tipo SOCOMEC. Unsigned int."""
    return int(val[0])

def STRING_16(val):
    """Adattatore di tipo SOCOMEC. Stringa in due word"""
    return STRING_NORM(val)

def U16(val):
    """Adattatore di tipo SOCOMEC. Unsigned int da word"""
    return int(val[0])

def U16_HEX(val):
    """Adattatore di tipo SOCOMEC. Non si capisce. Str di valori hex ?"""
    return f'{val[0] // 256} {val[0] % 256}'

def U64_HEX(val):
    """Adattatore di tipo SOCOMEC. Str di valori hex da 4 word ?"""
    return U16_HEX([val[0]]) + ' ' + U16_HEX([val[1]])\
         + ' ' + U16_HEX([val[2]]) + ' ' + U16_HEX([val[3]])

def value32(val, signed):
    """Ritorna il valore da due word S32 signed o U32 unsigned"""
    return int.from_bytes(
        int.to_bytes(val[0], length=2, byteorder='big') + 
        int.to_bytes(val[1], length=2, byteorder='big'),
        byteorder='big', signed=signed)

def U32(val):
    """Adattatore di tipo SOCOMEC. Unsigned int."""
    return value32(val, signed=False)

def S32(val):
    """Adattatore di tipo SOCOMEC. Signed int."""
    return value32(val, signed=True)

def STRING_NORM(val):
    """Adattatore di tipo SOCOMEC. Stringa"""
    return "".join(
        [c for c in
           "".join([chr(x // 256) + chr(x % 256) for x in val if x != 0])
            if c != "\x00"])

def DATETIME_3(val):
    """Adattatore di tipo SOCOMEC. Data e ora in tre word"""
    year = val[0]
    month = val[1] // 256
    day = val[1] % 256
    hour = val[2] // 256
    minute = val[2] % 256
    return f'{year:04}-{month:02}-{day:02} {hour:02}:{minute:02}'

def decode_datetime_3(registers):
    """
    Decodifica un valore DateTime_3 da tre registri Modbus.
    
    :param registers: Lista di 3 registri Modbus (es. [0x1803, 0x0A14, 0x2D1E])
    :return: Stringa con data e ora formattata
    """
    if len(registers) != 3:
        raise ValueError("Servono esattamente 3 registri per il formato DateTime_3")
    # Converti i registri in una sequenza di 6 byte
    byte_data = [
        (registers[0] >> 8) & 0xFF, registers[0] & 0xFF,  # Anno, Mese
        (registers[1] >> 8) & 0xFF, registers[1] & 0xFF,  # Giorno, Ore
        (registers[2] >> 8) & 0xFF, registers[2] & 0xFF   # Minuti, Secondi
    ]
    # Decodifica i valori
    year = 2000 + byte_data[0]  # Aggiungi 2000 per ottenere l'anno completo
    month = byte_data[1]
    day = byte_data[2]
    hour = byte_data[3]
    minute = byte_data[4]
    second = byte_data[5]
    # Formatta la data e ora
    return f"{year:04d}-{month:02d}-{day:02d} {hour:02d}:{minute:02d}:{second:02d}"


# pylint: enable=invalid-name

UserDB = [
  {
    "pid": "0",
    "pname": "Basic",
    "pwd": ""
  },
  {
    "pid": "1",
    "pname": "Advance",
    "pwd": "SocoAdm"
  },
  {
    "pid": "2",
    "pname": "Expert",
    "pwd": "sOcOmec"
  }
]


# Per adattare il copia incolla dalla tabella internet dei registri usa:
#reg exp        ^(\d+)\t([^\t]+)\t(\d+)\t([^\t]+)\t([^\t]+)\t(.*)$
#sostitusci con          ($1,\t$3,\t'$4',\t'$5',\t$6),

# Dec address,	Words count,	Description,	Unit,	Data type

REGISTRI_PRODUCTID = [
  (50000,	4,	'"SOCO"',	'-',	STRING_16,),
  (50004,	1,	'Product order ID (Countis:100, Protection:200, Atys:300, Diris:400)',	'-',	U16,),
  (50005,	1,	'Product ID (EX: 1000 ATS3)',	'-',	U16,),
  (50006,	1,	'JBUS Table Version (EX: 101 Version 1.01)',	'-',	U16,),
  (50007,	1,	'Product software version (EX: 100 Version 1.00)',	'-',	U16,),
  (50008,	1,	'Serial_AA_SS',	'-',	U16_HEX,),
  (50009,	1,	'Serial_SST_L',	'-',	U16_HEX,),
  (50010,	1,	'Serial_order',	'-',	U16,),
  (50011,	2,	'Serial_Reserve',	'-',	U32,),
  (50013,	4,	'See "Code table" tab for more details',	'-',	U64_HEX,),
  (50017,	1,	'Customization data loaded (True/False)',	'-',	U8,),
  (50018,	1,	'Product version (Major)',	'-',	U16,),
  (50019,	1,	'Product version (Minor)',	'-',	U16,),
  (50020,	1,	'Product version (Revision)',	'-',	U16,),
  (50021,	1,	'Product version (Build)',	'-',	U16,),
#  (50022,	3,	'Product build date',	'-',	DATETIME_3,),
  (50025,	1,	'Software technical base version (Major)',	'-',	U16,),
  (50026,	1,	'Software technical base version (Minor)',	'-',	U16,),
  (50027,	1,	'Software technical base version (Revision)',	'-',	U16,),
  (50028,	1,	'Customization version (Major)',	'-',	U16,),
  (50029,	1,	'Customization version (Minor)',	'-',	U16,),
  (50030,	4,	'Product VLO (EX : "880100")',	'-',	STRING_NORM,),
  (50034,	4,	'Customization VLO (EX : "880700")',	'-',	STRING_NORM,),
  (50038,	4,	'Software technical base VLO (EX : "880600")',	'-',	STRING_NORM,),
  (50042,	8,	'Vendor name (EX : "SOCOMEC")',	'-',	STRING_NORM,),
  (50050,	8,	'Product name (EX : "DIRIS A40R")',	'-',	STRING_NORM,),
  (50058,	8,	'Extended name',	'-',	STRING_NORM),
]

REGISTRI_ORACORRENTE = [
  (57601,	1,	"Month",	'-',	U8),
  (57600,	1,	"Day",	'-',	U8),
  (57602,	1,	"Year",	'-',	U16),
  (57603,	1,	"Hour",	'-',	U8),
  (57604,	1,	"Minute",	'-',	U8),
  (57605,	1,	"Second",	'-',	U8),
]

REGISTRI_MISURE = [
  (50512,	2,	'Hour Meter',	'h / 100',	U32),
  (50514,	2,	'Phase to Phase Voltage: U12',	'V / 100',	U32),
  (50516,	2,	'Phase to Phase Voltage: U23',	'V / 100',	U32),
  (50518,	2,	'Phase to Phase Voltage: U31',	'V / 100',	U32),
  (50520,	2,	'Simple voltage : V1',	'V / 100',	U32),
  (50522,	2,	'Simple voltage : V2',	'V / 100',	U32),
  (50524,	2,	'Simple voltage : V3',	'V / 100',	U32),
  (50526,	2,	'Frequency : F',	'Hz / 100',	U32),
  (50528,	2,	'Current : I1',	'A / 1000',	U32),
  (50530,	2,	'Current : I2',	'A / 1000',	U32),
  (50532,	2,	'Current : I3',	'A / 1000',	U32),
  (50534,	2,	'Neutral Current : In',	'A / 1000',	U32),
  (50536,	2,	'Active Power +/- : P',	'W / 0.1',	S32),
  (50538,	2,	'Reactive Power +/- : Q',	'var / 0.1',	S32),
  (50540,	2,	'Apparent Power : S',	'VA / 0.1',	U32),
  (50542,	2,	'Power Factor : -: leading et + : lagging : PF',	'- / 1000',	S32),
  (50544,	2,	'Active Power phase 1 +/- : P1',	'W / 0.1',	S32),
  (50546,	2,	'Active Power phase 2 +/- : P2',	'W / 0.1',	S32),
  (50548,	2,	'Active Power phase 3 +/- : P3',	'W / 0.1',	S32),
  (50550,	2,	'Reactive Power phase 1 +/- : Q1',	'var / 0.1',	S32),
  (50552,	2,	'Reactive Power phase 2 +/- : Q2',	'var / 0.1',	S32),
  (50554,	2,	'Reactive Power phase 3 +/- : Q3',	'var / 0.1',	S32),
  (50556,	2,	'Apparent Power phase 1 : S1',	'VA / 0.1',	U32),
  (50558,	2,	'Apparent Power phase 2 : S2',	'VA / 0.1',	U32),
  (50560,	2,	'Apparent Power phase 3 : S3',	'VA / 0.1',	U32),
  (50562,	2,	'Power Factor phase 1 -: leading and + : lagging : PF1',	'- / 1000',	S32),
  (50564,	2,	'Power Factor phase 2 -: leading and + : lagging : PF2',	'- / 1000',	S32),
  (50566,	2,	'Power Factor phase 3 -: leading and + : lagging : PF3',	'- / 1000',	S32),
  (50568,	2,	'System value I Sys : ( I1+I2+I3) / 3',	'A / 1000',	U32),
  (50570,	2,	'System value U Sys : (U12 + U23 + U31 ) / 3',	'V / 100',	U32),
  (50572,	2,	'System value V Sys : (V1 + V2 + V3 ) / 3',	'V / 100',	U32),
]

REGISTRI_MISURE_STATISTICA = [ # Il tempo di campionamento di default è di 15 minuti
  (51024,	2,	'Avg U12',	'V / 100',	U32),
  (51026,	2,	'Avg U23',	'V / 100',	U32),
  (51028,	2,	'Avg U31',	'V / 100',	U32),
  (51030,	2,	'Avg V1',	'V / 100',	U32),
  (51032,	2,	'Avg V2',	'V / 100',	U32),
  (51034,	2,	'Avg V3',	'V / 100',	U32),
  (51036,	2,	'Avg F',	'Hz / 100',	U32),
  (51038,	2,	'Avg I1',	'A / 1000',	U32),
  (51040,	2,	'Avg I2',	'A / 1000',	U32),
  (51042,	2,	'Avg I3',	'A / 1000',	U32),
  (51044,	2,	'Avg In',	'A / 1000',	U32),
  (51046,	2,	'Avg P+ (? active power +)',	'W / 0.1',	U32),
  (51048,	2,	'Avg P- (? active power -)',	'W / 0.1',	U32),
  (51050,	2,	'Avg Q+ (? reactive power +)',	'var / 0.1',	U32),
  (51052,	2,	'Avg Q-(? reactive power -)',	'var / 0.1',	U32),
  (51054,	2,	'Avg S (? apparent power)',	'VA / 0.1',	U32),
  (51056,	2,	'Max/avg U12',	'V / 100',	U32),
  (51058,	2,	'Max/avg U23',	'V / 100',	U32),
  (51060,	2,	'Max/avg U31',	'V / 100',	U32),
  (51062,	2,	'Max/avg V1',	'V / 100',	U32),
  (51064,	2,	'Max/avg V2',	'V / 100',	U32),
  (51066,	2,	'Max/avg V3',	'V / 100',	U32),
  (51068,	2,	'Max/avg F',	'Hz / 100',	U32),
  (51070,	2,	'Max/avg I1',	'A / 1000',	U32),
  (51072,	2,	'Max/avg I2',	'A / 1000',	U32),
  (51074,	2,	'Max/avg I3',	'A / 1000',	U32),
  (51076,	2,	'Max/avg In',	'A / 1000',	U32),
  (51078,	2,	'Max/avg P+',	'W / 0.1',	U32),
  (51080,	2,	'Max/avg P-',	'W / 0.1',	U32),
  (51082,	2,	'Max/avg Q+',	'var / 0.1',	U32),
  (51084,	2,	'Max/avg Q-',	'var / 0.1',	U32),
  (51086,	2,	'Max/avg S',	'VA / 0.1',	U32),
]
REGISTRI_ENERGIE = [
  (50768,	2,	'Hour meter',	'h / 100',	U32),
  (50780,	2,	'Partial Positive Active Energy: Ea+',	'Wh / 0.001',	U32),
  (50782,	2,	'Partial Positive Reactive Energy: Er +',	'varh / 0.001',	U32),
  (50784,	2,	'Partial Apparent Energy : Es',	'VAh / 0.001',	U32),
  (50786,	2,	'Partial Negative Active Energy : Ea-',	'Wh / 0.001',	U32),
  (50788,	2,	'Partial Negative Reactive Energy : Er -',	'varh / 0.001',	U32),
  (50790,	2,	'Number of pulse meter ( 10 Maxi )',	'-',	U32),
  (50792,	2,	'Total pulse meter Input 1',	'-',	U32),
  (50794,	2,	'Total pulse meter Input 2',	'-',	U32),
  (50796,	2,	'Total pulse meter Input 3',	'-',	U32),
  (50798,	2,	'Total pulse meter Input 4',	'-',	U32),
  (50800,	2,	'Total pulse meter Input 5',	'-',	U32),
  (50802,	2,	'Total pulse meter Input 6',	'-',	U32),
  (50804,	2,	'Total pulse meter Input 7',	'-',	U32),
  (50806,	2,	'Total pulse meter Input 8',	'-',	U32),
  (50808,	2,	'Total pulse meter Input 9',	'-',	U32),
  (50810,	2,	'Total pulse meter Input 10',	'-',	U32),
  (50812,	2,	'Predictive Active Power',	'W / 0.1',	U32),
  (50814,	2,	'Predictive Reactive Power',	'var / 0.1',	U32),
  (50816,	2,	'Predictive Apparent Power',	'VA / 0.1',	U32),
  (50818,	2,	'Mean positive active power between 2 signals',	'W / 0.1',	U32),
  (50820,	2,	'Mean negative active power between 2 signals',	'W / 0.1',	U32),
  (50822,	2,	'Mean positive reactive power between 2 signals',	'var / 0.1',	U32),
  (50824,	2,	'Mean negative reactive power between 2 signals',	'var / 0.1',	U32),
]

def studio():
    """"Funzione per prove e studio."""
    misure = {
        f'{reg[2]} {reg[3]}': reg[4](
            modbus_tcp("pwrmu.loc.ghiaia.net").chat(
                modbusf3(reg[0], reg[1], unit_identifier=255)
            )
        )
        for reg in REGISTRI_MISURE
    }
    pprint(misure)
    energie = {
        f'{reg[2]} {reg[3]}': reg[4](
            modbus_tcp("pwrmu.loc.ghiaia.net").chat(
                modbusf3(reg[0], reg[1], unit_identifier=255)
            )
        )
        for reg in REGISTRI_ENERGIE
        if  reg[2] in [
            'Partial Positive Active Energy: Ea+',
            'Partial Negative Active Energy : Ea-',
            'Partial Positive Reactive Energy: Er +',]
    } 
    pprint(energie)
    misure_stat = {
        f'{reg[2]} {reg[3]}': reg[4](
            modbus_tcp("pwrmu.loc.ghiaia.net").chat(
                modbusf3(reg[0], reg[1], unit_identifier=255)
            )
        )
        for reg in REGISTRI_MISURE_STATISTICA
    }
    pprint(misure_stat)
    misure = modbus_tcp("pwrmu.loc.ghiaia.net").chat(
              modbusf3(50022, 3, unit_identifier=255))

    return misure
