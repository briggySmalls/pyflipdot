"""Controller for interfacing with one or more Hanover flipdot signs"""
from typing import Dict

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

    @property
    def signs(self) -> Dict[str, HanoverSign]:
        """Get the connected signs

        Returns:
            Dict[str, HanoverSign]: Signs, indexed by name
        """
        return self._signs

    def add_sign(self, name: str, sign: HanoverSign):
        """Adds a sign for the controller to communicate with

        Args:
            sign (HanoverSign): Sign to add

        Raises:
            ValueError: Sign with same name already added
        """
        if name in self.signs.keys():
            raise ValueError("Display '{}' already exists".format(sign.name))

        # Add the new sign
        self._signs[name] = sign

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
        if sign_name is None:
            if len(self.signs) == 1:
                # Get the only sign
                sign = next(iter(self.signs.values()))
            else:
                raise ValueError(
                    "Cannot determine which sign image data is for")
        else:
            # Get the specified sign
            sign = self.signs[sign_name]

        # Construct and send image message
        command = sign.to_image_packet(image_data)
        self._write(command)

    def _write(self, packet: Packet):
        self._port.write(packet.get_bytes())
