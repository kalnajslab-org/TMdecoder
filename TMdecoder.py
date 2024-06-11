import csv 
import struct
import xmltodict
import sys
import argparse

class TMmsg:
    def __init__(self, msg_file_name:str):
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
        with open(msg_file_name, "rb") as binary_file:
            data = binary_file.read()

        self.data = data
        self.bindata = self.binaryData()
        # All of the decoded data samples. Each record
        # is a dictionary.
        self.records = []
        
    def allSamples(self):
        return self.records

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
    def __init__(self, msg_file_name:str):
        '''
        Initialize the object with the provided binary data.

        Args:
            msg_file_name: The message file name.

        Returns:
            None
        '''
        super().__init__(msg_file_name)
        self.csv_header = 'valid,frame_count,air_temp_degC,humdity_percent,pres_mb,module_error'
        self.records = self.allRS41samples()

    def csvText(self)->list:
        '''
        Generate CSV text lines from the records.

        Returns:
            list: List of CSV text lines.

        Args:
            self: The instance containing records and a CSV header.
        '''

        csv_lines = [self.csv_header]
        for r in self.records:
            csv_line = \
                f"{r['valid']},{r['frame_count']},{r['air_temp_degC']:0.2f},{r['humdity_percent']:0.2f},{r['pres_mb']:0.2f},{r['module_error']}"
            csv_lines.append(csv_line)
        return csv_lines

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

def argParse():
    '''
    Parse command line arguments for the TMdecoder script.

    Returns:
        Parsed command line arguments.

    '''
    parser = argparse.ArgumentParser(
                        prog='TMdecoder',
                        description='Decode a LASP StratoCore TM message and produce CSV',
                        epilog='')
    parser.add_argument('filename', help='TM message file')           
    parser.add_argument('-o', '--outfile', help='Save CSV to a file')
    parser.add_argument('-q', '--quiet',  action='store_true', help='Turn off printing')  # on/off flag
    return parser.parse_args()

if __name__ == "__main__":

    args = argParse()
    print(args)

    rs41_msg = RS41msg(sys.argv[1])
    if not args.quiet:
        rs41_msg.printCsv()
    if args.outfile:
        rs41_msg.saveCsv(args.outfile)

