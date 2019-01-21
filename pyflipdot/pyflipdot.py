"""Controller for interfacing with one or more Hanover flipdot signs"""
import numpy as np
from serial import Serial

from pyflipdot.data import Packet, TestSignsStartPacket, TestSignsStopPacket
from pyflipdot.sign import HanoverSign


class HanoverController:
    """A controller for addressing Hanover signs
    """
    _BAUD_RATE = 4800  # Baud rate of serial connection

    def __init__(self, port: Serial):
        """Constructor for HanoverController

        Args:
            port (Serial): Serial port used to communicate with signs
        """
        self._port = port
        self._port.baudrate = self._BAUD_RATE
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

    def get_sign(self, sign_name: str = None) -> HanoverSign:
        """Gets a sign by name, or gets only sign

        Args:
            sign_name (str, optional): The name of the sign to fetch.

        Returns:
            HanoverSign: Sign object

        Raises:
            ValueError: The specified sign was not found
        """
        if (sign_name is None) and (len(self._signs) != 1):
            raise ValueError("Cannot determine which sign image data is for")

        # Determine sign name
        sign_name = (sign_name if
                     (sign_name is not None) else list(self._signs.keys())[0])

        # Return the sign
        return self._signs[sign_name]

    def start_test_signs(self):
        """Broadcasts the test signs start command
        All signs connected to the serial port will loop the test sequence.
        Note: The sign need not be added to the controller for this sequence to
        take effect.
        """
        self._write(TestSignsStartPacket())

    def stop_test_signs(self):
        """Broadcasts the test signs stop command
        All signs connected to the serial port will stop the test sequence.
        Note: The sign need not be added to the controller for this sequence to
        take effect.
        """
        self._write(TestSignsStopPacket())

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
