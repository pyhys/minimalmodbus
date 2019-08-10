.. _troubleshooting:

================
Trouble shooting
================


No communication
----------------
If there is no communication, make sure that the settings on your instrument are OK:

* Wiring is correct
* Communication module is set for digital communication
* Correct protocol (Modbus, and the RTU or ASCII version)
* Baud rate
* Parity
* Delay (most often not necessary)
* Address

The corresponding settings should also be used in MinimalModbus. Check also your:

* Port name

For troubleshooting, it is recommended to use interactive mode with debug
enabled. See :ref:`interactiveusage`.

If there is no response from your instrument, you can try using a lower
baud rate, or to adjust the timeout setting.

See also the pySerial pages: https://pyserial.readthedocs.io

To make sure you are sending something valid, start with the examples in
the users manual of your instrument. Use MinimalModbus in debug mode and make sure that each sent byte is correct.

The terminiation resistors of the RS-485 bus must be set correctly. Use a
multimeter to verify that there is termination in the appropriate nodes of
your RS-485 bus.

To troubleshoot the communication in more detail, an oscilloscope can be very
useful to verify transmitted data.


Local echo
----------
Local echo of the USB-to-RS485 adaptor can also be the cause of some problems,
and give rise to strange error messages (like "CRC error" or "wrong number of bytes error" etc).
Switch on the debug mode to see the request and response messages.
If the full request message can be found as the first part of the response,
then local echo is likely the cause.

Make a test to remove the adaptor from the instrument (but still connected
to the computer), and see if you still have a response.

Most adaptors have switches to select echo ON/OFF. Turning off the local
echo can be done in a number of ways:

* A DIP-switch inside the plastic cover.
* A jumper inside the plastic cover.
* Shorting two of the pins in the 9-pole D-SUB connector turns off the echo for some models.
* If based on a FTDI chip, some special program can be used to change a chip setting for disabling echo.

To handle local echo, see :class:`minimalmodbus.Instrument`.


Empty bytes added in the beginning or the end on the received message
---------------------------------------------------------------------
This is due to interference. Use biasing of modbus lines, by connecting resistors
to GND and Vcc from the the two lines. This is sometimes named "failsafe".


Serial adaptors not recognized
------------------------------
There have been reports on problems with serial adaptors on some platforms,
for example Raspberry Pi. It seems to lack kernel drives for some chips, like PL2303.
Serial adaptors based on FTDI FT232RL are known to work.

Make sure to run the ``dmesg`` command before and after plugging in your
serial adaptor, to verify that the proper kernel driver is loaded.


Known issues
--------------

See GitHub page.


Issues when running under Windows
---------------------------------
Since MinimalModbus version 0.5, the handling of several instruments on the same
serial port has been improved for Windows.

.. _support:

Support
-------
Ask a question on https://stackoverflow.com/. Use the tags "modbus", "python" and "minimalmodbus".

Describe the problem in detail, and include any error messsages.

Note that it can be very helpful to switch on the debug mode, where the communication
details are printed. See :ref:`debugmode`.

Please also include the output after running::

  >>> import minimalmodbus
  >>> print(minimalmodbus._get_diagnostic_string())

Describe which instrument model you are using, and possibly a link to online PDF documentation for it.
