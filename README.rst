==============
Aqours Wotabag
==============

Idol themed LED controller for Raspberry Pi.

wotabag is a Python based controller for Raspberry Pi intended to drive a series of WS281X (Neopixel) RGB LEDs,
and play a light show in sync with idol music.
The original purpose of this project was to build an Aqours itabag containing three standard Kingblade penlights,
with a strip of 9 LEDs inserted into each penlight tube.
In theory, this package could be modified to drive an arbitrary number of LEDs, and is not limited to LoveLive colors.

The wotabag daemon can be controlled over HTTP via a JSON-RPC API.
`wotabag-remote`_ is also available for controlling the daemon over BLE from an iOS device.

Under the hood, all GPIO handling is done by rpi-ws281x-python_.
wotabag is written with the assumption that a single strip of 27 (9x3) LEDs is being driven by the default PWM GPIO
output pin, but any output pin and method (i.e. SPI) supported by rpi-ws281x_ should work.

Note: Using PWM in rpi-ws281x requires that the wotabag daemon be run as root,
and that using PWM requires disabling the onboard Pi sound device.
So for the default wotabag configuration, a USB audio device must be used.

* Free software: GNU General Public License v3+

.. _rpi-ws281x: https://github.com/jgarff/rpi_ws281x
.. _rpi-ws281x-python: https://github.com/rpi-ws281x/rpi-ws281x-python
.. _`wotabag-remote`: https://github.com/pmrowla/wotabag-remote

Requirements
------------

* Python 3, Python 2 is not supported (tested on Python 3.7)
* mpv/libmpv
* RPC over BLE requires BlueZ (Linux Bluetooth stack) (tested with BlueZ 5.50)
* Raspberry Pi (tested on Raspberry Pi 4 Model B and Raspberry Pi Zero W running Raspbian Buster,
  but in theory any Pi supported by rpi-ws281x should work)
* RPC over BLE requires a Bluetooth enabled Pi (or USB Bluetooth adapter)

Usage
-----

After installing the required system dependencies, clone this repo and install the wotabag package via pip.
This will place the server daemon into pip's default script install path.

.. code-block:: bash

    $ sudo wotabagd your_config_file.yml

See ``examples/`` for an example configuration file and example song files.

Pi Model Caveats
----------------

Raspberry Pi 4
~~~~~~~~~~~~~~

The default BLE MTU used in wotabag is 48 bytes, as this is the largest value that worked in testing with a Pi Zero W.
However, the maximum allowed BLE MTU size by an iOS device is 185 bytes, and in testing a Raspberry Pi Model 4 did support using 185 bytes.
If you are running wotabag on a Pi 4, adjusting the value of ``MTU_SIZE`` in ``wotabag/sdp.py`` (and the corresponding value in ``Constants.swift`` for wotabag-remote) to 185 may give you a slight performance increase.

Raspberry Pi Zero (W)
~~~~~~~~~~~~~~~~~~~~~

Since this is written in Python, it is not particularly efficient, and since Linux is not a real-time operating system, timing sensitive operations are not handled precisely on a Raspberry Pi.
This can lead to choppy LED animations when running wotabag on a Pi Zero.

Using chrt_ to give the process a higher priority seems to give "good enough" real-world results when using a Pi Zero, but your mileage may vary.
The easiest alternative to get smooth playback is to just use a full-featured Pi, but for a portable solution, I would still recommend using a Pi Zero in your actual bag.

.. _chrt: http://man7.org/linux/man-pages/man1/chrt.1.html

License
-------

::

    GNU GENERAL PUBLIC LICENSE
                          Version 3, 29 June 2007

        wotabag
        Copyright (C) 2019, Peter Rowlands

        This program is free software: you can redistribute it and/or modify
        it under the terms of the GNU General Public License as published by
        the Free Software Foundation, either version 3 of the License, or
        (at your option) any later version.

        This program is distributed in the hope that it will be useful,
        but WITHOUT ANY WARRANTY; without even the implied warranty of
        MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
        GNU General Public License for more details.

        You should have received a copy of the GNU General Public License
        along with this program.  If not, see <http://www.gnu.org/licenses/>.

    Also add information on how to contact you by electronic and paper mail.

      You should also get your employer (if you work as a programmer) or school,
    if any, to sign a "copyright disclaimer" for the program, if necessary.
    For more information on this, and how to apply and follow the GNU GPL, see
    <http://www.gnu.org/licenses/>.

      The GNU General Public License does not permit incorporating your program
    into proprietary programs.  If your program is a subroutine library, you
    may consider it more useful to permit linking proprietary applications with
    the library.  If this is what you want to do, use the GNU Lesser General
    Public License instead of this License.  But first, please read
    <http://www.gnu.org/philosophy/why-not-lgpl.html>.

Credits
-------

This package contains code based on `Jumperr-labs/python-gatt-server`_ and the BlueZ_ project.
BlueZ is licensed under GPLv2.0.

This package utilizes libmpv. mpv is licensed under either GPLv2 or LGPLv2 depending on distribution.

This package was created with Cookiecutter_ and the `audreyr/cookiecutter-pypackage`_ project template.

.. _`Jumperr-labs/python-gatt-server`: https://github.com/Jumperr-labs/python-gatt-server
.. _BlueZ: http://www.bluez.org/
.. _Cookiecutter: https://github.com/audreyr/cookiecutter
.. _`audreyr/cookiecutter-pypackage`: https://github.com/audreyr/cookiecutter-pypackage
