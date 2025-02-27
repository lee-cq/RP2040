"""适用于RP Pico Mini"""
import machine


def get_temperature() -> float:
    """RP Pico Mini Temperature - 返回树莓派温度传感器的摄氏度温度"""
    sensor_temp = machine.ADC(4)
    conversion_factor = 3.3/65535
    reading = sensor_temp.read_u16() * conversion_factor
    return 27-(reading-0.706)/0.001721

if __name__ == "__main__":
    print(get_temperature())