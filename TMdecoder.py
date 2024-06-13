import struct
import xmltodict
import csv
import io
import sys
import argparse
from datetime import datetime
from datetime import timezone


class TMmsg:
    def __init__(self, msg_filename:str):
        '''
        Base class for Strateole2 TM message decoding

        See the Zephyr TM specification in:
        ZEPHYR INTERFACES FOR HOSTED INSTRUMENTS
        STR2-ZEPH-DCI-0-031 Version : 1.3

        Args:
            data (bytes): The binary data to decode.

        Examples:
            tm_msg = TMmsg(data)
            tm_msg.TMxml()
            tm_msg.CRCxml()
        '''
        with open(msg_filename, "rb") as binary_file:
            data = binary_file.read()

        self.data = data
        self.bindata = self.binaryData()
        # All of the decoded data samples. Each record
        # is a dictionary.
        self.records = []
        
    def parse_TM_xml(self)->str:
        xml_txt = self.delimitedText(b'<TM>', b'</TM>')
        return xmltodict.parse(xml_txt)

    def parse_CRC_xml(self)->str:
        '''
        Parse TM XML data from the binary input.

        Returns:
            str: Parsed XML data.

        Raises:
            KeyError: If the start or end text is not found in the input data.
        '''        
        xml_txt = self.delimitedText(b'<CRC>', b'</CRC>')
        return xmltodict.parse(xml_txt)

    def delimitedText(self, startTxt:str, endTxt:str)->str:
        '''
        Extract and decode text delimited by start and end markers from the binary input.

        Args:
            startTxt (str): The start marker for the delimited text.
            endTxt (str): The end marker for the delimited text.

        Returns:
            bytes: Decoded text between the start and end markers.

        Raises:
            ValueError: If the start or end markers are not found in the input data.
        '''
        start = self.data.find(startTxt)
        end = self.data.find(endTxt)
        return self.data[start:end+len(endTxt)].decode()

    def binaryData(self)->bytes:
        '''
        Extracts and returns a segment of binary data based on markers and lengths from the input data.

        Returns:
            bytes: The extracted binary data segment.

        Raises:
            KeyError: If the 'TM' or 'Length' keys are not found in the parsed XML data.
        '''
        tm_xml = self.parse_TM_xml()
        bin_length = int(tm_xml['TM']['Length'])
        bin_start = self.data.find(b'</CRC>\nSTART') + 12
        return self.data[bin_start:bin_start+bin_length]

class RS41msg(TMmsg):
    # The binary payload for the RS41 contains a couple of
    # metadata fields, followed by multiple data records.
    # The payload is coded as follows:
    # uint32_t start time
    # uint16_t n_samples
    # data records:
    # struct RS41Sample_t {
    #    uint8_t valid;
    #    uint32_t frame;
    #    uint16_t tdry; (tdry+100)*100
    #    uint16_t humidity; (humdity*100)
    #    uint16_t pres; (pres*100)
    #    uint16_t error;
    #};
    def __init__(self, msg_filename:str):
        '''
        Initialize the object with the provided binary data.

        Args:
            msg_filename: The message file name.

        Returns:
            None
        '''
        super().__init__(msg_filename)
        self.records = self.allRS41samples()

    def csvText(self)->list:
        '''
        Generate CSV text lines from the records.

        Returns:
            list: List of CSV text lines.

        Args:
            self: The instance containing records and a CSV header.
        '''
        self.csv_io = io.StringIO()
        csv_writer = csv.writer(self.csv_io, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        
        csv_header = 'valid,frame_count,air_temp_degC,humdity_percent,pres_mb,module_error'.split(',')
        csv_writer.writerow(csv_header)

        for r in self.records:
            csv_line = [r['valid'], r['frame_count'], r['air_temp_degC'], r['humdity_percent'], r['pres_mb'], r['module_error']]
            csv_writer.writerow(csv_line)
        return self.csv_io.getvalue().split('\r\n')

    def printCsv(self):
        '''
        Prints the CSV text lines generated from the records.

        Args:
            self: The instance containing the CSV text lines to print.
            
        Returns:
            None
        '''

        for r in self.csvText():
            print(r)
    
    def saveCsv(self, out_filename:str)->None:
        with open(out_filename, "w") as out_file:
            for r in self.csvText():
                out_file.write(r)
                out_file.write('\n')

    def decodeRS41sample(self, record)->dict:
        '''
        Decode a binary sample and convert it to real-world values.

        Args:
            record: The binary sample to decode.

        Returns:
            dict: Decoded real-world values of the binary sample.
        '''
        r = {}
        r['valid'] = struct.unpack_from('B', record, 0)[0]
        r['frame_count'] = struct.unpack_from('>l', record, 1)[0]
        r['air_temp_degC'] = struct.unpack_from('>H', record, 5)[0]/100.0-100.0
        r['humdity_percent'] = struct.unpack_from('>H', record, 7)[0]/100.0
        r['pres_mb'] = struct.unpack_from('>H', record, 9)[0]/100.0
        r['module_error'] = struct.unpack_from('>H', record, 11)[0]
        #print(f"{valid}, {frame}, {tdry:0.2f}, {humidity:0.2f}, {pres:0.2f}, 0x{error:04x}")
        return r

    def allRS41samples(self)->list:
        '''
        Go through all data samples and convert them to real-world values.

        Returns:
            list: List of dictionaries containing decoded real-world values for each data sample.
        '''
        record_len = 1 + 4 + 2 + 2 + 2 + 2
        records = []
        for i in range(6, len(self.bindata)-6, record_len):
            record = self.bindata[i:i+record_len]
            records.append(self.decodeRS41sample(record))
        return records

    def timeStamp(self)->int:
        '''
        Extract the timestamp from the binary data.

        Returns:
            int: The extracted timestamp value.

        Raises:
            struct.error: If there is an issue with unpacking the timestamp from the binary data.
        '''
        return  struct.unpack_from('>L', self.bindata, 0)[0]

class LPCmsg(TMmsg):
    def __init__(self, msg_filename:str):
        '''
        Initialize the object with the provided binary data.

        Args:
            msg_filename: The message file name.

        Returns:
            None
        '''
        super().__init__(msg_filename)

        #LPC bins - each number is the left end of the bins in nm.   The first bin has minimal sensitivity
        diams = [275,300,325,350,375,400,450,500,550,600,650,700,750,800,900,1000,1200,1400,1600,1800,2000,2500,3000,3500,4000,6000,8000,10000,13000,16000,24000,24000]
        self.bin_header = list(map(str, diams))

        # Initialize some metadata
        self.sn = 'Unknown'
        self.lat = ''
        self.lon= ''
        self.alt = ''

        self.start_time = struct.unpack_from('>I',self.bindata,0)[0] #get the first number which is the start time
        date_time = datetime.fromtimestamp(int(self.start_time),tz=timezone.utc)
        self.end_time = date_time.strftime("%m/%d/%Y, %H:%M:%S")

        tm_xml = self.parse_TM_xml()

        self.instrument = 'Unknown'
        if 'Inst' in tm_xml['TM']:
            self.inst = tm_xml['TM']['Inst']

        if 'StateMess1' in tm_xml['TM']:
            tokens = tm_xml['TM']['StateMess1'].split(',')
            if len(tokens) == 3:
                self.lat = tokens[0]
                self.lon = tokens[1]
                self.alt = tokens[2]
        self.unpackBinary()

    def unpackBinary(self):
        for y in range(int(len(self.bindata)/96 -1)):
            self.HGBins = []
            self.LGBins = []
            self.HKRaw = []
            self.HKData = [0]*16
            indx = 36 + (y+1)*96
        
            for x in range(16):
                self.HGBins.append(struct.unpack_from('>H',self.bindata,indx + x*2)[0])    
                self.LGBins.append(struct.unpack_from('>H',self.bindata,indx + x*2 + 32)[0])
                self.HKRaw.append(struct.unpack_from('>H',self.bindata,indx + x*2 + 64)[0])

            self.HKData[0] = self.HKRaw[0] + self.start_time #elapsed time since the start of the measurement in seconds
            self.HKData[1] = self.HKRaw[1]  # Pump1 Current in mA
            self.HKData[2] = self.HKRaw[2]  # Pump2 Current in mA
            self.HKData[3] = self.HKRaw[3]  # Detector Current in mA
            self.HKData[4] = self.HKRaw[4] / 1000.0 # Detector voltage in V
            self.HKData[5] = self.HKRaw[5] / 1000.0 # PHA Voltage in volts
            self.HKData[6] = self.HKRaw[6] / 1000.0 #Input V in volts
            self.HKData[7] = self.HKRaw[7] / 1000.0 # Flow in SLPM
            self.HKData[8] = self.HKRaw[8] / 1000.0 # Teensy voltage in V
            self.HKData[9] = self.HKRaw[9] # Pump1 PWM drive signal (0 - 1023)
            self.HKData[10] = self.HKRaw[10] # Pump2 PWM drive signal (0 - 1023)
            self.HKData[11] = self.HKRaw[11] / 100.0 - 273.15 # Pump1 T in C
            self.HKData[12] = self.HKRaw[12] / 100.0 - 273.15 # Pump2 T in C
            self.HKData[13] = self.HKRaw[13] / 100.0 - 273.15 # Laser T in C
            self.HKData[14] = self.HKRaw[14] / 100.0 - 273.15 # Board T in C
            self.HKData[15] = self.HKRaw[15] / 100.0 - 273.15 # Inlet T in C

    def csvText(self)->list:
        '''
        Generate CSV text lines from the records.

        Returns:
            list: List of CSV text lines.

        Args:
            self: The instance containing records and a CSV header.
        '''

        self.csv_io = io.StringIO()

        #LPC bins - each number is the left end of the bins in nm.   The first bin has minimal sensitivity
        diams = [275,300,325,350,375,400,450,500,550,600,650,700,750,800,900,1000,1200,1400,1600,1800,2000,2500,3000,3500,4000,6000,8000,10000,13000,16000,24000,24000]
        bin_header = list(map(str,diams))

        csv_writer = csv.writer(self.csv_io, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        
        header1 = ['Instrument:', self.inst, 'Measurerment End Time: ', self.end_time, 
                   'LASP Optical Particle Counter on Strateole 2 Super Pressure Balloons']
        csv_writer.writerow(header1)

        header2 = ['GPS Position at start of Measurement ', 'Latitude: ', self.lat, 'Longitude: ', self.lon, 
                   'Altitude [m]:',self.alt]
        csv_writer.writerow(header2)

        header3 = ['Time', 'Pump1_I','Pump2_I','PHA_I', 'PHA_12V','PHA_3V3','Input_V', 'Flow', 'CPU_V', 
                   'Pump1_PWM', 'Pump2_PWM','Pump1_T', 'Pump2_T', 'Laser_T', 'PCB_T', 'Inlet_T'] + bin_header
        csv_writer.writerow(header3)

        header4 = ['[Unix Time]', '[mA]','[mA]','[mA]','[V]','[V]','[V]', '[SLPM]', '[V]','[#]','[#]', '[C]', '[C]','[C]', '[C]', '[C]'] + ['[diam >nm]']*len(bin_header)
        csv_writer.writerow(header4)

        csv_writer.writerow(self.HKData + self.HGBins + self.LGBins)

        return self.csv_io.getvalue().split('\r\n')

    def printCsv(self):
        '''
        Prints the CSV text lines generated from the records.

        Args:
            self: The instance containing the CSV text lines to print.
            
        Returns:
            None
        '''

        for r in self.csvText():
            print(r)
    
    def saveCsv(self, out_filename:str)->None:
        with open(out_filename, "w") as out_file:
            for r in self.csvText():
                out_file.write(r)
                out_file.write('\n')

def argParse():
    '''
    Parse command line arguments for the TMdecoder script.

    Returns:
        Parsed command line arguments.

    '''
    parser = argparse.ArgumentParser(
                        prog='TMdecoder',
                        description='Decode a LASP StratoCore TM message and produce CSV',
                        epilog='If -l or -r are not specified, try to automatically determine the msg type')
    parser.add_argument('filename', help='TM message file')
    parser.add_argument('-l', '--lpc', action='store_true', help='LPC file')
    parser.add_argument('-r', '--rs41', action='store_true', help='RS41 file')           
    parser.add_argument('-c', '--csv', help='Save CSV to a file')
    parser.add_argument('-q', '--quiet',  action='store_true', help='Turn off printing')  # on/off flag

    args=parser.parse_args()

    if args.lpc & args.rs41:
        print('Only one of -l or -r can be specified')
        parser.print_usage()
        sys.exit(1)

    args.msg_type = None
    if args.lpc:
        args.msg_type = 'lpc'
    if args.rs41:
        args.msg_type = 'rs41'

    return args

def determine_msg_type(filename:str)->str:
    msg_type = 'lpc'

    msg = TMmsg(filename)
    tm = msg.parse_TM_xml()
    if 'StateMess2' in tm['TM']:
        if tm['TM']['StateMess2'] == 'RS41':
            msg_type = 'rs41'

    return msg_type

if __name__ == "__main__":

    args = argParse()

    if not args.msg_type:
        args.msg_type = determine_msg_type(args.filename)

    if args.msg_type == 'lpc':
        msg = LPCmsg(args.filename)
    if args.msg_type == 'rs41':
        msg = RS41msg(args.filename)

    if not args.quiet:
        msg.printCsv()

    if args.csv:
        msg.saveCsv(args.csv)

