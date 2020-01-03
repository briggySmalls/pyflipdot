"""Test data packet logic"""

import numpy as np

from pyflipdot.data import ImagePacket, Packet


def test_no_payload():
    packet = Packet(1, 2)
    packet_data = packet.get_bytes()

    assert packet_data == b'\x0212\x039A'


def test_with_payload():
    payload = b'345'
    packet = Packet(1, 2, payload)
    packet_data = packet.get_bytes()

    assert packet_data == b'\x0212345\x03FE'


def test_simple_image():
    # Send an image as below ('p' indicates byte alignment padding)
    # (0) | 1, 0 |
    # (1) | 0, 0 | -> [0x01, 0x00]
    # (2) | 0, 0 |
    # (3) | 0, 0 |
    image = np.full((3, 2), False)
    image[0, 0] = True

    packet = ImagePacket(1, image)
    packet_data = packet.get_bytes()
    assert packet_data == b'\x0211020100\x0378'


def test_tall_image():
    # Send an image as below ('p' indicates byte alignment padding)
    # (0)  | 1, 0 |
    # (1)  | 0, 0 |
    # (2)  | 0, 0 |
    # (3)  | 0, 0 |
    # (4)  | 0, 0 |
    # (5)  | 0, 0 |
    # (6)  | 0, 0 |
    # (7)  | 0, 0 | -> | 0x01, 0x00 | -> [0x01, 0x02, 0x00, 0x00]
    # (8)  | 0, 0 |    | 0x02, 0x00 |
    # (9)  | 1, 0 |
    # (10) | 0, 0 |
    # (11) | 0, 0 |
    # (12) | 0, 0 |
    # (13) | 0, 0 |
    # (14) | 0, 0 |
    image = np.full((15, 2), False)
    image[0, 0] = True
    image[9, 0] = True

    packet = ImagePacket(1, image)
    packet_data = packet.get_bytes()
    assert packet_data == b'\x02110401020000\x03B4'


def test_large_image():
    # Create an image that is 128x32 pixels
    image = np.full((16, 128), True)

    packet = ImagePacket(1, image)
    packet_data = packet.get_bytes()
    assert packet_data[:5] == b'\x021100'
    for val in packet_data[7:-3]:
        assert val.to_bytes(1, byteorder='big') == b'F'
    assert packet_data[-3:] == b'\x033B'
