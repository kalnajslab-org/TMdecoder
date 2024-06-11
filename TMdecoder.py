import csv 
import struct
import xmltodict
import sys

class TMmsg:
    '''Base class for Strateole2 TM message decoding

    See the Zephyr TM specification in:
    ZEPHYR INTERFACES FOR HOSTED INSTRUMENTS
    STR2-ZEPH-DCI-0-031 Version : 1.3
    '''
    def __init__(self, data:bytes):
        self.data = data
        self.bindata = self.binaryData()

    def TMxml(self)->str:
        xml_txt = self.delimitedText(b'<TM>', b'</TM>')
        result = xmltodict.parse(xml_txt)
        return result

    def CRCxml(self)->str:
        xml_txt = self.delimitedText(b'<CRC>', b'</CRC>')
        result = xmltodict.parse(xml_txt)
        return result

    def delimitedText(self, startTxt:str, endTxt:str)->bytes:
        start = self.data.find(startTxt)
        end = self.data.find(endTxt)
        return data[start:end+len(endTxt)].decode()

    def binaryData(self)->bytes:
        '''Return the binary data segment'''
        tm_xml = self.TMxml()
        bin_length = int(tm_xml['TM']['Length'])
        bin_start = self.data.find(b'</CRC>\nSTART') + 12
        bindata = self.data[bin_start:bin_start+bin_length]
        return bindata

class RS41msg(TMmsg):
    '''LOPC RS41 TM message'''
    # RS41 binary segment:
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
        super().__init__(data)

    def decodeRS41sample(self, record)->dict:
        '''Decode one binary sample and convert to real world values'''
        r = dict()
        r['valid'] = struct.unpack_from('B', record, 0)[0]
        r['frame'] = struct.unpack_from('>l', record, 1)[0]
        r['tdry'] = struct.unpack_from('>H', record, 5)[0]/100.0-100.0
        r['humidity'] = struct.unpack_from('>H', record, 7)[0]/100.0
        r['pres'] = struct.unpack_from('>H', record, 9)[0]/100.0
        r['error'] = struct.unpack_from('>H', record, 11)[0]
        #print(f"{valid}, {frame}, {tdry:0.2f}, {humidity:0.2f}, {pres:0.2f}, 0x{error:04x}")
        return r

    def allRS41samples(self)->list:
        '''Go through all data samples and convert to real world values'''
        record_len = 1 + 4 + 2 + 2 + 2 + 2
        records = []
        for i in range(6, len(self.bindata)-6, record_len):
            record = self.bindata[i:i+record_len]
            records.append(self.decodeRS41sample(record))
        return records

    def timeStamp(self)->int:
        time_stamp = struct.unpack_from('>L', self.bindata, 0)[0]
        return time_stamp

if __name__ == "__main__":
    inFile = sys.argv[1]
    with open(inFile, "rb") as binary_file:
        data = binary_file.read()

    rs41_msg = RS41msg(data)

    print(rs41_msg.TMxml())
    print(rs41_msg.CRCxml())

    time_stamp = rs41_msg.timeStamp()
    print(f"timestamp: {time_stamp}")

    records = rs41_msg.allRS41samples()
    print(f"{len(records)} data records in the file")

    for r in records:
        print(r)
