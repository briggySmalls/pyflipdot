"""Controller for interfacing with one or more Hanover flipdot signs"""
from typing import Callable, Dict

import numpy as np
from serial import Serial

from pyflipdot.data import Packet, TestSignsStartPacket, TestSignsStopPacket
from pyflipdot.sign import HanoverSign


class HanoverController:
    """A controller for addressing Hanover signs
    """

    def __init__(self, writer: Callable[[bytes],None]):
        """Constructor for HanoverController

        Args:
            writer (Callable[[bytes], None]): Callable for communicating
                with the sign
        """
        self._writer = writer
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
        self._writer(packet.get_bytes())

    @staticmethod
    def with_serial(port: Serial) -> 'HanoverController':
        # Set the typical baudrate
        port.baudrate = 4800
        # Instantiate with the port's write method
        return HanoverController(lambda x: port.write(x))
