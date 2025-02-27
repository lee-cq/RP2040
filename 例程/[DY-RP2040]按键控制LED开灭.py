import machine
import utime

key = machine.Pin(24, machine.Pin.IN, machine.Pin.PULL_UP)
led = machine.Pin(25, machine.Pin.OUT)

print('gpio input demo...')
while True:
    if key.value() == 1:
        led.value(1)
    else:
        led.value(0)
    utime.sleep_ms(100)
        
