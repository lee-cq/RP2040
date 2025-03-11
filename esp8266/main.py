from machine import Pin,I2C,Timer, soft_reset
from micropython import alloc_emergency_exception_buf
from time import sleep

from send_http import post_temp
from aht10 import AHT10
from ssd1306 import SSD1306_I2C
from func import strftime, dprint, connect_wifi, update_time, is_night


def oled_init():
    import framebuf
    # Raspberry Pi logo as 32x32 bytearray
    buffer = bytearray(b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00|?\x00\x01\x86@\x80\x01\x01\x80\x80\x01\x11\x88\x80\x01\x05\xa0\x80\x00\x83\xc1\x00\x00C\xe3\x00\x00~\xfc\x00\x00L'\x00\x00\x9c\x11\x00\x00\xbf\xfd\x00\x00\xe1\x87\x00\x01\xc1\x83\x80\x02A\x82@\x02A\x82@\x02\xc1\xc2@\x02\xf6>\xc0\x01\xfc=\x80\x01\x18\x18\x80\x01\x88\x10\x80\x00\x8c!\x00\x00\x87\xf1\x00\x00\x7f\xf6\x00\x008\x1c\x00\x00\x0c \x00\x00\x03\xc0\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00")
    # Load the raspberry pi logo into the framebuffer (the image is 32x32)
    fb = framebuf.FrameBuffer(buffer, 32, 32, framebuf.MONO_HLSB)
    oled.fill(0)
    oled.blit(fb, (128-32)//2, (64-32)//2)
    oled.text('Esp8266 Temp', 0, 0)
    oled.hline(0,12, 128, 1)
    oled.blit(fb, (128-32), 15)
    oled.show()


def to_ssd1306(t=None ):
    humi = aht10.humidity()
    temp = aht10.temperature()
    dewp = aht10.dew_point()
    
    global temp_s, humi_s, dewp_s, add_times, times
    temp_s += temp
    humi_s += humi
    dewp_s += dewp
    add_times += 1
    
    d, t = strftime()
    #oled.fill(0)
    oled.rect(0,16,128-32,46, 0, True)
    oled.text("Temp: {:.2f}C".format(temp), 2, 16)
    oled.text("Humi: {:.2f}%".format(humi), 2, 26)
    oled.text("Dewp: {:.2f}C".format(dewp), 2, 36)
    oled.rect(0,45,128,64, 0, True)
    d, t = strftime()
    oled.text(f"Date: {d}", 1, 46)
    oled.text(f"Time: {t}", 1, 56)
    oled.show()


def to_feishu(t=None):
    global temp_s, humi_s, dewp_s, add_times, times
        
    oled.rect(0,0,128,11, 0, True)
    if post_temp(temp_s/add_times, humi_s/add_times, dewp_s / add_times) == 200:
        times += 1
        dprint(f"post to feishu [{times}] ok ")
        oled.text(f'Feishu {times: 6d} ' + "ok", 0, 0)
        oled.show()
        temp_s, humi_s, dewp_s, add_times = 0,0,0,0
    else:
        oled.text(f'Feishu {times: 6d} ' + "er", 0, 0)
        dprint(f"post to feishu [{times + 1}] err ")
        oled.show()


def upload_error():
    from  send_http import post_error
    try:
        post_error(open("last_error.log").read())
        os.unlink("last_error.log")
        dprint("Upload Error File.")
    except OSError:
        dprint("Not Find Error File.")



def main():
    Timer(-1).init(mode=Timer.ONE_SHOT, period=3600_000, callback=soft_reset)
    while True:
        to_ssd1306()
        if add_times >= 39 or times == 0:
            update_time()
            to_feishu()
            oled.poweroff() if is_night() else oled.poweron()
        else:
            sleep(1)

def init():
    dprint("Init Time.")
    import os
    connect_wifi(oled, "Ziroom302_1", "4001001111")
    oled.poweroff() if is_night() else oled.poweron()
    
    oled_init()
    upload_error()
    dprint("Clear logs ...")
    logs = sorted([i for i in os.listdir("/") if i.endswith(".log")])
    [os.unlink(i) for i in logs[:-3]]
    dprint("Init Success.")


alloc_emergency_exception_buf(100)
i2c = I2C(scl=Pin(5), sda=Pin(4))
dprint("Address List:",i2c.scan())

aht10 = AHT10(i2c, mode=0, address=56)
oled = SSD1306_I2C(128,64,i2c, addr=60 if 60 in i2c.scan() else 61)
temp_s, humi_s, dewp_s, add_times, times  = 0,0,0,0, 0

try:
    init()
    dprint("main start.")
    main()
    
except Exception as e:
    from sys  import print_exception
    
    print_exception(e, open("/last_error.log", 'w'))
    dprint(open("/last_error.log").read())
    dprint("Reset After 5s. If need REPL, Place Ctrl+C.")
    oled.rect(0,16,128,64, 0, True)
    oled.text("Error", 0,16)
    oled.text("Reset After 5s", 0,25)
    oled.text("Ctrl+C to REPL", 0,34)
    oled.show()
    
    sleep(5)
    soft_reset()

