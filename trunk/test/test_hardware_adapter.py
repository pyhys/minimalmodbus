import time
import serial
import minimalmodbus


## Define callbacks for transmitter ##
def on_transmitter_enable(instr, userdata):
    instr.serial.setRTS(level=False) # Output voltage 5 V or 3.3 V
    
def on_transmitter_disable(instr, userdata):
    instr.serial.setRTS(level=True) # Output voltage 0 V 


## Set up instrument ##
instrument = minimalmodbus.Instrument('/dev/ttyUSB0', 1) # port name, slave address (in decimal)
instrument.serial.baudrate = 9600
instrument.handle_local_echo = True
instrument.debug = True



## Set up callbacks for transmitter ##
instrument.on_transmitter_enable = on_transmitter_enable
instrument.on_transmitter_disable = on_transmitter_disable
instrument.userdata = 'ABC'

# Initial value
instrument.serial.setRTS(level=True) 




while True:
    print instrument.read_register(0x102F)
    time.sleep(1)


    
