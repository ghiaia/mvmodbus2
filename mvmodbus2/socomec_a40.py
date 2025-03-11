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

def S16(val):
    """Adattatore di tipo SOCOMEC. Signed int da word"""
    return int.from_bytes(
        int.to_bytes(val[0], length=2, byteorder='big'),
        byteorder='big', signed=True)

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

def DATETIME_3(registers):
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
    (50022,	3,	'Product build date',	'-',	DATETIME_3,),
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

REGISTRI_METROLOGIA_BASSA_PRECISIONE = [
    (51280,	1,	'Hour Meter',	'h / 100',	U16),
    (51281,	1,	'Phase to Phase Voltage: U12',	'V / 100',	U16),
    (51282,	1,	'Phase to Phase Voltage: U23',	'V / 100',	U16),
    (51283,	1,	'Phase to Phase Voltage: U31',	'V / 100',	U16),
    (51284,	1,	'Simple voltage : V1',	'V / 100',	U16),
    (51285,	1,	'Simple voltage : V2',	'V / 100',	U16),
    (51286,	1,	'Simple voltage : V3',	'V / 100',	U16),
    (51287,	1,	'Frequency : F',	'Hz / 100',	U16),
    (51288,	1,	'Current : I1',	'A / 1000',	U16),
    (51289,	1,	'Current : I2',	'A / 1000',	U16),
    (51290,	1,	'Current : I3',	'A / 1000',	U16),
    (51291,	1,	'Neutral Current : In',	'A / 1000',	U16),
    (51292,	1,	'? active Power +/- : P',	'W / 0.1',	S16),
    (51293,	1,	'? reactive Power +/- : Q',	'var / 0.1',	S16),
    (51294,	1,	'? apparent power : S',	'VA / 0.1',	U16),
    (51295,	1,	'? power factor : -: leading and + : lagging : PF',	'- / 1000',	S16),
    (51296,	1,	'Active Power phase 1 +/- : P1',	'W / 0.1',	S16),
    (51297,	1,	'Active Power phase 2 +/- : P2',	'W / 0.1',	S16),
    (51298,	1,	'Active Power phase 3 +/- : P3',	'W / 0.1',	S16),
    (51299,	1,	'Reactive Power phase 1 +/- : Q1',	'var / 0.1',	S16),
    (51300,	1,	'Reactive Power phase 2 +/- : Q2',	'var / 0.1',	S16),
    (51301,	1,	'Reactive Power phase 3 +/- : Q3',	'var / 0.1',	S16),
    (51302,	1,	'Apparent power phase 1 : S1',	'VA / 0.1',	U16),
    (51303,	1,	'Apparent power phase 2 : S2',	'VA / 0.1',	U16),
    (51304,	1,	'Apparent power phase 3 : S3',	'VA / 0.1',	U16),
    (51305,	1,	'Power Factor phase 1 -: leading and + : lagging : PF1',	'- / 1000',	S16),
    (51306,	1,	'Power Factor phase 2 -: leading and + : lagging : PF2',	'- / 1000',	S16),
    (51307,	1,	'Power Factor phase 3 -: leading and + : lagging : PF3',	'- / 1000',	S16),
    (51308,	1,	'System value I Sys : ( I1+I2+I3) / 3',	'A / 1000',	U16),
    (51309,	1,	'System value U Sys : (U12 + U23 + U31 ) / 3',	'V / 10',	U16),
    (51310,	1,	'System value V Sys : (V1 + V2 + V3 ) / 3',	'V / 10',	U16),
    (51311,	1,	'Total Positive Active Energy (no resetable) : Ea+',	'Wh / 1E-06',	U16),
    (51312,	1,	'Total Negative Active Energy (no resetable) : Ea-',	'varh / 1E-06',	U16),
    (51313,	1,	'Total Positive Reactive Energy (no resetable) : Er+',	'Wh / 1E-06',	U16),
    (51314,	1,	'Total Negative Reactive Energy (no resetable) : Er -',	'varh / 1E-06',	U16),
]

REGISTRI_MISURE_PRECISIONE = [
    (768,	2,	'Phase 1 Current',	'A / 1000',	U32),
    (770,	2,	'Phase 2 Current',	'A / 1000',	U32),
    (772,	2,	'Phase 3 Current',	'A / 1000',	U32),
    (774,	2,	'Neutral Current',	'A / 1000',	U32),
    (776,	2,	'Phase to Phase Voltage: U12',	'V / 100',	U32),
    (778,	2,	'Phase to Phase Voltage: U23',	'V / 100',	U32),
    (780,	2,	'Phase to Phase Voltage: U31',	'V / 100',	U32),
    (782,	2,	'Phase to Neutral voltage phase 1',	'V / 100',	U32),
    (784,	2,	'Phase to Neutral voltage phase 2',	'V / 100',	U32),
    (786,	2,	'Phase to Neutral voltage phase 3',	'V / 100',	U32),
    (788,	2,	'Frequency',	'Hz / 100',	U32),
    (790,	2,	'? active power +/- : P',	'W / 0.1',	S32),
    (792,	2,	'? reactive power +/- : Q',	'var / 0.1',	S32),
    (794,	2,	'? apparent power : S',	'VA / 0.1',	U32),
    (796,	2,	'? power factor : -: leadiing et + : lagging : PF',	'- / 1000',	S32),
    (798,	2,	'Active Power phase1 +/-',	'W / 0.1',	S32),
    (800,	2,	'Active Power phase2 +/-',	'W / 0.1',	S32),
    (802,	2,	'Active Power phase3 +/-',	'W / 0.1',	S32),
    (804,	2,	'Reactive Power phase1 +/-',	'var / 0.1',	S32),
    (806,	2,	'Reactive Power phase2 +/-',	'var / 0.1',	S32),
    (808,	2,	'Reactive Power phase3 +/-',	'var / 0.1',	S32),
    (810,	2,	'Apparent Power phase1',	'VA / 0.1',	U32),
    (812,	2,	'Apparent Power phase2',	'VA / 0.1',	U32),
    (814,	2,	'Apparent Power phase3',	'VA / 0.1',	U32),
    (816,	2,	'Power factor phase 1 -:leading and +: lagging',	'- / 1000',	S32),
    (818,	2,	'Power factor phase 2 -:leading and +: lagging',	'- / 1000',	S32),
    (820,	2,	'Power factor phase 3 -:leading and +: lagging',	'- / 1000',	S32),
    (822,	2,	'avg I1',	'A / 1000',	U32),
    (824,	2,	'avg I2',	'A / 1000',	U32),
    (826,	2,	'avg I3',	'A / 1000',	U32),
    (828,	2,	'avg ?active power +',	'W / 0.1',	U32),
    (830,	2,	'avg ?active power -',	'W / 0.1',	U32),
    (832,	2,	'avg ?reactive power +',	'var / 0.1',	U32),
    (834,	2,	'avg ?reactive power -',	'var / 0.1',	U32),
    (836,	2,	'avg ? apparent power',	'VA / 0.1',	U32),
    (838,	2,	'max/avg I1',	'A / 1000',	U32),
    (840,	2,	'max/avg I2',	'A / 1000',	U32),
    (842,	2,	'max/avg I3',	'A / 1000',	U32),
    (844,	2,	'max/avg ?active power +',	'W / 0.1',	U32),
    (846,	2,	'max/avg ?active power -',	'W / 0.1',	U32),
    (848,	2,	'max/avg ?reactive power +',	'var / 0.1',	U32),
    (850,	2,	'max/avg ?reactive power -',	'var / 0.1',	U32),
    (852,	2,	'max/avg ? apparent power',	'VA / 0.1',	U32),
    (854,	2,	'Hour meter',	'h / 100',	U32),
    (856,	2,	'Active Energy +',	'Wh / 0.001',	U32),
    (858,	2,	'Reactive Energy +',	'varh / 0.001',	U32),
    (860,	2,	'Apparent Energy',	'VAh / 0.001',	U32),
    (862,	2,	'Active Energy -',	'Wh / 0.001',	U32),
    (864,	2,	'Reactive Energy -',	'varh / 0.001',	U32),
    (866,	2,	'Input pulse meter 1',	'-',	U32),
    (868,	2,	'Input pulse meter 2',	'-',	U32),
    (870,	2,	'Number of input pulse meters',	'-',	U32),
    (872,	2,	'Alarm in progress (Timer finished) - bit field: bit 1: Ibit 2: Inbit 3: Ubit 4: Vbit 5: ?P+bit 6: ?Q+ bit 7: ?S bit 8: F bit 9: ?PF (L)bit 10: Timebit 11: THD I bit 12: THD Inbit 13: THD Ubit 14: THD Vbit 15: ?P-bit 16: ?Q-bit 17: ?PF (C)bit 18: T?C 1bit 19: T?C 2bit 20: T?C 3bit 21: T?C 4bit 22: P Predictedbit 23: Q predictedbit 24: S Predicted',	'-',	U32),
    (874,	2,	'Alarm detected (Timer in progress) - bit field: bit 1: Ibit 2: Inbit 3: Ubit 4: Vbit 5: ?P+bit 6: ?Q+ bit 7: ?S bit 8: F bit 9: ?PF (L)bit 10: Timebit 11: THD I bit 12: THD Inbit 13: THD Ubit 14: THD Vbit 15: ?P-bit 16: ?Q-bit 17: ?PF (C)bit 18: T?C 1bit 19: T?C 2bit 20: T?C 3bit 21: T?C 4bit 22: P Predictedbit 23: Q predictedbit 24: S Predicted',	'-',	U32),
    (876,	2,	'Number of inputs-outputs : Low_order: number of inputs : High-order: number of outputs',	'-',	U32),
    (878,	2,	'Status of inputs-outputsbit 0 : status input 1 (0 : open, 1 : closed) bit 1 : status input 2 (0 : open, 1 : closed) bit 2 : status input 3 (0 : open, 1 : closed) bit 3 : status input 4 (0 : open, 1 : closed) bit 4 : status input 5 (0 : open, 1 : closed) bit 5 : status input 6 (0 : open, 1 : closed) bit 16 : statuis output 1 (0 : open, 1 : closed) bit 17 : statuis output 2 (0 : open, 1 : closed) bit 18 : statuis output 3 (0 : open, 1 : closed) bit 19 : statuis output 4 (0 : open, 1 : closed) bit 20 : statuis output 5 (0 : open, 1 : closed) bit 21 : statuis output 6 (0 : open, 1 : closed)',	'-',	U32),
    (880,	2,	'System value for current',	'A / 1000',	U32),
    (882,	2,	'System value for phase to phase voltage',	'V / 100',	U32),
    (884,	2,	'System value for phase to neutral voltage',	'V / 100',	U32),
    (886,	2,	'avg U12',	'V / 100',	U32),
    (888,	2,	'avg U23',	'V / 100',	U32),
    (890,	2,	'avg U31',	'V / 100',	U32),
    (892,	2,	'avg V1',	'V / 100',	U32),
    (894,	2,	'avg V2',	'V / 100',	U32),
    (896,	2,	'avg V3',	'V / 100',	U32),
    (898,	2,	'avg F',	'Hz / 100',	U32),
    (900,	2,	'max/avg U12',	'V / 100',	U32),
    (902,	2,	'max/avg U23',	'V / 100',	U32),
    (904,	2,	'max/avg U31',	'V / 100',	U32),
    (906,	2,	'max/avg V1',	'V / 100',	U32),
    (908,	2,	'max/avg V2',	'V / 100',	U32),
    (910,	2,	'max/avg V3',	'V / 100',	U32),
    (912,	2,	'max/avg F',	'Hz / 100',	U32),
    (914,	2,	'avg In',	'A / 1000',	U32),
    (916,	2,	'max/avg In',	'A / 1000',	U32),
    (918,	2,	'Mean positive active power between 2 signals',	'W / 0.1',	U32),
    (920,	2,	'Mean negative active power between 2 signals',	'W / 0.1',	U32),
    (922,	2,	'Mean positive reactive power between 2 signals',	'var / 0.1',	U32),
    (924,	2,	'Mean negative reactive power between 2 signals',	'var / 0.1',	U32),
    (926,	2,	'Predictive total active power',	'W / 0.1',	U32),
    (928,	2,	'Predictive total Reactive power',	'var / 0.1',	U32),
    (930,	2,	'Predictive total Apparent power',	'VA / 0.1',	U32),
]

def get_regs(slave, regs_list, REGISTRI=None):
    """Get regs regs_list (part of REGISTRI) from slave_addr"""
    if REGISTRI is None:
        REGISTRI = REGISTRI_MISURE_PRECISIONE
    regs = {
        reg[2]: # denominazione registro
            reg[4]( # converti
                slave.chat( # leggi
                    modbusf3( # funzione modbus 3
                        reg[0], reg[1],
                        unit_identifier=255)
                )
            )
        for reg in REGISTRI
        if reg[2] in regs_list
    }
    return regs

def get_energia_consumata(slave):
    """Get energia regs from slave_addr"""
    regs = get_regs(slave, [
            'Active Energy +',
        ])
    return regs['Active Energy +']

def get_energia_prodotta(slave):
    """Get energia regs from slave_addr kWh"""
    regs = get_regs(slave, [
            'Active Energy -',
        ])
    return regs['Active Energy -']


def studio():
    """"Funzione per prove e studio."""
    slave = modbus_tcp("pwrmu.loc.ghiaia.net")
    misure = get_regs(slave, [reg[2] for reg in REGISTRI_MISURE], REGISTRI_MISURE)
    pprint(misure)

    energie = get_regs(
            slave,
            [
                'Partial Positive Active Energy: Ea+',
                'Partial Negative Active Energy : Ea-',
                'Partial Positive Reactive Energy: Er +',],
            REGISTRI_ENERGIE)
    pprint(energie)

    misure_stat = get_regs(
                        slave,
                        [reg[2] for reg in REGISTRI_MISURE_STATISTICA],
                        REGISTRI_MISURE_STATISTICA)
    pprint(misure_stat)

    misure_metro = get_regs(slave, [reg[2] for reg in REGISTRI_METROLOGIA_BASSA_PRECISIONE],
                            REGISTRI_METROLOGIA_BASSA_PRECISIONE)
    pprint(misure_metro)

    potenze = get_regs(slave, [
        '? active power +/- : P'
    ])
    pprint(potenze['? active power +/- : P'] * 10) # in W
    
    return misure
