Internal documentation for Minimalmodbus
========================================

.. autoclass:: minimalmodbus.Instrument
   :noindex:
   :members: read_register, write_register, _performCommand, _communicate




Helper functions
----------------
.. automodule:: minimalmodbus
   :noindex:
   :members: _embedPayload, _extractPayload, _twoByteStringToNum, _numToOneByteString, _numToTwoByteString, _calculateCrcString, _XOR, _setBitOn, _rightshift, _toPrintableString
