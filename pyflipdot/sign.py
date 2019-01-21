"""Communication logic for controlling a Hanover sign"""

import numpy as np

from pyflipdot.data import ImagePacket


class HanoverSign(object):
    """A Hanover sign

    Attributes:
        address (int): Address of the sign
        flip (bool): True if the sign is upside-down
        height (int): Pixel height of the sidn
        name (str): Friendly name for the sign
        width (int): Pixel width of the sidn
    """

    def __init__(self,
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
                    columns, rows, self.name, self.width, self.height))

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
