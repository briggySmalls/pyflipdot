"""Test data packet logic"""

import numpy as np

from pyflipdot.data import ImagePacket, Packet


class TestPackets(object):
    def test_no_payload(self):
        packet = Packet(1, 2)
        packet_data = packet.get_bytes()

        assert packet_data == b'\x0212\x039A'

    def test_with_payload(self):
        payload = b'345'
        packet = Packet(1, 2, payload)
        packet_data = packet.get_bytes()

        assert packet_data == b'\x0212345\x03FE'

    def test_image(self):
        # Create an image as below ('p' indicates byte alignment padding)
        # | p, p | (0)
        # | p, p | (1)
        # | p, p | (2)
        # | p, p | (3)
        # | p, p | (4)
        # | 1, 0 | (5)
        # | 0, 0 | (6)
        # | 0, 0 | (7)
        image = np.full((3, 2), False)
        image[0, 0] = True

        packet = ImagePacket(1, image)
        packet_data = packet.get_bytes()
        assert packet_data == b'\x0211020400\x0375'

    def test_tall_image(self):
        # Create an image as below ('p' indicates byte alignment padding)
        # | p, p | (0)
        # | 1, 0 | (1)
        # | 0, 0 | (2)
        # | 0, 0 | (3)
        # | 0, 0 | (4)
        # | 0, 0 | (5)
        # | 0, 0 | (6)
        # | 0, 0 | (7)
        # | 0, 0 | (8)
        # | 0, 0 | (9)
        # | 1, 0 | (10)
        # | 0, 0 | (11)
        # | 0, 0 | (12)
        # | 0, 0 | (13)
        # | 0, 0 | (14)
        # | 0, 0 | (15)
        image = np.full((15, 2), False)
        image[0, 0] = True  # MSbit of MSbyte
        image[9, 0] = True  # MSbit for LSbyte

        packet = ImagePacket(1, image)
        packet_data = packet.get_bytes()
        assert packet_data == b'\x02110440200000\x03B1'
