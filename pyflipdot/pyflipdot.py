# -*- coding: utf-8 -*-

"""Main module."""
import math
import time

import numpy as np
from serial import Serial

_START_BYTE = b'\x02'  # Start byte for every packet
_END_BYTE = b'\x03'  # End byte for every packet (followed by checksum)

# Command code lookup
_COMMAND_CODES = {
    'start_test_signs': 3,
    'stop_test_signs': 12,
    'write_image': 1,
}


def _to_ascii_hex(value: bytes) -> bytes:
    def bytes_to_ascii_hex(val: bytes) -> bytes:
        return val.hex().upper().encode('ASCII')

    try:
        return bytes_to_ascii_hex(value)
    except AttributeError:
        return bytes_to_ascii_hex(bytes([value]))


def _bytes_to_int(data: bytes) -> int:
    return int.from_bytes(data, byteorder='big')


def _closest_larger_multiple(value: int, base: int) -> int:
    return int(base * math.ceil(float(value) / base))


class Packet(object):
    def __init__(self, command: int, address: int, payload: bytes = None):
        self.command = command
        self.address = address
        self.payload = payload

    def get_bytes(self) -> bytes:
        data = b''

        # Construct the header
        data += _START_BYTE
        # Command/address take one hex byte each
        data += "{:1X}{:1X}".format(
            self.command, self.address).encode('ASCII')

        # Add the payload (if present)
        if self.payload:
            data += self.payload

        # Add the footer (end byte and checksum)
        data += _END_BYTE
        data += _to_ascii_hex(self.calculate_checksum(data))

        return data

    @staticmethod
    def calculate_checksum(data: bytes) -> bytes:
        total = sum(bytearray(data)) - _bytes_to_int(_START_BYTE)
        total_clipped = total & 0xFF
        checksum = ((total_clipped ^ 0xFF) + 1) & 0xFF
        return bytes([checksum])


class ImagePacket(Packet):
    def __init__(self, address: int, image: np.array):
        assert len(image.shape) == 2

        image_bytes = self.image_to_bytes(image)

        # Create the payload from the image data
        payload = b''
        # Add the resolution (image byte count)
        payload += _to_ascii_hex(len(image_bytes))
        # Add the image bytes
        payload += _to_ascii_hex(image_bytes)

        # Create the packet as normal
        super().__init__(_COMMAND_CODES['write_image'], address, payload)

    @staticmethod
    def image_to_bytes(image: np.array) -> bytes:
        data_mat = ImagePacket.pad_image(image)

        # Flatten 'column major', so a whole column of pixels are sent together
        return bytes(np.packbits(data_mat.flatten('F')))

    @staticmethod
    def pad_image(image: np.array) -> np.array:
        # Check if row count converts nicely into bytes
        (rows, columns) = image.shape
        data_rows = _closest_larger_multiple(rows, 8)
        data_mat = image

        if data_rows != rows:
            # Pad the top of the image, first 'padding' rows are ignored
            padding = data_rows - rows
            data_mat = np.full((data_rows, columns), False)
            data_mat[padding:, :columns] = image

        return data_mat

    @staticmethod
    def calculate_resolution(rows: int, columns: int) -> int:
        return _closest_larger_multiple(rows, 8) * columns / 8


class HanoverSign(object):
    def __init__(
            self,
            name: str,
            address: int,
            width: int,
            height: int,
            flip: bool = False):
        self.name = name
        self.address = address
        self.width = width
        self.height = height
        self.flip = flip

    def to_image_packet(self, image_data: np.array):
        # Check image is correct format for sign
        (rows, columns) = image_data.shape
        if (self.height != rows) or (self.width != columns):
            raise ValueError(
                "{}x{} image incompatible with sign '{}' ({}x{})".format(
                    columns, rows,
                    self.name, self.width, self.height))

        # Flip if necessary
        if self.flip:
            image_data = np.flipud(image_data)

        return ImagePacket(self.address, image_data)

    def create_image_data(self):
        return np.full((self.height, self.width), False)


class HanoverController(object):
    TEST_SIGNS_SLEEP_TIME_S = 4

    def __init__(self, port: Serial):
        self.port = port
        self.signs = {}

    def add_sign(self, sign: HanoverSign):
        if sign.name in self.signs:
            raise ValueError("Display '{}' already exists".format(sign.name))

        # Add the new sign
        self.signs.update({sign.name: sign})

    def list_signs(self):
        return self.signs

    def test_signs(self, duration_s=10):
        for _ in range(duration_s / self.TEST_SIGNS_SLEEP_TIME_S):
            self.start_test_signs()
            time.sleep(self.TEST_SIGNS_SLEEP_TIME_S)
        self.stop_test_signs()

    def start_test_signs(self):
        command = Packet(_COMMAND_CODES['start_test_signs'], 0)
        self.write(command)

    def stop_test_signs(self):
        command = Packet(_COMMAND_CODES['stop_test_signs'], 0)
        self.write(command)

    def draw_image(self, image_data: np.array, sign_name: str = None):
        # Determine sign name
        if (sign_name is None) and (len(self.signs) != 1):
            raise ValueError("Cannot determine which sign image data is for")
        sign_name = (
            sign_name if
            (sign_name is not None) else
            list(self.signs.keys())[0])
        sign = self.signs[sign_name]

        # Construct and send image message
        command = sign.to_image_packet(image_data)
        self.write(command)

    def write(self, packet: Packet):
        self.port.write(packet.get_bytes())
