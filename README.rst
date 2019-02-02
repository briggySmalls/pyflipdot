=========
pyflipdot
=========

.. image:: https://img.shields.io/pypi/v/pyflipdot.svg
        :target: https://pypi.python.org/pypi/pyflipdot

.. image:: https://img.shields.io/travis/briggySmalls/pyflipdot.svg
        :target: https://travis-ci.org/briggySmalls/pyflipdot

.. image:: https://coveralls.io/repos/github/briggySmalls/pyflipdot/badge.svg?branch=master
        :target: https://coveralls.io/github/briggySmalls/pyflipdot?branch=master

.. image:: https://img.shields.io/pypi/pyversions/pyflipdot.svg
        :target: https://pypi.python.org/pypi/pyflipdot

Simple python driver for controlling Hanover flipdot displays.

* Free software: MIT license
* Documentation: https://briggysmalls.github.io/pyflipdot/

Features
--------

* Simple API for writing data in numpy arrays
* Includes broadcast test sequence commands for quick testing
* Control multiple signs using a single serial connection

Credits
-------

This package was built after careful study of John Whittington's `blog post`_ and his node.js driver `node-flipdot`_.

If you like the package structure (tox/pipenv/invoke/yapf etc.) then consider using my `cookiecutter template`_ 😎.

.. _`blog post`: https://engineer.john-whittington.co.uk/2017/11/adventures-flippy-flip-dot-display/
.. _`node-flipdot`: https://github.com/tuna-f1sh/node-flipdot
.. _`cookiecutter template`: https://github.com/briggySmalls/cookiecutter-pypackage
