=====
Usage
=====

You can quickly test your Hanover flipdot signs by broadcasting a command to start a test pattern::

    from pyflipdot.pyflipdot import HanoverController
    from serial import Serial

    # Create a serial port (update with port name on your system)
    ser = Serial('/dev/ttyUSB0')

    # Create a controller
    controller = HanoverController.from_serial(ser)

    # Start the test sequence on any connected signs
    controller.start_test_signs()

Once you've confirmed this is working, you'll want to send specific images to a specific sign::

    import numpy as np
    from pyflipdot.sign import HanoverSign

    # Add a sign
    # Note: The sign's address is set via it's potentiometer
    sign = HanoverSign(address=1, width=86, height=7)
    controller.add_sign('dev', sign)

    # Create a 'checkerboard' image
    image = sign.create_image()
    image[::2, ::2] = True
    image[1::2, 1::2] = True

    # Write the image
    controller.draw_image(image)

If you are connecting to your Hanover signs using some other communications interface,
you can supply a custom function to write the bytes out.
The following is a simple example of how using a TCP to RS485 bridge might look::

    from pyflipdot.pyflipdot import HanoverController
    import socket

    # Create a socket
    SERVER_ADDRESS = ("80.243.211.69", 8080)
    socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    socket.connect(SERVER_ADDRESS)

    # Create a custom writer function
    def write(payload: bytes) -> None:
        # Write the bytes to the socket
        socket.sendall(payload)

    # Create a controller - pass in custom writer function
    controller = HanoverController(write)

Refer to the :ref:`api` for full documentation.
