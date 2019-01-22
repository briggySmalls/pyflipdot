=====
Usage
=====

You can quickly test your Hanover flipdot signs by broadcasting a command to start a test pattern::

    from pyflipdot.pyflipdot import HanoverController
    from serial import Serial

    # Create a serial port (update with port name on your system)
    ser = Serial('/dev/ttyUSB0')

    # Create a controller
    controller = HanoverController(ser)

    # Start the test sequence on any connected signs
    controller.start_test_signs()

Once you've confirmed this is working, you'll want to send specific images to a specific sign::

    import numpy as np
    from pyflipdot.sign import HanoverSign

    # Add a sign
    # Note: The sign's address is set via it's potentiometer
    sign = HanoverSign(name='dev', address=1, width=86, height=7)
    controller.add_sign(sign)

    # Create a 'checkerboard' image
    image = sign.create_image()
    image[::2, ::2] = True
    image[1::2, 1::2] = True

    # Write the image
    controller.write(image)

Refer to the :ref:`api` for full documentation.
