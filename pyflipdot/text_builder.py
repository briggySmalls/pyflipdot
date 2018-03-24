from PIL import Image, ImageDraw, ImageFont
import numpy as np


def preview_image(image):

    def bit_to_char(image, col, row):
        if image[row, col]:
            return '#'
        return ' '

    (rows, columns) = image.shape
    print("Printing {}x{} image".format(columns, rows))
    for row in range(rows):
        print("|{}|".format(''.join(
            [bit_to_char(image, col, row) for col in range(columns)])))


class TextBuilder(object):

    def __init__(self, width, height):
        self.width = width
        self.height = height

    def text_image(
        self,
        text: str,
        font: ImageFont,
        alignment='left'
    ):

        # Get some details about the font
        size, (_, offset_y) = font.font.getsize(text)

        # Determine Text starting position
        text_position = self.get_text_position(size, alignment)
        text_position['y'] -= offset_y

        # Create a new image
        image = Image.new(mode='1', size=(self.width, self.height), color=0)
        # Get a drawing context
        draw = ImageDraw.Draw(image)

        # Draw text
        draw.text(
            (text_position['x'], text_position['y']),
            text,
            fill=1,
            font=font)
        return np.array(image)

    def get_text_position(self, size, alignment):
        width, height = size

        if (width > self.width) or (height > self.height):
            print("Warning: {}x{} text will be clipped to fit on {}x{} image".format(
                width, height, self.width, self.height))

        text_position = {
            'y': 0
        }

        # Find x-position based on alignment
        if alignment == 'left':
            text_position['x'] = 0
        elif alignment == 'right':
            text_position['x'] = self.width - width
        elif alignment == 'centre':
            text_position['x'] = int(round((self.width - width) / 2))
        else:
            raise ValueError("Invalid alignment '{}'".format(alignment))

        return text_position
