from machine import Pin
import rp2
import array


@rp2.asm_pio(
    sideset_init=rp2.PIO.OUT_LOW,
    out_shiftdir=rp2.PIO.SHIFT_LEFT,
    autopull=True,
    pull_thresh=24,
)
def _ws2812():
    T1 = 2
    T2 = 5
    T3 = 3
    wrap_target()
    label("bitloop")
    out(x, 1)               .side(0)    [T3 - 1]
    jmp(not_x, "do_zero")   .side(1)    [T1 - 1]
    jmp("bitloop")          .side(1)    [T2 - 1]
    label("do_zero")
    nop()                   .side(0)    [T2 - 1]
    wrap()

sm = rp2.StateMachine(0, _ws2812, freq=8_000_000, sideset_base=Pin(16))
sm.active(1)

NUM_LEDS = 1
ar = array.array("I", [0 for _ in range(NUM_LEDS)])


def set_rgb(r,g,b):
    ar[0] = g << 16 | r<<8| b
    sm.put(ar, 8)

def red():
    set_rgb(100, 0, 0)

def green():
    set_rgb(0,100,0)

def blue():
    set_rgb(0,0,100)

def close():
    set_rgb(0,0,0)