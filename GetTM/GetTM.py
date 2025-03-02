#
#
# 
from bitstruct import *

# Define the format string for the bitstruct
format_string = (
    '>'    # little-endian
    'u4'   # rev (4 bits)
    'u1'   # heat_on (1 bit)
    'u9'   # v5 (9 bits)
    'u11'  # v12 (11 bits)
    'u13'  # v56 (13 bits)
    'u11'  # board_t (11 bits)
    'u1'   # gps_valid (1 bit)
    's32'  # gps_lat (32 bits)
    's32'  # gps_lon (32 bits)
    'u16'  # gps_alt (16 bits)
    'u5'   # gps_sats (5 bits)
    'u8'   # gps_hdop (8 bits)
    'u8'   # gps_age_secs (8 bits)
    'u1'   # rs41_valid (1 bit)
    'u14'  # rs41_airt (14 bits)
    'u10'  # rs41_hum (10 bits)
    'u8'   # rs41_hst (8 bits)
    'u17'  # rs41_pres (17 bits)
    'u1'   # rs41_pcb_h (1 bit)
    'u12'  # tsen_airt (12 bits)
    'u24'  # tsen_ptemp (24 bits)
    'u24'  # tsen_pres (24 bits)
)

variable_names = [
    'rev', 'heat_on', 'v5', 'v12', 'v56', 'board_t', 'gps_valid', 
    'gps_lat', 'gps_lon', 'gps_alt', 'gps_sats', 'gps_hdop', 
    'gps_age_secs', 'rs41_valid', 'rs41_airt', 'rs41_hum', 
    'rs41_hst', 'rs41_pres', 'rs41_pcb_h', 'tsen_airt', 
    'tsen_ptemp', 'tsen_pres'
    ]

if __name__ == "__main__":
    # Open the file
    with open("TM.dat", "rb") as f:
        all_bytes = f.read()
        print('TM size:', len(all_bytes))
        start = all_bytes.find(b"START")
        print('TM binary start:', start)
        data_bytes = all_bytes[start+5:]
        f='>u16u16'
        n_recs, rec_size = unpack(f, data_bytes)
        print('TM n_recs:', n_recs)
        print('TM rec_size:', rec_size)
        print()
        
        data_record = data_bytes[4:]
    
        # Unpack the first record
        unpacked_data = unpack(format_string, data_record)
        # print(unpacked_data)

        # Scale the data
        rev = unpacked_data[0]
        heat_on = bool(unpacked_data[1])
        v5 = unpacked_data[2]/100.0
        v12 = unpacked_data[3]/100.0
        v56 = unpacked_data[4]/100.0
        board_t = unpacked_data[5]/10.0-100.0
        gps_valid = bool(unpacked_data[6])
        gps_lat = unpacked_data[7]*1.0e-6
        gps_lon = unpacked_data[8]*1.0e-6
        gps_alt = unpacked_data[9]*1.0
        gps_sats = unpacked_data[10]
        gps_hdop = unpacked_data[11]
        gps_age_secs = unpacked_data[12]
        rs41_valid = bool(unpacked_data[13])
        rs41_airt = unpacked_data[14]/100.0-100.0
        rs41_hum = unpacked_data[15]/100.0
        rs41_hst = unpacked_data[16]
        rs41_pres = unpacked_data[17]/100.0
        rs41_pcb_h = bool(unpacked_data[18])
        tsen_airt = unpacked_data[19]
        tsen_ptemp = unpacked_data[20]
        tsen_pres = unpacked_data[21]


        # Print the scaled data
        print('rev:', rev)
        print('heat_on:', heat_on)
        print('v5:', v5)
        print('v12:', v12)
        print('v56:', v56)
        print('board_t:', board_t)
        print('gps_valid:', gps_valid)
        print('gps_lat:', gps_lat)
        print('gps_lon:', gps_lon)
        print('gps_alt:', gps_alt)
        print('gps_sats:', gps_sats)
        print('gps_hdop:', gps_hdop)
        print('gps_age_secs:', gps_age_secs)
        print('rs41_valid:', rs41_valid)
        print('rs41_airt:', rs41_airt)
        print('rs41_hum:', rs41_hum)
        print('rs41_hst:', rs41_hst)
        print('rs41_pres:', rs41_pres)
        print('rs41_pcb_h:', rs41_pcb_h)
        print('tsen_airt:', f'0x{tsen_airt:03x}')
        print('tsen_ptemp:', f'0x{tsen_ptemp:06x}')
        print('tsen_pres:', f'0x{tsen_pres:06x}')
        print()

        var_dict = unpack_dict(format_string, variable_names, data_record)
        print(var_dict)
