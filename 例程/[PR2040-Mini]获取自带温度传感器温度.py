"""
RP2040 Mini 自带的温度传感器
"""

import machine
import utime

sensor_temp = machine.ADC(4)
#sensor_temp = machine.ADC(machine.ADC.CORE_TEMP)
conversion_factor = 3.3/(65535)
while True:
    reading = sensor_temp.read_u16()*conversion_factor
    temperature = 27 - (reading - 0.706)/0.001721
    print(temperature,"C")
    utime.sleep(1)
