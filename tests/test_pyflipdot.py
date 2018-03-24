#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for `pyflipdot` module."""

import pytest

from pyflipdot.pyflipdot import (
    Packet, ImagePacket, HanoverController, HanoverSign)
import numpy as np
from unittest.mock import MagicMock

# Disable errors for pytest fixtures/classes
# pylint: disable=no-self-use,redefined-outer-name


@pytest.fixture
def serial_port():
    return MagicMock()


@pytest.fixture
def controller(serial_port):
    return HanoverController(serial_port)


class TestPackets(object):

    def test_no_payload(self):
        packet = Packet(1, 2)
        packet_data = packet.get_bytes()

        assert packet_data == b'\x0212\x039A'

    def test_with_payload(self):
        payload = b'345'
        packet = Packet(1, 2, payload)
        packet_data = packet.get_bytes()

        assert packet_data == b'\x0212345\x03FE'

    def test_image(self):
        # Create an image as below ('p' indicates byte alignment padding)
        # | p, p | (0)
        # | p, p | (1)
        # | p, p | (2)
        # | p, p | (3)
        # | p, p | (4)
        # | 1, 0 | (5)
        # | 0, 0 | (6)
        # | 0, 0 | (7)
        image = np.full((3, 2), False)
        image[0, 0] = True

        packet = ImagePacket(1, image)
        packet_data = packet.get_bytes()
        assert packet_data == b'\x0211020400\x0375'

    def test_tall_image(self):
        # Create an image as below ('p' indicates byte alignment padding)
        # | p, p | (0)
        # | 1, 0 | (1)
        # | 0, 0 | (2)
        # | 0, 0 | (3)
        # | 0, 0 | (4)
        # | 0, 0 | (5)
        # | 0, 0 | (6)
        # | 0, 0 | (7)
        # | 0, 0 | (8)
        # | 0, 0 | (9)
        # | 1, 0 | (10)
        # | 0, 0 | (11)
        # | 0, 0 | (12)
        # | 0, 0 | (13)
        # | 0, 0 | (14)
        # | 0, 0 | (15)
        image = np.full((15, 2), False)
        image[0, 0] = True  # MSbit of MSbyte
        image[9, 0] = True  # MSbit for LSbyte

        packet = ImagePacket(1, image)
        packet_data = packet.get_bytes()
        assert packet_data == b'\x02110440200000\x03B1'


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
        serial_port.write.assert_called_once_with(b'\x0211020104\x0374')

    def test_draw_bad_image(self, controller):
        sign = HanoverSign('dev', 1, 2, 3)
        controller.add_sign(sign)

        with pytest.raises(ValueError):
            # Construct image with different number of rows/columns
            bad_image = np.full((4, 5), True)
            controller.draw_image(bad_image)
