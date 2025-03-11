   

def strftime():
    import time
    d = time.localtime(time.time() + 8*3600)
    return f"{d[0]}-{d[1]:02d}-{d[2]:02d}", f"{d[3]:02d}:{d[4]:02d}:{d[5]:02d}"


def dprint(*args, **kwargs):
    d,t =strftime()
    print(f"[{d} {t}]", *args, **kwargs)
    with open(f"{d}-{t[:2]}.log", "a") as f:
        print(f"[{d} {t}]", *args, file=f, **kwargs)


def is_night():
    from time import localtime, time
    hour = localtime(time() + 8*3600)[3]
    return 0 <= hour < 7 # or hour >= 23


def get_time():
    import time
    # 2000-01-01 00:00:00 -- 946656000
    return time.time() + 946656000 + 8*3600


def update_time(oled=None ):
    import ntptime
    ntptime.host = "ntp.aliyun.com"
    ntptime.settime()
    try:
        d, t = strftime()
        oled.text(f"Date: {d}", 2, 46)
        oled.text(f"Time: {t}", 2, 56)
        oled.show()
        time.sleep(2)
    except Exception:
        pass


def connect_wifi(oled, ssid, password):
    dprint("Start Connect Wifi")
    import network, time
    wlan = network.WLAN(network.STA_IF)
    
    if wlan.isconnected():
        dprint(f"Connecnted. -> {wlan.ipconfig('addr4')[0]}")
        return
    
    oled.fill(0)
    oled.text(f'-> {ssid}', 0, 0)
    dprint(f"Will Connect to {ssid} : {password}")
    oled.show()
    
    wlan.active(True)
    wlan.connect(ssid, password)
    st_time = time.time()
    while time.time() - st_time <= 5:
        time.sleep(1)
        if wlan.isconnected():
            break

    if not wlan.isconnected():
        oled.text('Connect Error.', 0,9)
        oled.text('Reset After 5s.', 0,18)
        dprint("Connect Error. Reset After 5s...")
        oled.show()
        time.sleep(5)
        import machine
        machine.reset()

    dprint('Network config:', wlan.ifconfig())
    oled.text('Connect Success.', 0, 9)
    oled.text(f'ip: ', 0, 18)
    oled.text(wlan.ifconfig()[0], 0, 27)
    oled.show()
    
    time.sleep(1)
    update_time(oled)