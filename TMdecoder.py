import csv 
import struct
import xmltodict
import sys

class TMmsg:
    def __init__(self, data:bytes):
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
        self.data = data
        self.bindata = self.binaryData()

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

    def delimitedText(self, startTxt:str, endTxt:str)->bytes:
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
        return data[start:end+len(endTxt)].decode()

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
    def __init__(self, data:bytes):
        '''
        Initialize the object with the provided binary data.

        Args:
            data (bytes): The binary data to initialize the object.

        Returns:
            None
        '''
        super().__init__(data)

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
        r['frame'] = struct.unpack_from('>l', record, 1)[0]
        r['tdry'] = struct.unpack_from('>H', record, 5)[0]/100.0-100.0
        r['humidity'] = struct.unpack_from('>H', record, 7)[0]/100.0
        r['pres'] = struct.unpack_from('>H', record, 9)[0]/100.0
        r['error'] = struct.unpack_from('>H', record, 11)[0]
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

if __name__ == "__main__":
    inFile = sys.argv[1]
    with open(inFile, "rb") as binary_file:
        data = binary_file.read()

    rs41_msg = RS41msg(data)

    print(rs41_msg.parse_TM_xml())
    print(rs41_msg.parse_CRC_xml())

    time_stamp = rs41_msg.timeStamp()
    print(f"timestamp: {time_stamp}")

    records = rs41_msg.allRS41samples()
    print(f"{len(records)} data records in the file")

    for r in records:
        print(r)
