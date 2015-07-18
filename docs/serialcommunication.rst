====================
Serial communication
====================


Timing of the serial communications
-----------------------------------
The Modbus RTU standard prescribes a silent period corresponding to 3.5 characters 
between each message, to be able fo figure out where one message ends and the 
next one starts.

The silent period after the message to the slave is the responsibility of the slave.

The silent period after the message from the slave has previously been 
implemented in MinimalModbus by setting a generous timeout value, and let the 
serial ``read()`` function wait for timeout.

The character time corresponds to 11 bit times, according to http://www.automation.com/library/articles-white-papers/fieldbus-serial-bus-io-networks/introduction-to-modbus.

========== ============== ========== =============== ======================
Baud rate  Bit rate       Bit time   Character time  3.5 character times
========== ============== ========== =============== ======================
2400       2400 bits/s    417 us     4.6 ms          16 ms
4800       4800 bits/s    208 us     2.3 ms          8.0 ms
9600       9600 bits/s    104 us     1.2 ms          4.0 ms
19200      19200 bits/s   52 us      573 us          2.0 ms
38400      38400 bits/s   26 us      286 us          1.0 ms
115200     115200 bit/s   8.7 us     95 us           0.33 ms
========== ============== ========== =============== ======================


RS-485 introduction
-------------------
Several nodes (instruments) can be connected to one RS485 bus. The bus consists of two lines, 
A and B, carrying differential voltages. In both ends of the bus, 
a 120 Ohm termination resistor is connected between line A and B. 
Most often a common ground line is connected between the nodes as well.

At idle, both line A and B rest at the same voltage (or almost the same voltage). 
When a logic 1 is transmitted, line A is pulled towards lower voltage and 
line B is pulled towards higher voltage. 
Note that the A/B naming is sometimes mixed up by some manufacturers.

Each node uses a transceiver chip, containing a transmitter (sender) and a receiver. 
Only one transmitter can be active on the bus simultaneously. 

Pins on the RS485 bus side of the transceiver chip:

* A: inverting line
* B: non-inverting line
* GND

Pins on the microcontroller side of the transceiver chip:

* TX: Data to be transmitted
* TXENABLE: For enabling/disabling the transmitter
* RX: Received data
* RXENABLE: For enabling/disabling the receiver

If the receiver is enabled simultaneusly with the transmitter, the sent data 
is echoed back to the microcontroller. This echo functionality is sometimes useful, 
but most often the TXENABLE and RXENABLE pins are connected in such a way 
that the receiver is disabled when the transmitter is active.

For detailed information, see https://en.wikipedia.org/wiki/RS-485.


Controlling the RS485 transmitter
---------------------------------
Controlling the TXENABLE pin on the transceiver chip is the tricky part 
when it comes to RS485 communication. There are some options:

**Using a USB-to-serial conversion chip that is capable of setting the TXENABLE pin properly**
    See for example the FTDI chip 
    `FT232RL <http://www.ftdichip.com/Products/ICs/FT232R.htm>`_, which has a separate 
    output for this purpose (TXDEN in their terminology). The Sparkfun 
    breakout board `BOB-09822 <https://www.sparkfun.com/products/9822>`_ 
    combines this FTDI chip with a RS485 transceiver chip. The TXDEN output 
    from the FTDI chip is high (+5 V) when the transmitter is to be activated. 
    The FTDI chip calculates when the transmitter should be activated, so you 
    do not have to do anything in your application software.

**Using a RS232-to-RS485 converter capable of figuring out this by it self**
    This typically requires a microcontroller in the converter, and that you 
    configure the baud rate, stop bits etc. This is a straight-forward and 
    easy-to-use alternative, as you can use it together with a standard 
    USB-to-RS232 cable and nothing needs to be done in your application software. 
    One example of this type of converter is `Westermo MDW-45 <http://www.westermo.com>`_, 
    which I have been using with great success.

**Using a converter where the TXENABLE pin is controlled by the TX pin, sometimes via some timer circuit**
    I am not conviced that it is a good idea to control the TXENABLE pin by the TX pin, 
    as only one of the logic levels are actively driving the bus voltage. 
    If using a timer circuit, the hardware needs to be adjusted to the baudrate.
    
**Have the transmitter constantly enabled**
    Some users have been reporting on success for this strategy. The problem is that the master and
    slaves have their transmitters enabled simultaneously. I guess for certain situations (and
    being lucky with the transceiver chip) it might work. Note that you will receive your own transmitted 
    message (local echo). See :ref:`handlelocalecho`.

**Controlling a separate GPIO pin from kernelspace software on embedded Linux machines** 
    See for example http://blog.savoirfairelinux.com/en/2013/rs-485-for-beaglebone-a-quick-peek-at-the-omap-uart/ 
    This is a very elegant solution, as the TXENABLE pin is controlled by the 
    kernel driver and you don't have to worry about it in your application program. 
    Unfortunately this is not available for all boards, for example the standard distribution for 
    Beaglebone (September 2014).

**Controlling a separate GPIO pin from userspace software on embedded Linux machines**
    This will give large time delays, but might be acceptable for low speeds. 

**Controlling the RTS pin in the RS232 interface (from userspace), and connecting it to the TXENABLE pin of the transceiver**
    This will give large time delays, but might be acceptable for low speeds. 
       

Controlling the RS-485 transceiver from userspace
----------------------------------------------------
As described above, this should be avoided. Nevertheless, for low speeds (maybe up to 9600 bits/s) it might be useful.

This can be done from userspace, but will then lead to large time delays. 
I have tested this with a 3.3V FTDI  USB-to-serial cable using pySerial 
on a Linux laptop. The cable has a RTS output, 
but no TXDEN output. Note that the RTS output is +3.3 V at idle, and 0 V when 
RTS is set to True. The delay time is around 1 ms, as measured with an oscilloscope. 
This corresponds to approx 100 bit times when running at 115200 bps, but this 
value also includes delays caused by the Python intepreter.



