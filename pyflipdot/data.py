"""Packets sent via Serial to control Hanover signs"""

import math

import numpy as np

_START_BYTE = b'\x02'  # Start byte for every packet
_END_BYTE = b'\x03'  # End byte for every packet (followed by checksum)

# Command code lookup
_COMMAND_CODES = {
    'start_test_signs': 3,
    'stop_test_signs': 12,
    'write_image': 1,
}


def _to_ascii_hex(value: bytes) -> bytes:
    def _bytes_to_ascii_hex(val: bytes) -> bytes:
        return val.hex().upper().encode('ASCII')

    try:
        return _bytes_to_ascii_hex(value)
    except AttributeError:
        return _bytes_to_ascii_hex(bytes([value]))


def _bytes_to_int(data: bytes) -> int:
    return int.from_bytes(data, byteorder='big')


def _closest_larger_multiple(value: int, base: int) -> int:
    return int(base * math.ceil(float(value) / base))


class Packet:
    """Encapsulation of data to be sent over serial

    Attributes:
        address (int): Hanover protocol command
        command (int): Address of sign packet is intended for
        payload (byte | None): Data bytes that may accompany command
    """

    def __init__(self, command: int, address: int, payload: bytes = None):
        """Constructor of Packet

        Args:
            command (int): Hanover protocol command
            address (int): Address of sign packet is intended for
            payload (bytes, optional): Data bytes that may accompany command
        """
        self.command = command
        self.address = address
        self.payload = payload

    def get_bytes(self) -> bytes:
        """Converts the packet data into bytes

        Returns:
            bytes: Bytes ready to be sent over serial
        """

        # Start the packet with the start byte
        data = _START_BYTE
        # Command/address take one hex byte each
        data += "{:1X}{:1X}".format(self.command, self.address).encode('ASCII')

        # Add the payload (if present)
        if self.payload:
            data += self.payload

        # Add the footer (end byte and checksum)
        data += _END_BYTE
        data += _to_ascii_hex(self.calculate_checksum(data))

        return data

    @staticmethod
    def calculate_checksum(data: bytes) -> bytes:
        """Helper function for calculating a packet's modular checksum

        Args:
            data (bytes): Data to calculate checksum for

        Returns:
            bytes: Checksum bytes
        """
        total = sum(bytearray(data)) - _bytes_to_int(_START_BYTE)
        total_clipped = total & 0xFF
        checksum = ((total_clipped ^ 0xFF) + 1) & 0xFF
        return bytes([checksum])


class TestSignsStartPacket(Packet):
    """Command for all signs to cycle through a test mode sequence
    """

    def __init__(self):
        super().__init__(_COMMAND_CODES['start_test_signs'], 0)


class TestSignsStopPacket(Packet):
    """Command for all signs to stop test mode sequence
    """

    def __init__(self):
        super().__init__(_COMMAND_CODES['stop_test_signs'], 0)


class ImagePacket(Packet):
    """Packet that encodes an image to display
    """

    def __init__(self, address: int, image: np.ndarray):
        """Contructor for an ImagePacket

        Args:
            address (int): Address of sign packet is intended for
            image (np.ndarray): Image data
        """
        assert len(image.shape) == 2

        # Convert the image to an array of bytes
        image_bytes = self.image_to_bytes(image)

        # Start with the resolution (image byte count)
        payload = _to_ascii_hex(len(image_bytes))
        # Add the image bytes
        payload += _to_ascii_hex(image_bytes)

        # Create the packet as normal
        super().__init__(_COMMAND_CODES['write_image'], address, payload)

    @staticmethod
    def image_to_bytes(image: np.ndarray) -> bytes:
        """Converts an image into an array of bytes

        Args:
            image (np.ndarray): Image data

        Returns:
            bytes: Array of bytes to add a packet payload
        """
        data_mat = ImagePacket.pad_image(image)

        # Flatten 'column major', so a whole column of pixels are sent together
        return bytes(np.packbits(data_mat.flatten('F')))

    @staticmethod
    def pad_image(image: np.ndarray) -> np.ndarray:
        """Pads an image to ensure column data is byte aligned

        Args:
            image (np.ndarray): Image data

        Returns:
            np.ndarray: Padded image data
        """
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
