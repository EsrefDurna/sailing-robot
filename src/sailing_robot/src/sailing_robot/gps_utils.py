import os
import struct
import sys
from pynmea2 import NMEASentence

if sys.version_info[0] >= 3:
    def iter_ints(b):
        return b
else:
    def iter_ints(b):
        for c in b:
            yield ord(c)

class UBXMessage(object):
    def __init__(self, msg_id, payload):
        self.msg_id = msg_id
        self.payload = payload

    def serialise(self):
        msg_body = self.msg_id + struct.pack('<H', len(self.payload)) + self.payload
        checksum = ubx_checksum(msg_body)
        return b'\xB5\x62' + msg_body + checksum + b'\x10\x13'


def ubx_checksum(msg):
    a = b = 0
    for c in iter_ints(msg):
        a = (a + c) & 0xff
        b = (b + a) & 0xff
    return struct.pack('BB', a, b)

def get_port():
    """The serial port for the GPS has different names on raspi 2 and 3.
    """
    if os.path.exists('/its_raspi3'):
        return "/dev/serial0"  # Raspi 3
    return "/dev/ttyAMA0"  # Raspi 2

class UbxNmeaParser(object):
    def __init__(self):
        self.buf = b''

    def feed(self, data):
        self.buf += data

    def _take_chunk(self, n):
        c, self.buf = self.buf[:n], self.buf[n:]
        return c

    def _take_nmea(self):
        crlf_ix = self.buf.find(b'\r\n')
        if crlf_ix == -1:
            return None   # Don't have a complete message yet
        data = self._take_chunk(crlf_ix + 2)
        return NMEASentence.parse(data)

    def _take_ubx(self):
        if len(self.buf) < 6:
            return None    # Don't have the length yet
        payload_length = struct.unpack('<H', self.buf[4:6])[0]
        msg_length = payload_length + 8
        if len(self.buf) >= msg_length:
            return self._take_chunk(msg_length)

    def _next_msg(self):
        nmea_start = self.buf.find(b'$')
        ubx_start = self.buf.find(b'\xb5b')
        if nmea_start == 0:
            return self._take_nmea()
        elif ubx_start == 0:
            return self._take_ubx()
        elif (nmea_start > 0) and (ubx_start > 0):
            return self._take_chunk(min(nmea_start, ubx_start))
        elif nmea_start > 0:
            return self._take_chunk(nmea_start)
        elif ubx_start > 0:
            return self._take_chunk(ubx_start)

    def get_msgs(self):
        return iter(self._next_msg, None)

def test_stream_parser(filename):
    import random
    parser = UbxNmeaParser()
    with open(filename, 'rb') as f:
        while True:
            b = f.read(random.randint(1, 100))
            if b == b'':
                return
            parser.feed(b)
            for msg in parser.get_msgs():
                print(repr(msg))

if __name__ == '__main__':
    test_stream_parser(sys.argv[1])