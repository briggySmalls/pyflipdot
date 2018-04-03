# -*- coding: utf-8 -*-

"""Main module."""
import math
import time

import numpy as np
from serial import Serial

BAUD_RATE = 4800  # Baud rate of serial connection
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


class Packet(object):
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


class ImagePacket(Packet):
    """Packet that encodes an image to display
    """
    def __init__(self, address: int, image: np.array):
        """Contructor for an ImagePacket

        Args:
            address (int): Address of sign packet is intended for
            image (np.array): Image data
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
    def image_to_bytes(image: np.array) -> bytes:
        """Converts an image into an array of bytes

        Args:
            image (np.array): Image data

        Returns:
            bytes: Array of bytes to add a packet payload
        """
        data_mat = ImagePacket.pad_image(image)

        # Flatten 'column major', so a whole column of pixels are sent together
        return bytes(np.packbits(data_mat.flatten('F')))

    @staticmethod
    def pad_image(image: np.array) -> np.array:
        """Pads an image to ensure column data is byte aligned

        Args:
            image (np.array): Image data

        Returns:
            np.array: Padded image data
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


class HanoverSign(object):
    """A Hanover sign

    Attributes:
        address (int): Address of the sign
        flip (bool): True if the sign is upside-down
        height (int): Pixel height of the sidn
        name (str): Friendly name for the sign
        width (int): Pixel width of the sidn
    """

    def __init__(
            self,
            name: str,
            address: int,
            width: int,
            height: int,
            flip: bool = False):
        """Constructor for a hanover sign

        Args:
            name (str): Friendly name for the sign
            address (int): Address of the sign
            width (int): Pixel width of the sidn
            height (int): Pixel height of the sign
            flip (bool, optional): True if the sign is upside-down
        """
        self.name = name
        self.address = address
        self.width = width
        self.height = height
        self.flip = flip

    def to_image_packet(self, image_data: np.array):
        """Produces a serial packet from an image

        Args:
            image_data (np.array): Image data

        Returns:
            ImagePacket: packet

        Raises:
            ValueError: Image incompatible with the sign
        """
        # Check image is correct format for sign
        (rows, columns) = image_data.shape
        if (self.height != rows) or (self.width != columns):
            raise ValueError(
                "{}x{} image incompatible with sign '{}' ({}x{})".format(
                    columns, rows,
                    self.name, self.width, self.height))

        # Flip image upside-down, if necessary
        if self.flip:
            image_data = np.flipud(image_data)

        return ImagePacket(self.address, image_data)

    def create_image(self):
        """Creates a blank image

        Returns:
            np.array: The blank image
        """
        return np.full((self.height, self.width), False)


class HanoverController(object):
    """A controller for addressing Hanover signs
    """

    def __init__(self, port: Serial):
        """Constructor for HanoverController

        Args:
            port (Serial): Serial port used to communicate with signs
        """
        self._port = port
        self._port.baudrate = BAUD_RATE
        self._signs = {}

    def add_sign(self, sign: HanoverSign):
        """Adds a sign for the controller to communicate with

        Args:
            sign (HanoverSign): Sign to add

        Raises:
            ValueError: Sign with same name already added
        """
        if sign.name in self._signs:
            raise ValueError("Display '{}' already exists".format(sign.name))

        # Add the new sign
        self._signs.update({sign.name: sign})

    def get_sign(self, sign_name: str = None):
        if (sign_name is None) and (len(self._signs) != 1):
            raise ValueError("Cannot determine which sign image data is for")

        # Determine sign name
        sign_name = (
            sign_name if
            (sign_name is not None) else
            list(self._signs.keys())[0])

        # Return the sign
        return self._signs[sign_name]

    def start_test_signs(self):
        """Broadcasts the test signs start command
        All signs connected to the serial port will loop the test sequence.
        Note: The sign need not be added to the controller for this sequence to
        take effect.
        """
        command = Packet(_COMMAND_CODES['start_test_signs'], 0)
        self._write(command)

    def stop_test_signs(self):
        """Broadcasts the test signs stop command
        All signs connected to the serial port will stop the test sequence.
        Note: The sign need not be added to the controller for this sequence to
        take effect.
        """
        command = Packet(_COMMAND_CODES['stop_test_signs'], 0)
        self._write(command)

    def draw_image(self, image_data: np.array, sign_name: str = None):
        """Sends an image to a sign to be displayed

        Args:
            image_data (np.array): Image to display
            sign_name (str, optional): Sign to address

        Raises:
            ValueError: Ambiguity which sign is to be addressed
        """
        sign = self.get_sign(sign_name)

        # Construct and send image message
        command = sign.to_image_packet(image_data)
        self._write(command)

    def _write(self, packet: Packet):
        self._port.write(packet.get_bytes())
