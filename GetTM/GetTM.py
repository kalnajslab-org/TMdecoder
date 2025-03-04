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
    'u8'   # switch_mA (8 bits)
    'u1'   # gps_valid (1 bit)
    's32'  # gps_lat (32 bits)
    's32'  # gps_lon (32 bits)
    'u16'  # gps_alt (16 bits)
    'u5'   # gps_sats (5 bits)
    'u17'  # gps_date (17 bits)
    'u25'  # gps_time (25 bits)
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
    'rev', 
    'heat_on', 
    'v5', 
    'v12', 
    'v56', 
    'board_t', 
    'switch_mA', 
    'gps_valid', 
    'gps_lat', 
    'gps_lon', 
    'gps_alt', 
    'gps_sats', 
    'gps_date', 
    'gps_time', 
    'gps_age_secs', 
    'rs41_valid', 
    'rs41_airt', 
    'rs41_hum', 
    'rs41_hst', 
    'rs41_pres', 
    'rs41_pcb_h', 
    'tsen_airt', 
    'tsen_ptemp', 
    'tsen_pres'
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
        
        record_num = 0
        offset = 4
        while offset < len(data_bytes):
            if offset+rec_size > len(data_bytes):
                # We've reached the terminating bytes at the end of the file
                break
            data_record = data_bytes[offset:offset+rec_size]
        
            # Unpack the unscaled parameters for the first record
            vars = unpack_dict(format_string, variable_names, data_record)

            # Scale them
            scaled_vars = {}
            scaled_vars['rev'] = vars['rev']
            scaled_vars['heat_on'] = bool(vars['heat_on'])
            scaled_vars['v5'] = vars['v5']/100.0
            scaled_vars['v12'] = vars['v12']/100.0
            scaled_vars['v56'] = vars['v56']/100.0
            scaled_vars['board_t'] = vars['board_t']/10.0-100.0
            scaled_vars['switch_mA'] = vars['switch_mA']
            scaled_vars['gps_valid'] = bool(vars['gps_valid'])
            scaled_vars['gps_lat'] = vars['gps_lat']*1.0e-6
            scaled_vars['gps_lon'] = vars['gps_lon']*1.0e-6
            scaled_vars['gps_alt'] = vars['gps_alt']*1.0
            scaled_vars['gps_sats'] = vars['gps_sats']
            scaled_vars['gps_date'] = vars['gps_date']
            scaled_vars['gps_time'] = vars['gps_time']
            scaled_vars['gps_age_secs'] = vars['gps_age_secs']
            scaled_vars['rs41_valid'] = bool(vars['rs41_valid'])
            scaled_vars['rs41_airt'] = vars['rs41_airt']/100.0-100.0
            scaled_vars['rs41_hum'] = vars['rs41_hum']/100.0
            scaled_vars['rs41_hst'] = vars['rs41_hst']
            scaled_vars['rs41_pres'] = vars['rs41_pres']/100.0
            scaled_vars['rs41_pcb_h'] = bool(vars['rs41_pcb_h'])
            scaled_vars['tsen_airt'] = vars['tsen_airt']
            scaled_vars['tsen_ptemp'] = vars['tsen_ptemp']
            scaled_vars['tsen_pres'] = vars['tsen_pres']

            print(f'----- Record {record_num}:')
            record_num += 1
            for key, value in scaled_vars.items():
                if key in ['tsen_airt', 'tsen_ptemp', 'tsen_pres']:
                    print(f'{key}: 0x{value:06x}')
                elif key in ['gps_date']:
                    print(f'{key}:   {value:06d}')
                elif key in ['gps_time']:
                    print(f'{key}: {value:08d}')
                else:
                    print(f'{key}: {value}')
            offset += rec_size

