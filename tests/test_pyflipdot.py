"""Tests for `pyflipdot` module."""

from unittest.mock import MagicMock

import numpy as np
import pytest

from pyflipdot.pyflipdot import HanoverController
from pyflipdot.sign import HanoverSign

# Disable errors for pytest fixtures/classes
# pylint: disable=no-self-use,redefined-outer-name


@pytest.fixture
def serial_port():
    return MagicMock()


@pytest.fixture
def controller(serial_port):
    return HanoverController(serial_port)


class TestController(object):
    def test_start_test_signs(self, controller, serial_port):
        controller.start_test_signs()
        serial_port.write.assert_called_once_with(b'\x0230\x039A')

    def test_stop_test_signs(self, controller, serial_port):
        controller.stop_test_signs()
        serial_port.write.assert_called_once_with(b'\x02C0\x038A')

    def test_draw_image_no_sign(self, controller):
        # Draw image before adding a sign
        image = np.ones((2, 3))
        with pytest.raises(ValueError):
            controller.draw_image(image)

    def test_draw_good_image(self, controller, serial_port):
        # Add a sign
        sign = HanoverSign('dev', 1, 2, 3)
        controller.add_sign(sign)

        # Construct and draw image as below
        # ('p' indicates byte alignment padding)
        # | p, p |
        # | p, p |
        # | p, p |
        # | p, p |
        # | p, p |
        # | 1, 0 |
        # | 0, 0 |
        # | 0, 1 |
        image = np.full((3, 2), False)
        image[0, 0] = True
        image[2, 1] = True

        controller.draw_image(image)
        serial_port.write.assert_called_once_with(b'\x0211020401\x0374')

    def test_draw_flipped_image(self, controller, serial_port):
        # Add a sign that flips all images vertically
        flipped_sign = HanoverSign('dev', 1, 2, 3, flip=True)
        controller.add_sign(flipped_sign)

        # Construct and draw image as below
        # ('p' indicates byte alignment padding)
        # | p, p |     | p, p |
        # | p, p |     | p, p |
        # | p, p |     | p, p |
        # | p, p |     | p, p |
        # | p, p | --> | p, p |
        # | 0, 1 |     | 1, 0 |
        # | 0, 0 |     | 0, 0 |
        # | 0, 1 |     | 1, 0 |
        image = np.full((3, 2), False)
        image[0, 1] = True
        image[2, 1] = True

        controller.draw_image(image)
        serial_port.write.assert_called_once_with(b'\x0211020500\x0374')

    def test_draw_bad_image(self, controller):
        sign = HanoverSign('dev', 1, 2, 3)
        controller.add_sign(sign)

        with pytest.raises(ValueError):
            # Construct image with different number of rows/columns
            bad_image = np.full((4, 5), True)
            controller.draw_image(bad_image)
